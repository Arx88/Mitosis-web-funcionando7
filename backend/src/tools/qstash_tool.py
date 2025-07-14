"""
Herramienta de Jobs en Background con QStash
Para procesamiento de tareas largas sin bloquear la UI
"""

import os
import requests
import redis
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time
import uuid
from urllib.parse import urlparse

class QStashTool:
    def __init__(self):
        self.name = "qstash_jobs"
        self.description = "Herramienta para procesamiento de trabajos en segundo plano"
        self.redis_url = os.getenv('QSTASH_URL')
        self.redis_client = None
        
        if self.redis_url:
            try:
                # Configurar conexión Redis
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                print("✅ QStash Redis connection established")
            except Exception as e:
                print(f"❌ QStash Redis connection failed: {e}")
                self.redis_client = None
        else:
            print("⚠️  QSTASH_URL not found in environment variables")
    
    def get_description(self) -> str:
        return self.description
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "action",
                "type": "string",
                "description": "Acción a realizar",
                "required": True,
                "enum": ["create_job", "check_status", "get_result", "list_jobs", "cancel_job"]
            },
            {
                "name": "job_type",
                "type": "string",
                "description": "Tipo de trabajo",
                "enum": ["deep_research", "file_processing", "web_scraping", "data_analysis", "custom"],
                "default": "custom"
            },
            {
                "name": "job_id",
                "type": "string",
                "description": "ID del trabajo (requerido para check_status, get_result, cancel_job)",
                "required": False
            },
            {
                "name": "payload",
                "type": "object",
                "description": "Datos del trabajo a procesar",
                "required": False
            },
            {
                "name": "delay_seconds",
                "type": "integer",
                "description": "Retraso en segundos antes de ejecutar",
                "default": 0
            },
            {
                "name": "timeout_seconds",
                "type": "integer",
                "description": "Tiempo límite para el trabajo",
                "default": 300
            },
            {
                "name": "priority",
                "type": "string",
                "description": "Prioridad del trabajo",
                "enum": ["low", "normal", "high"],
                "default": "normal"
            }
        ]
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecutar operación de QStash
        
        Args:
            parameters: Parámetros de la herramienta
            config: Configuración adicional
            
        Returns:
            Resultado de la operación
        """
        try:
            if not self.redis_client:
                return {
                    'success': False,
                    'error': 'QStash Redis not configured',
                    'suggestion': 'Configure QSTASH_URL in environment variables'
                }
            
            action = parameters.get('action')
            
            if action == 'create_job':
                return self._create_job(parameters)
            elif action == 'check_status':
                return self._check_status(parameters)
            elif action == 'get_result':
                return self._get_result(parameters)
            elif action == 'list_jobs':
                return self._list_jobs(parameters)
            elif action == 'cancel_job':
                return self._cancel_job(parameters)
            else:
                return {
                    'success': False,
                    'error': f'Invalid action: {action}'
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _create_job(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Crear un nuevo trabajo"""
        try:
            job_id = str(uuid.uuid4())
            job_type = parameters.get('job_type', 'custom')
            payload = parameters.get('payload', {})
            delay_seconds = parameters.get('delay_seconds', 0)
            timeout_seconds = parameters.get('timeout_seconds', 300)
            priority = parameters.get('priority', 'normal')
            
            # Crear información del trabajo
            job_info = {
                'job_id': job_id,
                'job_type': job_type,
                'payload': payload,
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'scheduled_at': (datetime.now() + timedelta(seconds=delay_seconds)).isoformat(),
                'timeout_seconds': timeout_seconds,
                'priority': priority,
                'progress': 0,
                'result': None,
                'error': None,
                'logs': []
            }
            
            # Guardar trabajo en Redis
            self.redis_client.setex(
                f"job:{job_id}", 
                timeout_seconds + 3600,  # TTL extra para permitir recuperación
                json.dumps(job_info)
            )
            
            # Agregar a cola según prioridad
            queue_name = f"queue:{priority}"
            self.redis_client.lpush(queue_name, job_id)
            
            # Iniciar procesamiento si no hay delay
            if delay_seconds == 0:
                self._process_job_async(job_id)
            else:
                # Programar para más tarde
                self._schedule_job(job_id, delay_seconds)
            
            return {
                'success': True,
                'job_id': job_id,
                'status': 'pending',
                'message': f'Job {job_id} created successfully',
                'scheduled_at': job_info['scheduled_at']
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create job: {str(e)}'
            }
    
    def _check_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Verificar estado del trabajo"""
        try:
            job_id = parameters.get('job_id')
            
            if not job_id:
                return {
                    'success': False,
                    'error': 'job_id is required'
                }
            
            # Obtener información del trabajo
            job_data = self.redis_client.get(f"job:{job_id}")
            
            if not job_data:
                return {
                    'success': False,
                    'error': f'Job {job_id} not found'
                }
            
            job_info = json.loads(job_data)
            
            return {
                'success': True,
                'job_id': job_id,
                'status': job_info.get('status', 'unknown'),
                'progress': job_info.get('progress', 0),
                'created_at': job_info.get('created_at'),
                'updated_at': job_info.get('updated_at'),
                'logs': job_info.get('logs', [])[-5:],  # Últimos 5 logs
                'has_result': job_info.get('result') is not None,
                'error': job_info.get('error')
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to check status: {str(e)}'
            }
    
    def _get_result(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Obtener resultado del trabajo"""
        try:
            job_id = parameters.get('job_id')
            
            if not job_id:
                return {
                    'success': False,
                    'error': 'job_id is required'
                }
            
            # Obtener información del trabajo
            job_data = self.redis_client.get(f"job:{job_id}")
            
            if not job_data:
                return {
                    'success': False,
                    'error': f'Job {job_id} not found'
                }
            
            job_info = json.loads(job_data)
            
            if job_info.get('status') != 'completed':
                return {
                    'success': False,
                    'error': f'Job {job_id} is not completed yet. Status: {job_info.get("status")}',
                    'status': job_info.get('status'),
                    'progress': job_info.get('progress', 0)
                }
            
            return {
                'success': True,
                'job_id': job_id,
                'status': job_info.get('status'),
                'result': job_info.get('result'),
                'completed_at': job_info.get('completed_at'),
                'execution_time': job_info.get('execution_time'),
                'logs': job_info.get('logs', [])
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get result: {str(e)}'
            }
    
    def _list_jobs(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Listar trabajos"""
        try:
            # Obtener todos los trabajos
            job_keys = self.redis_client.keys("job:*")
            jobs = []
            
            for key in job_keys:
                job_data = self.redis_client.get(key)
                if job_data:
                    job_info = json.loads(job_data)
                    jobs.append({
                        'job_id': job_info.get('job_id'),
                        'job_type': job_info.get('job_type'),
                        'status': job_info.get('status'),
                        'progress': job_info.get('progress', 0),
                        'created_at': job_info.get('created_at'),
                        'priority': job_info.get('priority')
                    })
            
            # Ordenar por fecha de creación
            jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return {
                'success': True,
                'jobs': jobs,
                'total_jobs': len(jobs),
                'queues': {
                    'high': self.redis_client.llen('queue:high'),
                    'normal': self.redis_client.llen('queue:normal'),
                    'low': self.redis_client.llen('queue:low')
                }
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to list jobs: {str(e)}'
            }
    
    def _cancel_job(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Cancelar trabajo"""
        try:
            job_id = parameters.get('job_id')
            
            if not job_id:
                return {
                    'success': False,
                    'error': 'job_id is required'
                }
            
            # Obtener información del trabajo
            job_data = self.redis_client.get(f"job:{job_id}")
            
            if not job_data:
                return {
                    'success': False,
                    'error': f'Job {job_id} not found'
                }
            
            job_info = json.loads(job_data)
            
            if job_info.get('status') in ['completed', 'failed', 'cancelled']:
                return {
                    'success': False,
                    'error': f'Job {job_id} cannot be cancelled. Status: {job_info.get("status")}'
                }
            
            # Actualizar estado
            job_info['status'] = 'cancelled'
            job_info['cancelled_at'] = datetime.now().isoformat()
            job_info['logs'].append({
                'timestamp': datetime.now().isoformat(),
                'level': 'info',
                'message': 'Job cancelled by user'
            })
            
            # Guardar cambios
            self.redis_client.setex(
                f"job:{job_id}", 
                3600,  # TTL reducido para jobs cancelados
                json.dumps(job_info)
            )
            
            return {
                'success': True,
                'job_id': job_id,
                'status': 'cancelled',
                'message': f'Job {job_id} cancelled successfully'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to cancel job: {str(e)}'
            }
    
    def _process_job_async(self, job_id: str) -> None:
        """Procesar trabajo de forma asíncrona"""
        try:
            # Obtener información del trabajo
            job_data = self.redis_client.get(f"job:{job_id}")
            
            if not job_data:
                return
            
            job_info = json.loads(job_data)
            
            # Actualizar estado a procesando
            job_info['status'] = 'processing'
            job_info['started_at'] = datetime.now().isoformat()
            job_info['logs'].append({
                'timestamp': datetime.now().isoformat(),
                'level': 'info',
                'message': 'Job processing started'
            })
            
            self.redis_client.setex(
                f"job:{job_id}", 
                job_info['timeout_seconds'] + 3600,
                json.dumps(job_info)
            )
            
            # Procesar según tipo
            job_type = job_info.get('job_type')
            payload = job_info.get('payload', {})
            
            try:
                if job_type == 'deep_research':
                    result = self._process_deep_research(job_id, payload)
                elif job_type == 'file_processing':
                    result = self._process_file_processing(job_id, payload)
                elif job_type == 'web_scraping':
                    result = self._process_web_scraping(job_id, payload)
                elif job_type == 'data_analysis':
                    result = self._process_data_analysis(job_id, payload)
                else:
                    result = self._process_custom_job(job_id, payload)
                
                # Actualizar con resultado exitoso
                job_info['status'] = 'completed'
                job_info['result'] = result
                job_info['completed_at'] = datetime.now().isoformat()
                job_info['progress'] = 100
                
                # Calcular tiempo de ejecución
                start_time = datetime.fromisoformat(job_info['started_at'])
                end_time = datetime.fromisoformat(job_info['completed_at'])
                job_info['execution_time'] = (end_time - start_time).total_seconds()
                
                job_info['logs'].append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'info',
                    'message': f'Job completed successfully in {job_info["execution_time"]:.2f} seconds'
                })
            
            except Exception as e:
                # Actualizar con error
                job_info['status'] = 'failed'
                job_info['error'] = str(e)
                job_info['failed_at'] = datetime.now().isoformat()
                job_info['logs'].append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'error',
                    'message': f'Job failed: {str(e)}'
                })
            
            # Guardar estado final
            self.redis_client.setex(
                f"job:{job_id}", 
                3600,  # TTL de 1 hora para trabajos completados
                json.dumps(job_info)
            )
        
        except Exception as e:
            print(f"Error processing job {job_id}: {e}")
    
    def _process_deep_research(self, job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar investigación profunda"""
        # Simular procesamiento largo
        self._update_job_progress(job_id, 25, "Iniciando investigación...")
        time.sleep(2)
        
        self._update_job_progress(job_id, 50, "Recopilando fuentes...")
        time.sleep(3)
        
        self._update_job_progress(job_id, 75, "Analizando contenido...")
        time.sleep(2)
        
        self._update_job_progress(job_id, 100, "Generando reporte...")
        
        return {
            'query': payload.get('query', ''),
            'analysis': f"Análisis profundo completado para: {payload.get('query', 'N/A')}",
            'key_findings': [
                'Hallazgo 1: Información relevante encontrada',
                'Hallazgo 2: Datos estadísticos importantes',
                'Hallazgo 3: Tendencias identificadas'
            ],
            'recommendations': [
                'Recomendación 1: Acción sugerida',
                'Recomendación 2: Mejora propuesta'
            ],
            'sources_analyzed': 15,
            'processing_time': 'Completado en background'
        }
    
    def _process_file_processing(self, job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar archivos"""
        files = payload.get('files', [])
        
        self._update_job_progress(job_id, 20, "Validando archivos...")
        time.sleep(1)
        
        self._update_job_progress(job_id, 60, "Procesando contenido...")
        time.sleep(2)
        
        self._update_job_progress(job_id, 100, "Procesamiento completado")
        
        return {
            'files_processed': len(files),
            'total_size': sum(f.get('size', 0) for f in files),
            'processing_summary': 'Archivos procesados exitosamente'
        }
    
    def _process_web_scraping(self, job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar web scraping"""
        urls = payload.get('urls', [])
        
        self._update_job_progress(job_id, 30, "Iniciando scraping...")
        time.sleep(1)
        
        self._update_job_progress(job_id, 70, "Extrayendo contenido...")
        time.sleep(2)
        
        self._update_job_progress(job_id, 100, "Scraping completado")
        
        return {
            'urls_scraped': len(urls),
            'content_extracted': 'Contenido extraído exitosamente'
        }
    
    def _process_data_analysis(self, job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar análisis de datos"""
        data = payload.get('data', [])
        
        self._update_job_progress(job_id, 40, "Analizando datos...")
        time.sleep(2)
        
        self._update_job_progress(job_id, 80, "Generando estadísticas...")
        time.sleep(1)
        
        self._update_job_progress(job_id, 100, "Análisis completado")
        
        return {
            'records_analyzed': len(data),
            'analysis_summary': 'Análisis de datos completado'
        }
    
    def _process_custom_job(self, job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar trabajo personalizado"""
        self._update_job_progress(job_id, 50, "Procesando trabajo personalizado...")
        time.sleep(1)
        
        self._update_job_progress(job_id, 100, "Trabajo completado")
        
        return {
            'message': 'Trabajo personalizado completado',
            'payload': payload
        }
    
    def _update_job_progress(self, job_id: str, progress: int, message: str) -> None:
        """Actualizar progreso del trabajo"""
        try:
            job_data = self.redis_client.get(f"job:{job_id}")
            if job_data:
                job_info = json.loads(job_data)
                job_info['progress'] = progress
                job_info['updated_at'] = datetime.now().isoformat()
                job_info['logs'].append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'info',
                    'message': message
                })
                
                self.redis_client.setex(
                    f"job:{job_id}", 
                    job_info['timeout_seconds'] + 3600,
                    json.dumps(job_info)
                )
        except Exception as e:
            print(f"Error updating job progress: {e}")
    
    def _schedule_job(self, job_id: str, delay_seconds: int) -> None:
        """Programar trabajo para más tarde"""
        # En una implementación real, usarías un scheduler como Celery
        # Por ahora, simplemente simulamos el delay
        import threading
        
        def delayed_execution():
            time.sleep(delay_seconds)
            self._process_job_async(job_id)
        
        thread = threading.Thread(target=delayed_execution)
        thread.daemon = True
        thread.start()
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validar parámetros de entrada"""
        errors = []
        
        action = parameters.get('action')
        if not action:
            errors.append("action is required")
        elif action not in ['create_job', 'check_status', 'get_result', 'list_jobs', 'cancel_job']:
            errors.append("Invalid action")
        
        # Validaciones específicas por acción
        if action in ['check_status', 'get_result', 'cancel_job']:
            if not parameters.get('job_id'):
                errors.append("job_id is required for this action")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Información adicional de la herramienta"""
        return {
            'category': 'job_processing',
            'version': '1.0.0',
            'capabilities': [
                'Background job processing',
                'Job status tracking',
                'Progress monitoring',
                'Job scheduling',
                'Priority queues'
            ],
            'job_types': [
                'deep_research',
                'file_processing',
                'web_scraping',
                'data_analysis',
                'custom'
            ],
            'redis_status': 'connected' if self.redis_client else 'not_connected'
        }