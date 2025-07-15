"""
Context Manager - Gestor de contexto para mantenimiento de estado entre pasos
Maneja variables, checkpoints y estado compartido durante la ejecución de tareas
"""

import json
import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from pathlib import Path
import pickle
import os

class ContextScope(Enum):
    TASK = "task"
    STEP = "step"
    GLOBAL = "global"
    TEMPORARY = "temporary"

class VariableType(Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    LIST = "list"
    FILE_PATH = "file_path"
    RESULT = "result"

@dataclass
class ContextVariable:
    key: str
    value: Any
    type: VariableType
    scope: ContextScope
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    source_step: Optional[str] = None

@dataclass
class ContextCheckpoint:
    checkpoint_id: str
    task_id: str
    step_id: str
    timestamp: datetime
    variables: Dict[str, ContextVariable]
    execution_state: Dict[str, Any]
    description: str
    auto_created: bool = False

@dataclass
class ContextSession:
    session_id: str
    task_id: str
    created_at: datetime
    last_accessed: datetime
    variables: Dict[str, ContextVariable]
    checkpoints: List[ContextCheckpoint]
    metadata: Dict[str, Any]
    is_active: bool = True

class ContextManager:
    def __init__(self, storage_path: str = "/tmp/context_manager"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # En memoria para acceso rápido
        self.active_sessions: Dict[str, ContextSession] = {}
        
        # Configuración
        self.config = {
            'max_sessions': 100,
            'session_ttl': timedelta(hours=24),
            'checkpoint_ttl': timedelta(hours=48),
            'auto_checkpoint_interval': 300,  # 5 minutos
            'max_checkpoints_per_session': 50,
            'variable_ttl': timedelta(hours=12),
            'cleanup_interval': timedelta(hours=1)
        }
        
        # Lock para thread safety
        self._lock = threading.RLock()
        
        # Inicializar sistema
        self._load_persistent_sessions()
        self._start_cleanup_thread()
    
    def create_session(self, task_id: str, metadata: Dict[str, Any] = None) -> str:
        """Crear nueva sesión de contexto para una tarea"""
        with self._lock:
            session_id = f"ctx_{task_id}_{uuid.uuid4().hex[:8]}"
            
            session = ContextSession(
                session_id=session_id,
                task_id=task_id,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                variables={},
                checkpoints=[],
                metadata=metadata or {},
                is_active=True
            )
            
            self.active_sessions[session_id] = session
            self._save_session(session)
            
            return session_id
    
    def get_session(self, session_id: str) -> Optional[ContextSession]:
        """Obtener sesión activa"""
        with self._lock:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.last_accessed = datetime.now()
                return session
            
            # Intentar cargar desde disco
            return self._load_session(session_id)
    
    def set_variable(self, session_id: str, key: str, value: Any, 
                    var_type: VariableType = VariableType.OBJECT,
                    scope: ContextScope = ContextScope.TASK,
                    expires_in: Optional[timedelta] = None,
                    metadata: Dict[str, Any] = None,
                    source_step: str = None) -> bool:
        """Establecer variable en el contexto"""
        with self._lock:
            session = self.get_session(session_id)
            if not session:
                return False
            
            # Calcular expiración
            expires_at = None
            if expires_in:
                expires_at = datetime.now() + expires_in
            elif scope == ContextScope.TEMPORARY:
                expires_at = datetime.now() + self.config['variable_ttl']
            
            # Crear variable
            variable = ContextVariable(
                key=key,
                value=value,
                type=var_type,
                scope=scope,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                expires_at=expires_at,
                metadata=metadata or {},
                source_step=source_step
            )
            
            # Guardar en sesión
            session.variables[key] = variable
            session.last_accessed = datetime.now()
            
            # Persistir cambios
            self._save_session(session)
            
            return True
    
    def get_variable(self, session_id: str, key: str) -> Optional[Any]:
        """Obtener valor de variable"""
        with self._lock:
            session = self.get_session(session_id)
            if not session:
                return None
            
            if key not in session.variables:
                return None
            
            variable = session.variables[key]
            
            # Verificar expiración
            if variable.expires_at and datetime.now() > variable.expires_at:
                del session.variables[key]
                self._save_session(session)
                return None
            
            # Actualizar acceso
            session.last_accessed = datetime.now()
            
            return variable.value
    
    def get_all_variables(self, session_id: str, scope: ContextScope = None) -> Dict[str, Any]:
        """Obtener todas las variables de un scope específico"""
        with self._lock:
            session = self.get_session(session_id)
            if not session:
                return {}
            
            variables = {}
            current_time = datetime.now()
            
            for key, variable in session.variables.items():
                # Verificar expiración
                if variable.expires_at and current_time > variable.expires_at:
                    continue
                
                # Filtrar por scope si se especifica
                if scope and variable.scope != scope:
                    continue
                
                variables[key] = variable.value
            
            return variables
    
    def delete_variable(self, session_id: str, key: str) -> bool:
        """Eliminar variable del contexto"""
        with self._lock:
            session = self.get_session(session_id)
            if not session:
                return False
            
            if key in session.variables:
                del session.variables[key]
                session.last_accessed = datetime.now()
                self._save_session(session)
                return True
            
            return False
    
    def create_checkpoint(self, session_id: str, step_id: str, 
                         description: str = "", auto_created: bool = False) -> str:
        """Crear checkpoint del estado actual"""
        with self._lock:
            session = self.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            checkpoint_id = f"cp_{step_id}_{uuid.uuid4().hex[:8]}"
            
            # Crear copia de variables para el checkpoint
            checkpoint_variables = {}
            for key, var in session.variables.items():
                checkpoint_variables[key] = ContextVariable(
                    key=var.key,
                    value=var.value,
                    type=var.type,
                    scope=var.scope,
                    created_at=var.created_at,
                    updated_at=var.updated_at,
                    expires_at=var.expires_at,
                    metadata=var.metadata.copy() if var.metadata else {},
                    source_step=var.source_step
                )
            
            checkpoint = ContextCheckpoint(
                checkpoint_id=checkpoint_id,
                task_id=session.task_id,
                step_id=step_id,
                timestamp=datetime.now(),
                variables=checkpoint_variables,
                execution_state={
                    'session_id': session_id,
                    'active_variables': len(session.variables),
                    'metadata': session.metadata.copy()
                },
                description=description,
                auto_created=auto_created
            )
            
            # Agregar checkpoint y mantener límite
            session.checkpoints.append(checkpoint)
            if len(session.checkpoints) > self.config['max_checkpoints_per_session']:
                session.checkpoints.pop(0)  # Remover el más antiguo
            
            session.last_accessed = datetime.now()
            self._save_session(session)
            
            return checkpoint_id
    
    def restore_checkpoint(self, session_id: str, checkpoint_id: str) -> bool:
        """Restaurar estado desde checkpoint"""
        with self._lock:
            session = self.get_session(session_id)
            if not session:
                return False
            
            # Buscar checkpoint
            checkpoint = None
            for cp in session.checkpoints:
                if cp.checkpoint_id == checkpoint_id:
                    checkpoint = cp
                    break
            
            if not checkpoint:
                return False
            
            # Restaurar variables
            session.variables = checkpoint.variables.copy()
            session.last_accessed = datetime.now()
            
            # Crear checkpoint de respaldo antes de restaurar
            self.create_checkpoint(
                session_id, 
                "restore_backup", 
                f"Backup before restoring {checkpoint_id}",
                auto_created=True
            )
            
            self._save_session(session)
            
            return True
    
    def get_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        """Obtener lista de checkpoints"""
        with self._lock:
            session = self.get_session(session_id)
            if not session:
                return []
            
            checkpoints = []
            for cp in session.checkpoints:
                checkpoints.append({
                    'checkpoint_id': cp.checkpoint_id,
                    'step_id': cp.step_id,
                    'timestamp': cp.timestamp.isoformat(),
                    'description': cp.description,
                    'auto_created': cp.auto_created,
                    'variables_count': len(cp.variables)
                })
            
            return checkpoints
    
    def pass_variables_to_step(self, session_id: str, step_id: str, 
                              variables: Dict[str, Any]) -> bool:
        """Pasar variables específicas a un paso"""
        with self._lock:
            success = True
            
            for key, value in variables.items():
                step_key = f"{step_id}_{key}"
                success &= self.set_variable(
                    session_id, 
                    step_key, 
                    value,
                    scope=ContextScope.STEP,
                    source_step=step_id
                )
            
            return success
    
    def get_step_variables(self, session_id: str, step_id: str) -> Dict[str, Any]:
        """Obtener variables específicas de un paso"""
        with self._lock:
            session = self.get_session(session_id)
            if not session:
                return {}
            
            step_variables = {}
            step_prefix = f"{step_id}_"
            
            for key, variable in session.variables.items():
                if key.startswith(step_prefix):
                    # Verificar expiración
                    if variable.expires_at and datetime.now() > variable.expires_at:
                        continue
                    
                    # Remover prefijo del step
                    clean_key = key[len(step_prefix):]
                    step_variables[clean_key] = variable.value
            
            return step_variables
    
    def chain_step_output(self, session_id: str, from_step: str, 
                         to_step: str, output_key: str, input_key: str = None) -> bool:
        """Encadenar output de un paso como input de otro"""
        with self._lock:
            from_key = f"{from_step}_{output_key}"
            to_key = f"{to_step}_{input_key or output_key}"
            
            value = self.get_variable(session_id, from_key)
            if value is None:
                return False
            
            return self.set_variable(
                session_id, 
                to_key, 
                value,
                scope=ContextScope.STEP,
                source_step=from_step
            )
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Obtener información detallada de la sesión"""
        with self._lock:
            session = self.get_session(session_id)
            if not session:
                return {}
            
            # Limpiar variables expiradas
            current_time = datetime.now()
            active_variables = {}
            expired_count = 0
            
            for key, variable in session.variables.items():
                if variable.expires_at and current_time > variable.expires_at:
                    expired_count += 1
                else:
                    active_variables[key] = {
                        'type': variable.type.value,
                        'scope': variable.scope.value,
                        'created_at': variable.created_at.isoformat(),
                        'updated_at': variable.updated_at.isoformat(),
                        'expires_at': variable.expires_at.isoformat() if variable.expires_at else None,
                        'source_step': variable.source_step
                    }
            
            return {
                'session_id': session_id,
                'task_id': session.task_id,
                'created_at': session.created_at.isoformat(),
                'last_accessed': session.last_accessed.isoformat(),
                'is_active': session.is_active,
                'variables': active_variables,
                'variables_count': len(active_variables),
                'expired_variables': expired_count,
                'checkpoints_count': len(session.checkpoints),
                'metadata': session.metadata
            }
    
    def close_session(self, session_id: str) -> bool:
        """Cerrar sesión y limpiar recursos"""
        with self._lock:
            session = self.get_session(session_id)
            if not session:
                return False
            
            # Crear checkpoint final
            self.create_checkpoint(
                session_id, 
                "session_close", 
                "Final checkpoint before closing session",
                auto_created=True
            )
            
            session.is_active = False
            self._save_session(session)
            
            # Remover de memoria
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            return True
    
    def _save_session(self, session: ContextSession):
        """Guardar sesión en disco"""
        try:
            session_file = self.storage_path / f"{session.session_id}.pkl"
            with open(session_file, 'wb') as f:
                pickle.dump(session, f)
        except Exception as e:
            print(f"Error saving session {session.session_id}: {e}")
    
    def _load_session(self, session_id: str) -> Optional[ContextSession]:
        """Cargar sesión desde disco"""
        try:
            session_file = self.storage_path / f"{session_id}.pkl"
            if session_file.exists():
                with open(session_file, 'rb') as f:
                    session = pickle.load(f)
                    if session.is_active:
                        self.active_sessions[session_id] = session
                        return session
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
        
        return None
    
    def _load_persistent_sessions(self):
        """Cargar sesiones persistentes al inicio"""
        try:
            for session_file in self.storage_path.glob("*.pkl"):
                session_id = session_file.stem
                self._load_session(session_id)
        except Exception as e:
            print(f"Error loading persistent sessions: {e}")
    
    def _start_cleanup_thread(self):
        """Iniciar thread de limpieza automática"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(self.config['cleanup_interval'].total_seconds())
                    self._cleanup_expired_data()
                except Exception as e:
                    print(f"Error in cleanup thread: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_expired_data(self):
        """Limpiar datos expirados"""
        with self._lock:
            current_time = datetime.now()
            sessions_to_remove = []
            
            for session_id, session in self.active_sessions.items():
                # Verificar TTL de sesión
                if current_time - session.last_accessed > self.config['session_ttl']:
                    sessions_to_remove.append(session_id)
                    continue
                
                # Limpiar variables expiradas
                expired_variables = []
                for key, variable in session.variables.items():
                    if variable.expires_at and current_time > variable.expires_at:
                        expired_variables.append(key)
                
                for key in expired_variables:
                    del session.variables[key]
                
                # Limpiar checkpoints expirados
                expired_checkpoints = []
                for checkpoint in session.checkpoints:
                    if current_time - checkpoint.timestamp > self.config['checkpoint_ttl']:
                        expired_checkpoints.append(checkpoint)
                
                for checkpoint in expired_checkpoints:
                    session.checkpoints.remove(checkpoint)
                
                # Guardar cambios si hubo limpieza
                if expired_variables or expired_checkpoints:
                    self._save_session(session)
            
            # Remover sesiones expiradas
            for session_id in sessions_to_remove:
                self.close_session(session_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema"""
        with self._lock:
            total_variables = 0
            total_checkpoints = 0
            
            for session in self.active_sessions.values():
                total_variables += len(session.variables)
                total_checkpoints += len(session.checkpoints)
            
            return {
                'active_sessions': len(self.active_sessions),
                'total_variables': total_variables,
                'total_checkpoints': total_checkpoints,
                'storage_path': str(self.storage_path),
                'config': {
                    'max_sessions': self.config['max_sessions'],
                    'session_ttl_hours': self.config['session_ttl'].total_seconds() / 3600,
                    'checkpoint_ttl_hours': self.config['checkpoint_ttl'].total_seconds() / 3600
                }
            }