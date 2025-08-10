"""
📄 DOCUMENTO EN VIVO - SISTEMA DE RECOLECCIÓN EN TIEMPO REAL
===========================================================

Este módulo maneja la creación y actualización en tiempo real de un documento
que muestra toda la información que el agente va recolectando de cada sitio web.

Características:
- ✅ Archivo .md que se actualiza en tiempo real
- ✅ Eventos WebSocket para mostrar en terminal de taskview
- ✅ Información completa de cada sitio visitado
- ✅ Timestamps y metadatos de cada recolección
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DocumentoEnVivo:
    """
    Gestor del documento en vivo que se actualiza con información recolectada.
    """
    
    def __init__(self, task_id: str, websocket_manager=None):
        self.task_id = task_id
        self.websocket_manager = websocket_manager
        self.documento_path = f"/tmp/documento_recoleccion_{task_id}.md"
        self.sitios_visitados = []
        self.informacion_total = []
        self.contador_actualizaciones = 0
        self._inicializar_documento()
        
    def _inicializar_documento(self):
        """Crea el documento inicial con header."""
        header = f"""# 📊 INFORMACIÓN RECOLECTADA EN TIEMPO REAL

**Tarea ID**: {self.task_id}  
**Iniciado**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Estado**: 🔄 Recolectando información...

---

## 🌐 PROGRESO DE NAVEGACIÓN WEB

"""
        
        try:
            with open(self.documento_path, 'w', encoding='utf-8') as f:
                f.write(header)
            
            self._emit_terminal_update(
                "📄 DOCUMENTO CREADO",
                f"Documento de recolección iniciado: {self.documento_path}",
                {"action": "documento_iniciado", "path": self.documento_path}
            )
            
            logger.info(f"📄 Documento en vivo inicializado: {self.documento_path}")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando documento: {e}")
    
    def agregar_sitio_visitado(self, url: str, titulo: str, contenido: str, 
                              metadatos: Dict[str, Any] = None):
        """
        Agrega información de un sitio visitado al documento en tiempo real.
        
        Args:
            url: URL del sitio visitado
            titulo: Título de la página
            contenido: Contenido completo extraído
            metadatos: Información adicional (tiempo de carga, método de extracción, etc.)
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        fecha_completa = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.contador_actualizaciones += 1
        
        # Preparar información del sitio
        sitio_info = {
            'numero': self.contador_actualizaciones,
            'url': url,
            'titulo': titulo,
            'contenido': contenido,
            'timestamp': fecha_completa,
            'metadatos': metadatos or {}
        }
        
        self.sitios_visitados.append(sitio_info)
        self.informacion_total.append(sitio_info)
        
        # Generar entrada markdown para este sitio
        entrada_md = f"""
### {self.contador_actualizaciones}. 🌐 {titulo}

**🔗 URL**: {url}  
**⏰ Recolectado**: {timestamp}  
**📊 Caracteres**: {len(contenido):,}  

"""
        
        # Agregar metadatos si existen
        if metadatos:
            entrada_md += "**📋 Metadatos**:\n"
            for key, value in metadatos.items():
                entrada_md += f"- **{key}**: {value}\n"
            entrada_md += "\n"
        
        # Agregar contenido completo
        entrada_md += f"""**📄 CONTENIDO COMPLETO EXTRAÍDO**:

```
{contenido}
```

---

"""
        
        # Escribir al archivo
        try:
            with open(self.documento_path, 'a', encoding='utf-8') as f:
                f.write(entrada_md)
            
            # Emitir evento WebSocket para terminal
            self._emit_terminal_update(
                f"📥 SITIO {self.contador_actualizaciones} RECOLECTADO",
                f"✅ {titulo[:50]}{'...' if len(titulo) > 50 else ''}\n🔗 {url}\n📊 {len(contenido):,} caracteres extraídos",
                {
                    "action": "sitio_recolectado",
                    "numero": self.contador_actualizaciones,
                    "url": url,
                    "titulo": titulo,
                    "contenido_preview": contenido[:200] + "..." if len(contenido) > 200 else contenido,
                    "contenido_completo": contenido,
                    "caracteres": len(contenido),
                    "timestamp": fecha_completa,
                    "metadatos": metadatos
                }
            )
            
            logger.info(f"📥 Sitio {self.contador_actualizaciones} agregado al documento: {titulo} ({len(contenido)} chars)")
            
        except Exception as e:
            logger.error(f"❌ Error escribiendo al documento: {e}")
    
    def agregar_analisis_paso(self, paso_numero: int, paso_titulo: str, 
                             analisis: str, insights: List[str] = None):
        """
        Agrega análisis de un paso específico al documento.
        
        Args:
            paso_numero: Número del paso
            paso_titulo: Título del paso
            analisis: Análisis completo del paso
            insights: Lista de insights encontrados
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        entrada_md = f"""
## 🧠 ANÁLISIS DEL PASO {paso_numero}: {paso_titulo}

