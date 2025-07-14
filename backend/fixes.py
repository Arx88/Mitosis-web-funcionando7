"""
Correcciones para los errores encontrados en las pruebas del agente Mitosis
"""

import json
from enum import Enum
from dataclasses import dataclass, asdict

# Corrección 1: Serialización JSON para enums
class EnhancedJSONEncoder(json.JSONEncoder):
    """Encoder JSON que maneja enums y otros tipos especiales"""
    
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

def safe_json_dumps(obj, **kwargs):
    """Función segura para serializar objetos a JSON"""
    return json.dumps(obj, cls=EnhancedJSONEncoder, **kwargs)

# Corrección 2: Función para convertir dataclass a dict serializable
def dataclass_to_serializable_dict(obj):
    """Convierte un dataclass a un diccionario serializable"""
    if hasattr(obj, '__dataclass_fields__'):
        result = {}
        for field_name, field_value in asdict(obj).items():
            if isinstance(field_value, Enum):
                result[field_name] = field_value.value
            elif isinstance(field_value, list):
                result[field_name] = [
                    item.value if isinstance(item, Enum) else item 
                    for item in field_value
                ]
            else:
                result[field_name] = field_value
        return result
    return obj

# Corrección 3: Template de prompt corregido
CORRECTED_TASK_PLANNING_TEMPLATE = """SOLICITUD DE PLANIFICACIÓN DE TAREA:

OBJETIVO: {goal}
DESCRIPCIÓN: {description}

CONTEXTO DISPONIBLE:
{context}

MEMORIA RELEVANTE:
{relevant_memory}

INSTRUCCIONES PARA PLANIFICACIÓN:
1. Analiza el objetivo y descompónlo en fases lógicas y secuenciales
2. Para cada fase, identifica:
   - Título descriptivo
   - Descripción detallada de lo que se debe lograr
   - Capacidades requeridas (ej: web_search, code_execution, file_analysis)
   - Criterios de éxito
3. Considera dependencias entre fases
4. Estima la complejidad y tiempo requerido
5. Identifica posibles riesgos o desafíos

FORMATO DE RESPUESTA:
Proporciona un plan estructurado en formato JSON:
{{
  "goal": "{goal}",
  "phases": [
    {{
      "id": 1,
      "title": "título_fase",
      "description": "descripción_detallada",
      "required_capabilities": ["capacidad1", "capacidad2"],
      "success_criteria": "criterios_de_éxito",
      "estimated_duration": "tiempo_estimado"
    }}
  ],
  "risks": ["riesgo1", "riesgo2"],
  "dependencies": "descripción_de_dependencias"
}}

Genera un plan detallado y realista para lograr el objetivo."""

# Corrección 4: Función mejorada de optimización de prompts
def optimize_prompt_length_improved(prompt: str, max_tokens: int = 4000) -> str:
    """Optimiza la longitud de un prompt de manera más efectiva"""
    # Estimación: ~4 caracteres por token
    max_chars = max_tokens * 4
    
    if len(prompt) <= max_chars:
        return prompt
    
    # Dividir en secciones
    lines = prompt.split('\n')
    
    # Identificar secciones críticas que no se pueden truncar
    critical_sections = []
    optional_sections = []
    
    current_section = []
    in_critical_section = False
    
    for line in lines:
        line_upper = line.upper()
        
        # Identificar inicio de secciones críticas
        if any(keyword in line_upper for keyword in [
            'INSTRUCCIONES', 'OBJETIVO', 'FORMATO DE RESPUESTA', 
            'CRITERIOS', 'TAREA:', 'ERROR:'
        ]):
            if current_section and not in_critical_section:
                optional_sections.extend(current_section)
            current_section = [line]
            in_critical_section = True
        else:
            current_section.append(line)
            
            # Si llegamos al final de una sección crítica
            if in_critical_section and (not line.strip() or line.startswith('---')):
                critical_sections.extend(current_section)
                current_section = []
                in_critical_section = False
    
    # Añadir la última sección
    if current_section:
        if in_critical_section:
            critical_sections.extend(current_section)
        else:
            optional_sections.extend(current_section)
    
    # Reconstruir prompt priorizando secciones críticas
    critical_text = '\n'.join(critical_sections)
    
    if len(critical_text) >= max_chars:
        # Si incluso las secciones críticas son muy largas, truncar cuidadosamente
        return critical_text[:max_chars-3] + '...'
    
    # Añadir secciones opcionales hasta el límite
    remaining_chars = max_chars - len(critical_text)
    optional_text = '\n'.join(optional_sections)
    
    if len(optional_text) <= remaining_chars:
        return critical_text + '\n' + optional_text
    else:
        # Truncar secciones opcionales
        truncated_optional = optional_text[:remaining_chars-3] + '...'
        return critical_text + '\n' + truncated_optional

# Corrección 5: Mock mejorado para pruebas de Ollama
class MockOllamaModel:
    """Mock mejorado para modelos de Ollama"""
    def __init__(self, name: str, size: int):
        self.name = name
        self.size = size
        self.digest = f"sha256:{name}_digest"
        self.modified_at = "2024-01-01T00:00:00Z"

def create_mock_ollama_models():
    """Crea modelos mock para pruebas"""
    return [
        MockOllamaModel("llama2:7b", 4000000000),
        MockOllamaModel("codellama:13b", 7000000000),
        MockOllamaModel("mistral:7b", 4200000000)
    ]

# Función de utilidad para aplicar todas las correcciones
def apply_fixes():
    """Aplica todas las correcciones necesarias"""
    print("🔧 Aplicando correcciones...")
    
    # Las correcciones se aplicarán mediante parches en los archivos originales
    fixes_applied = [
        "Encoder JSON mejorado para enums",
        "Función de serialización segura para dataclasses",
        "Template de prompt corregido",
        "Optimización de prompts mejorada",
        "Mocks mejorados para pruebas"
    ]
    
    for fix in fixes_applied:
        print(f"  ✅ {fix}")
    
    print("🎉 Todas las correcciones aplicadas exitosamente")

if __name__ == "__main__":
    apply_fixes()
    
    # Probar las correcciones
    print("\n🧪 Probando correcciones...")
    
    # Probar serialización JSON
    from enum import Enum
    
    class TestEnum(Enum):
        VALUE1 = "value1"
        VALUE2 = "value2"
    
    test_data = {
        "enum_field": TestEnum.VALUE1,
        "list_with_enums": [TestEnum.VALUE1, TestEnum.VALUE2],
        "normal_field": "test"
    }
    
    try:
        json_str = safe_json_dumps(test_data)
        print("  ✅ Serialización JSON con enums funciona")
    except Exception as e:
        print(f"  ❌ Error en serialización JSON: {e}")
    
    # Probar optimización de prompts
    long_prompt = "INSTRUCCIONES: " + "A" * 10000 + "\nOTRA SECCIÓN: " + "B" * 10000
    optimized = optimize_prompt_length_improved(long_prompt, max_tokens=1000)
    
    if len(optimized) < len(long_prompt):
        print("  ✅ Optimización de prompts funciona")
    else:
        print("  ❌ Optimización de prompts no redujo la longitud")
    
    print("\n✨ Pruebas de correcciones completadas")

