"""
Sistema de Feedback en Tiempo Real
===================================

Este módulo proporciona feedback en tiempo real sobre lo que el agente
está recolectando y procesando, permitiendo al usuario ver el progreso
de manera transparente.

Características:
- Recolección de información en tiempo real
- Mostrar datos conforme se van obteniendo
- Documentación automática del proceso
- Actualizaciones WebSocket para el frontend
"""

import logging
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)

@dataclass
class DataCollectionEntry:
    """Entrada de datos recolectados en tiempo real."""
    id: str
    timestamp: str
    source: str
    data_type: str
    title: str
    content: str
    url: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class FeedbackUpdate:
    """Actualización de feedback para el frontend."""
    id: str
    task_id: str
    step_id: str
    update_type: str  # 'data_collected', 'analysis_progress', 'insight_found'
    title: str
    content: str
    data: Dict[str, Any]
    timestamp: str
    progress_percentage: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class RealTimeFeedbackManager:
    """
    Gestor de feedback en tiempo real para mostrar el progreso de recolección de datos.
    """
    
    def __init__(self, websocket_manager=None):
        self.websocket_manager = websocket_manager
        self.task_data_collections = {}  # task_id -> List[DataCollectionEntry]
        self.task_progress = {}  # task_id -> Dict[step_id, progress_info]
        
    def start_data_collection_for_task(self, task_id: str, step_id: str, step_title: str):
        """Inicia la recolección de datos para una tarea específica."""
        if task_id not in self.task_data_collections:
            self.task_data_collections[task_id] = []
        
        if task_id not in self.task_progress:
            self.task_progress[task_id] = {}
        
        self.task_progress[task_id][step_id] = {
            'step_title': step_title,
            'started_at': datetime.now().isoformat(),
            'data_collected': 0,
            'status': 'collecting',
            'insights': []
        }
        
        # Notificar al frontend que se inició la recolección
        self._send_feedback_update(
            task_id=task_id,
            step_id=step_id,
            update_type='collection_started',
            title=f"Iniciando recolección de datos",
            content=f"Comenzando recolección para: {step_title}",
            data={'step_title': step_title},
            progress_percentage=0
        )
        
        logger.info(f"🔄 Started data collection for task {task_id}, step {step_id}")
    
    def add_collected_data(self, task_id: str, step_id: str, source: str, 
                          data_type: str, title: str, content: str, 
                          url: str = None, metadata: Dict[str, Any] = None) -> str:
        """
        Agrega datos recolectados y notifica al frontend inmediatamente.
        
        Args:
            task_id: ID de la tarea
            step_id: ID del paso actual
            source: Fuente de los datos (ej: "búsqueda web", "análisis")
            data_type: Tipo de datos (ej: "search_result", "insight", "summary")
            title: Título de la información
            content: Contenido de la información
            url: URL si aplica
            metadata: Metadatos adicionales
            
        Returns:
            ID del entry de datos creado
        """
        entry_id = str(uuid.uuid4())
        
        entry = DataCollectionEntry(
            id=entry_id,
            timestamp=datetime.now().isoformat(),
            source=source,
            data_type=data_type,
            title=title,
            content=content,
            url=url,
            metadata=metadata or {}
        )
        
        # Almacenar la entrada
        if task_id not in self.task_data_collections:
            self.task_data_collections[task_id] = []
        
        self.task_data_collections[task_id].append(entry)
        
        # Actualizar progreso
        if task_id in self.task_progress and step_id in self.task_progress[task_id]:
            self.task_progress[task_id][step_id]['data_collected'] += 1
            self.task_progress[task_id][step_id]['last_update'] = datetime.now().isoformat()
        
        # Enviar actualización inmediata al frontend
        self._send_feedback_update(
            task_id=task_id,
            step_id=step_id,
            update_type='data_collected',
            title=f"📥 Información recolectada: {title}",
            content=content[:200] + "..." if len(content) > 200 else content,
            data={
                'entry_id': entry_id,
                'source': source,
                'data_type': data_type,
                'title': title,
                'full_content': content,
                'url': url,
                'metadata': metadata,
                'collection_count': self.task_progress[task_id][step_id]['data_collected'] if task_id in self.task_progress and step_id in self.task_progress[task_id] else 1
            },
            progress_percentage=min(self.task_progress[task_id][step_id]['data_collected'] * 10, 90) if task_id in self.task_progress and step_id in self.task_progress[task_id] else 10
        )
        
        logger.info(f"📥 Added data entry for task {task_id}: {title}")
        return entry_id
    
    def add_insight(self, task_id: str, step_id: str, insight_type: str, 
                   title: str, content: str, confidence: float = 1.0):
        """Agrega un insight o análisis en tiempo real."""
        insight_id = str(uuid.uuid4())
        
        insight = {
            'id': insight_id,
            'type': insight_type,
            'title': title,
            'content': content,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }
        
        # Almacenar en progreso
        if task_id in self.task_progress and step_id in self.task_progress[task_id]:
            if 'insights' not in self.task_progress[task_id][step_id]:
                self.task_progress[task_id][step_id]['insights'] = []
            self.task_progress[task_id][step_id]['insights'].append(insight)
        
        # Notificar al frontend
        confidence_emoji = "🎯" if confidence > 0.8 else "💡" if confidence > 0.6 else "🤔"
        
        self._send_feedback_update(
            task_id=task_id,
            step_id=step_id,
            update_type='insight_found',
            title=f"{confidence_emoji} Insight: {title}",
            content=content,
            data={
                'insight_id': insight_id,
                'insight_type': insight_type,
                'confidence': confidence,
                'timestamp': insight['timestamp']
            },
            progress_percentage=75  # Los insights suelen venir al final del procesamiento
        )
        
        logger.info(f"💡 Added insight for task {task_id}: {title} (confidence: {confidence})")
        return insight_id
    
    def update_step_progress(self, task_id: str, step_id: str, progress_percentage: int, 
                           status_message: str = None):
        """Actualiza el progreso de un paso específico."""
        if task_id in self.task_progress and step_id in self.task_progress[task_id]:
            self.task_progress[task_id][step_id]['progress'] = progress_percentage
            self.task_progress[task_id][step_id]['last_update'] = datetime.now().isoformat()
            
            if status_message:
                self.task_progress[task_id][step_id]['status_message'] = status_message
        
        # Notificar progreso al frontend
        self._send_feedback_update(
            task_id=task_id,
            step_id=step_id,
            update_type='progress_update',
            title=f"Progreso: {progress_percentage}%",
            content=status_message or f"Progreso actualizado: {progress_percentage}%",
            data={'progress': progress_percentage},
            progress_percentage=progress_percentage
        )
    
    def complete_step_collection(self, task_id: str, step_id: str, summary: str = None):
        """Marca la recolección de un paso como completada."""
        if task_id in self.task_progress and step_id in self.task_progress[task_id]:
            self.task_progress[task_id][step_id]['status'] = 'completed'
            self.task_progress[task_id][step_id]['completed_at'] = datetime.now().isoformat()
            
            data_count = self.task_progress[task_id][step_id].get('data_collected', 0)
            insights_count = len(self.task_progress[task_id][step_id].get('insights', []))
        
        # Enviar resumen de finalización
        summary_text = summary or f"Recolección completada: {data_count} datos, {insights_count} insights"
        
        self._send_feedback_update(
            task_id=task_id,
            step_id=step_id,
            update_type='collection_completed',
            title="✅ Recolección completada",
            content=summary_text,
            data={
                'data_collected': data_count,
                'insights_found': insights_count,
                'completion_time': datetime.now().isoformat()
            },
            progress_percentage=100
        )
        
        logger.info(f"✅ Completed data collection for task {task_id}, step {step_id}")
    
    def get_task_collected_data(self, task_id: str) -> List[Dict[str, Any]]:
        """Obtiene todos los datos recolectados para una tarea."""
        if task_id not in self.task_data_collections:
            return []
        
        return [entry.to_dict() for entry in self.task_data_collections[task_id]]
    
    def get_task_progress_summary(self, task_id: str) -> Dict[str, Any]:
        """Obtiene un resumen del progreso de recolección para una tarea."""
        if task_id not in self.task_progress:
            return {}
        
        progress_summary = {}
        for step_id, step_info in self.task_progress[task_id].items():
            progress_summary[step_id] = {
                'step_title': step_info.get('step_title', ''),
                'status': step_info.get('status', 'unknown'),
                'data_collected': step_info.get('data_collected', 0),
                'insights_count': len(step_info.get('insights', [])),
                'started_at': step_info.get('started_at'),
                'completed_at': step_info.get('completed_at'),
                'progress': step_info.get('progress', 0)
            }
        
        return progress_summary
    
    def generate_collection_document(self, task_id: str) -> str:
        """
        Genera un documento con toda la información recolectada durante la tarea.
        
        Returns:
            String con documento markdown de la información recolectada
        """
        if task_id not in self.task_data_collections:
            return "# Información Recolectada\n\nNo se recolectó información para esta tarea."
        
        data_entries = self.task_data_collections[task_id]
        progress_info = self.task_progress.get(task_id, {})
        
        # Generar documento markdown
        doc = f"""# Información Recolectada en Tiempo Real
*Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Tarea ID: {task_id}*

## Resumen de Recolección
- **Total de datos recolectados**: {len(data_entries)}
- **Pasos procesados**: {len(progress_info)}

"""
        
        # Agrupar datos por paso si hay información de progreso
        if progress_info:
            for step_id, step_info in progress_info.items():
                doc += f"### Paso: {step_info.get('step_title', step_id)}\n"
                doc += f"- **Estado**: {step_info.get('status', 'unknown')}\n"
                doc += f"- **Datos recolectados**: {step_info.get('data_collected', 0)}\n"
                doc += f"- **Insights encontrados**: {len(step_info.get('insights', []))}\n\n"
                
                # Mostrar insights del paso
                insights = step_info.get('insights', [])
                if insights:
                    doc += "#### Insights Encontrados:\n"
                    for insight in insights:
                        doc += f"- **{insight['title']}** (Confianza: {insight['confidence']:.2f})\n"
                        doc += f"  {insight['content']}\n\n"
        
        # Mostrar todos los datos recolectados
        doc += "## Datos Recolectados Detallados\n\n"
        
        for i, entry in enumerate(data_entries, 1):
            doc += f"### {i}. {entry.title}\n"
            doc += f"- **Fuente**: {entry.source}\n"
            doc += f"- **Tipo**: {entry.data_type}\n"
            doc += f"- **Timestamp**: {entry.timestamp}\n"
            
            if entry.url:
                doc += f"- **URL**: [{entry.url}]({entry.url})\n"
            
            doc += f"\n**Contenido**:\n{entry.content}\n\n"
            
            if entry.metadata:
                doc += f"**Metadatos**: {json.dumps(entry.metadata, indent=2)}\n\n"
            
            doc += "---\n\n"
        
        return doc
    
    def _send_feedback_update(self, task_id: str, step_id: str, update_type: str,
                             title: str, content: str, data: Dict[str, Any],
                             progress_percentage: int = 0):
        """Envía actualización de feedback al frontend vía WebSocket."""
        if not self.websocket_manager:
            return
        
        update = FeedbackUpdate(
            id=str(uuid.uuid4()),
            task_id=task_id,
            step_id=step_id,
            update_type=update_type,
            title=title,
            content=content,
            data=data,
            timestamp=datetime.now().isoformat(),
            progress_percentage=progress_percentage
        )
        
        try:
            # Enviar update específico de feedback
            self.websocket_manager.send_task_update(task_id, {
                'type': 'real_time_feedback',
                'feedback_update': update.to_dict(),
                'timestamp': update.timestamp
            })
            
            logger.debug(f"📡 Sent feedback update: {update_type} for task {task_id}")
            
        except Exception as e:
            logger.error(f"❌ Error sending feedback update: {str(e)}")
    
    def cleanup_task_data(self, task_id: str):
        """Limpia los datos de una tarea completada."""
        if task_id in self.task_data_collections:
            del self.task_data_collections[task_id]
        
        if task_id in self.task_progress:
            del self.task_progress[task_id]
        
        logger.info(f"🧹 Cleaned up feedback data for task {task_id}")

# Instancia global del gestor de feedback
_feedback_manager_instance = None

def get_feedback_manager(websocket_manager=None) -> RealTimeFeedbackManager:
    """Obtiene la instancia del gestor de feedback en tiempo real."""
    global _feedback_manager_instance
    if _feedback_manager_instance is None:
        _feedback_manager_instance = RealTimeFeedbackManager(websocket_manager)
    elif websocket_manager and not _feedback_manager_instance.websocket_manager:
        _feedback_manager_instance.websocket_manager = websocket_manager
    return _feedback_manager_instance