**⏰ Completado**: {timestamp}  

**📊 ANÁLISIS COMPLETO**:

{analisis}

"""
        
        # Agregar insights si existen
        if insights:
            entrada_md += "**💡 INSIGHTS ENCONTRADOS**:\n\n"
            for i, insight in enumerate(insights, 1):
                entrada_md += f"{i}. {insight}\n\n"
        
        entrada_md += "---\n\n"
        
        # Escribir al archivo
        try:
            with open(self.documento_path, 'a', encoding='utf-8') as f:
                f.write(entrada_md)
            
            self._emit_terminal_update(
                f"🧠 ANÁLISIS PASO {paso_numero} COMPLETADO",
                f"✅ {paso_titulo}\n💡 {len(insights or [])} insights encontrados",
                {
                    "action": "analisis_completado",
                    "paso_numero": paso_numero,
                    "paso_titulo": paso_titulo,
                    "analisis": analisis,
                    "insights": insights or [],
                    "timestamp": timestamp
                }
            )
            
            logger.info(f"🧠 Análisis del paso {paso_numero} agregado al documento")
            
        except Exception as e:
            logger.error(f"❌ Error escribiendo análisis al documento: {e}")
    
    def actualizar_estado_navegacion(self, estado: str, detalles: str = ""):
        """
        Actualiza el estado de navegación en el documento.
        
        Args:
            estado: Estado actual (ej: "Navegando", "Extrayendo contenido", "Analizando")
            detalles: Detalles adicionales del estado
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Leer documento actual
        try:
            with open(self.documento_path, 'r', encoding='utf-8') as f:
                contenido_actual = f.read()
            
            # Actualizar la línea de estado
            if "**Estado**: 🔄 Recolectando información..." in contenido_actual:
                contenido_actualizado = contenido_actual.replace(
                    "**Estado**: 🔄 Recolectando información...",
                    f"**Estado**: 🔄 {estado} ({timestamp})"
                )
            else:
                # Si ya tiene un estado, actualizarlo
                import re
                pattern = r"\*\*Estado\*\*: 🔄 .+ \(\d{2}:\d{2}:\d{2}\)"
                contenido_actualizado = re.sub(
                    pattern,
                    f"**Estado**: 🔄 {estado} ({timestamp})",
                    contenido_actual
                )
            
            # Escribir documento actualizado
            with open(self.documento_path, 'w', encoding='utf-8') as f:
                f.write(contenido_actualizado)
            
            # Emitir evento al terminal
            self._emit_terminal_update(
                f"🔄 ESTADO ACTUALIZADO",
                f"{estado}\n{detalles}",
                {
                    "action": "estado_actualizado",
                    "estado": estado,
                    "detalles": detalles,
                    "timestamp": timestamp
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error actualizando estado: {e}")
    
    def finalizar_documento(self, resumen_final: str = ""):
        """
        Finaliza el documento con un resumen final.
        
        Args:
            resumen_final: Resumen final de toda la información recolectada
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        footer = f"""
## 📋 RESUMEN FINAL

**🏁 Completado**: {timestamp}  
**📊 Total sitios visitados**: {len(self.sitios_visitados)}  
**📄 Total caracteres recolectados**: {sum(len(sitio['contenido']) for sitio in self.sitios_visitados):,}  

{resumen_final}

---

*📄 Documento generado automáticamente por Mitosis en tiempo real*  
*🕐 Última actualización: {timestamp}*
"""
        
        try:
            # Actualizar estado final
            with open(self.documento_path, 'r', encoding='utf-8') as f:
                contenido_actual = f.read()
            
            # Cambiar estado a completado
            import re
            contenido_final = re.sub(
                r"\*\*Estado\*\*: 🔄 .+",
                f"**Estado**: ✅ Completado ({datetime.now().strftime('%H:%M:%S')})",
                contenido_actual
            )
            
            # Agregar footer
            contenido_final += footer
            
            with open(self.documento_path, 'w', encoding='utf-8') as f:
                f.write(contenido_final)
            
            self._emit_terminal_update(
                "✅ DOCUMENTO FINALIZADO",
                f"Recolección completada\n📊 {len(self.sitios_visitados)} sitios procesados\n📄 {sum(len(sitio['contenido']) for sitio in self.sitios_visitados):,} caracteres totales",
                {
                    "action": "documento_finalizado",
                    "total_sitios": len(self.sitios_visitados),
                    "total_caracteres": sum(len(sitio['contenido']) for sitio in self.sitios_visitados),
                    "path": self.documento_path,
                    "timestamp": timestamp
                }
            )
            
            logger.info(f"✅ Documento finalizado: {self.documento_path}")
            
        except Exception as e:
            logger.error(f"❌ Error finalizando documento: {e}")
    
    def obtener_contenido_completo(self) -> str:
        """Obtiene el contenido completo del documento actual."""
        try:
            with open(self.documento_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"❌ Error leyendo documento: {e}")
            return ""
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la recolección actual."""
        total_caracteres = sum(len(sitio['contenido']) for sitio in self.sitios_visitados)
        
        return {
            "sitios_visitados": len(self.sitios_visitados),
            "total_caracteres": total_caracteres,
            "actualizaciones": self.contador_actualizaciones,
            "documento_path": self.documento_path,
            "tamano_archivo_kb": self._obtener_tamano_archivo(),
            "ultimo_sitio": self.sitios_visitados[-1] if self.sitios_visitados else None
        }
    
    def _obtener_tamano_archivo(self) -> float:
        """Obtiene el tamaño del archivo en KB."""
        try:
            if os.path.exists(self.documento_path):
                size_bytes = os.path.getsize(self.documento_path)
                return round(size_bytes / 1024, 2)
            return 0.0
        except Exception:
            return 0.0
    
    def _emit_terminal_update(self, titulo: str, mensaje: str, data: Dict[str, Any]):
        """
        Emite actualización al terminal del taskview.
        
        Args:
            titulo: Título del evento
            mensaje: Mensaje detallado
            data: Datos adicionales del evento
        """
        if not self.websocket_manager:
            logger.warning("⚠️ WebSocket manager no disponible para terminal updates")
            return
        
        try:
            # Crear evento específico para el terminal del taskview
            event_data = {
                'type': 'documento_en_vivo',
                'titulo': titulo,
                'mensaje': mensaje,
                'data': data,
                'task_id': self.task_id,
                'timestamp': datetime.now().isoformat(),
                'documento_path': self.documento_path
            }
            
            # Enviar evento de terminal específico
            self.websocket_manager.emit_terminal_event(
                task_id=self.task_id,
                event_type='documento_recoleccion',
                data=event_data
            )
            
            # También enviar como log message para compatibilidad
            self.websocket_manager.send_log_message(
                task_id=self.task_id,
                level="info",
                message=f"📄 {titulo}: {mensaje}"
            )
            
            logger.debug(f"📡 Terminal update enviado: {titulo}")
            
        except Exception as e:
            logger.error(f"❌ Error enviando terminal update: {e}")

# Instancia global para el documento en vivo
_documentos_activos = {}

def obtener_documento_en_vivo(task_id: str, websocket_manager=None) -> DocumentoEnVivo:
    """
    Obtiene o crea una instancia del documento en vivo para una tarea.
    
    Args:
        task_id: ID de la tarea
        websocket_manager: Gestor de WebSocket para eventos en tiempo real
        
    Returns:
        Instancia de DocumentoEnVivo
    """
    global _documentos_activos
    
    if task_id not in _documentos_activos:
        _documentos_activos[task_id] = DocumentoEnVivo(task_id, websocket_manager)
    elif websocket_manager and not _documentos_activos[task_id].websocket_manager:
        # Actualizar websocket_manager si no estaba disponible antes
        _documentos_activos[task_id].websocket_manager = websocket_manager
    
    return _documentos_activos[task_id]

def limpiar_documento_tarea(task_id: str):
    """Limpia el documento de una tarea completada."""
    global _documentos_activos
    
    if task_id in _documentos_activos:
        documento = _documentos_activos[task_id]
        try:
            # Finalizar el documento antes de limpiar
            documento.finalizar_documento("Tarea completada y recursos liberados.")
        except Exception as e:
            logger.error(f"❌ Error finalizando documento antes de limpiar: {e}")
        
        # Remover de instancias activas
        del _documentos_activos[task_id]
        logger.info(f"🧹 Documento de tarea {task_id} limpiado de memoria")

def obtener_estadisticas_globales() -> Dict[str, Any]:
    """Obtiene estadísticas de todos los documentos activos."""
    global _documentos_activos
    
    return {
        "documentos_activos": len(_documentos_activos),
        "tareas_con_documentos": list(_documentos_activos.keys()),
        "total_sitios_recolectados": sum(
            len(doc.sitios_visitados) for doc in _documentos_activos.values()
        ),
        "timestamp": datetime.now().isoformat()
    }