"""
🔄 SISTEMA DE FEEDBACK EN TIEMPO REAL - MITOSIS
Documenta y transmite la información que el agente recolecta paso a paso
"""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

class RealTimeFeedbackSystem:
    """Sistema que documenta y transmite la información recolectada por el agente en tiempo real"""
    
    def __init__(self, task_id: str, websocket_manager=None):
        self.task_id = task_id
        self.websocket_manager = websocket_manager
        self.collected_data = {
            'sources': [],  # Sitios visitados y su información
            'extracted_info': [],  # Información específica extraída
            'screenshots': [],  # Screenshots con contexto
            'progress': [],  # Pasos completados
            'start_time': time.time()
        }
        
    def log_website_visit(self, url: str, title: str, content_preview: str = "", source_type: str = "web"):
        """Registra cuando el agente visita un sitio web"""
        visit_data = {
            'timestamp': time.time(),
            'url': url,
            'title': title,
            'content_preview': content_preview[:500] + "..." if len(content_preview) > 500 else content_preview,
            'source_type': source_type,
            'content_length': len(content_preview)
        }
        
        self.collected_data['sources'].append(visit_data)
        
        # Enviar actualización en tiempo real
        self._emit_feedback({
            'type': 'website_visited',
            'message': f'🌐 Visitando: {title}',
            'data': {
                'url': url,
                'title': title,
                'content_preview': content_preview[:200] + "..." if len(content_preview) > 200 else content_preview,
                'source_number': len(self.collected_data['sources'])
            }
        })
        
    def log_information_extracted(self, source_url: str, info_type: str, extracted_content: str, relevance_score: float = 0.0):
        """Registra información específica extraída de un sitio"""
        extraction_data = {
            'timestamp': time.time(),
            'source_url': source_url,
            'info_type': info_type,
            'content': extracted_content,
            'relevance_score': relevance_score,
            'content_length': len(extracted_content)
        }
        
        self.collected_data['extracted_info'].append(extraction_data)
        
        # Enviar actualización detallada
        self._emit_feedback({
            'type': 'information_extracted',
            'message': f'📊 Información extraída: {info_type}',
            'data': {
                'source_url': source_url,
                'info_type': info_type,
                'content_preview': extracted_content[:300] + "..." if len(extracted_content) > 300 else extracted_content,
                'relevance_score': relevance_score,
                'extraction_number': len(self.collected_data['extracted_info'])
            }
        })
        
    def log_screenshot_context(self, screenshot_url: str, page_url: str, page_title: str, action_performed: str = ""):
        """Registra el contexto de un screenshot"""
        screenshot_data = {
            'timestamp': time.time(),
            'screenshot_url': screenshot_url,
            'page_url': page_url,
            'page_title': page_title,
            'action_performed': action_performed
        }
        
        self.collected_data['screenshots'].append(screenshot_data)
        
        # Enviar actualización de screenshot con contexto
        self._emit_feedback({
            'type': 'screenshot_with_context',
            'message': f'📸 Capturando: {page_title}',
            'data': {
                'screenshot_url': screenshot_url,
                'page_url': page_url,
                'page_title': page_title,
                'action_performed': action_performed,
                'screenshot_number': len(self.collected_data['screenshots'])
            }
        })
        
    def log_step_progress(self, step_name: str, step_description: str, completion_percentage: float, details: str = ""):
        """Registra el progreso de un paso específico"""
        progress_data = {
            'timestamp': time.time(),
            'step_name': step_name,
            'step_description': step_description,
            'completion_percentage': completion_percentage,
            'details': details
        }
        
        self.collected_data['progress'].append(progress_data)
        
        # Enviar actualización de progreso
        self._emit_feedback({
            'type': 'step_progress',
            'message': f'⚡ {step_name}: {completion_percentage:.1f}%',
            'data': {
                'step_name': step_name,
                'step_description': step_description,
                'completion_percentage': completion_percentage,
                'details': details,
                'total_steps_completed': len(self.collected_data['progress'])
            }
        })
        
    def generate_real_time_summary(self) -> Dict[str, Any]:
        """Genera un resumen en tiempo real de toda la información recolectada"""
        current_time = time.time()
        elapsed_time = current_time - self.collected_data['start_time']
        
        summary = {
            'task_id': self.task_id,
            'elapsed_time_seconds': elapsed_time,
            'elapsed_time_formatted': f"{int(elapsed_time//60)}m {int(elapsed_time%60)}s",
            'statistics': {
                'sources_visited': len(self.collected_data['sources']),
                'information_extracted': len(self.collected_data['extracted_info']),
                'screenshots_captured': len(self.collected_data['screenshots']),
                'steps_completed': len(self.collected_data['progress'])
            },
            'recent_activity': self._get_recent_activity(),
            'data_quality': self._calculate_data_quality()
        }
        
        return summary
        
    def _get_recent_activity(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Obtiene la actividad más reciente"""
        all_activities = []
        
        # Agregar todas las actividades con timestamps
        for source in self.collected_data['sources']:
            all_activities.append({
                'type': 'website_visit',
                'timestamp': source['timestamp'],
                'description': f"Visitó: {source['title']}",
                'url': source['url']
            })
            
        for extraction in self.collected_data['extracted_info']:
            all_activities.append({
                'type': 'information_extraction',
                'timestamp': extraction['timestamp'],
                'description': f"Extrajo: {extraction['info_type']}",
                'content_length': extraction['content_length']
            })
            
        for progress in self.collected_data['progress']:
            all_activities.append({
                'type': 'step_progress',
                'timestamp': progress['timestamp'],
                'description': f"Completó: {progress['step_name']} ({progress['completion_percentage']:.1f}%)"
            })
        
        # Ordenar por timestamp y tomar los más recientes
        all_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_activities[:limit]
        
    def _calculate_data_quality(self) -> Dict[str, Any]:
        """Calcula métricas de calidad de los datos recolectados"""
        total_content_length = sum(info['content_length'] for info in self.collected_data['extracted_info'])
        avg_relevance = sum(info.get('relevance_score', 0) for info in self.collected_data['extracted_info']) / max(len(self.collected_data['extracted_info']), 1)
        
        return {
            'total_content_characters': total_content_length,
            'average_relevance_score': avg_relevance,
            'sources_per_minute': len(self.collected_data['sources']) / max((time.time() - self.collected_data['start_time']) / 60, 1),
            'extraction_efficiency': len(self.collected_data['extracted_info']) / max(len(self.collected_data['sources']), 1)
        }
        
    def _emit_feedback(self, feedback_data: Dict[str, Any]):
        """Emite feedback en tiempo real via WebSocket y guarda en archivo"""
        feedback_payload = {
            **feedback_data,
            'task_id': self.task_id,
            'timestamp': time.time(),
            'summary': self.generate_real_time_summary()
        }
        
        # Emitir via WebSocket
        if self.websocket_manager:
            try:
                self.websocket_manager.emit_to_task(
                    self.task_id,
                    'real_time_feedback',
                    feedback_payload
                )
            except Exception as e:
                print(f"Error emitting feedback: {e}")
        
        # Guardar en archivo para persistencia
        try:
            feedback_file = f"/tmp/feedback_{self.task_id}.json"
            complete_report = self.get_complete_report()
            with open(feedback_file, 'w') as f:
                json.dump(complete_report, f, indent=2)
        except Exception as e:
            print(f"Error saving feedback to file: {e}")
                
    def get_complete_report(self) -> Dict[str, Any]:
        """Genera un reporte completo de toda la información recolectada"""
        return {
            'task_id': self.task_id,
            'collection_summary': self.generate_real_time_summary(),
            'detailed_data': self.collected_data,
            'generated_at': time.time()
        }