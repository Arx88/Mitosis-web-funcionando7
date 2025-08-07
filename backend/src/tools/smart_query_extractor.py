"""
🧠 EXTRACTOR INTELIGENTE DE QUERIES PARA BÚSQUEDA WEB
Convierte títulos y descripciones de pasos en queries de búsqueda inteligentes y específicos

SOLUCIONA: El problema donde el agente busca "BUSCAR INFORMACIÓN" en lugar de keywords relevantes
"""

import re
from typing import List, Set
from datetime import datetime

def extract_smart_search_query(title: str, description: str, original_message: str = "") -> str:
    """
    🎯 EXTRACTOR PRINCIPAL - Convierte pasos en queries de búsqueda inteligentes
    
    Args:
        title: Título del paso (ej: "Buscar información sobre la selección argentina 2025")
        description: Descripción detallada del paso
        original_message: Mensaje original del usuario para contexto adicional
        
    Returns:
        Query optimizado para búsqueda web (ej: "selección argentina futbol 2025 jugadores")
    """
    
    # Combinar todo el texto disponible
    full_text = f"{title} {description} {original_message}".strip()
    
    # PASO 1: Limpiar texto de instrucciones genéricas
    cleaned_text = _remove_generic_instructions(full_text)
    
    # PASO 2: Extraer entidades importantes (nombres, lugares, fechas)
    entities = _extract_named_entities(cleaned_text)
    
    # PASO 3: Extraer keywords temáticos específicos
    thematic_keywords = _extract_thematic_keywords(cleaned_text)
    
    # PASO 4: Combinar y priorizar términos
    final_query = _build_optimized_query(entities, thematic_keywords, cleaned_text)
    
    # PASO 5: Validar y ajustar longitud
    final_query = _validate_and_optimize_length(final_query)
    
    return final_query

def _remove_generic_instructions(text: str) -> str:
    """🧹 Remover frases genéricas de instrucciones"""
    
    # Patrones a eliminar
    generic_patterns = [
        r'buscar información sobre\s*',
        r'investigar sobre\s*',
        r'analizar\s*',
        r'obtener datos sobre\s*',
        r'recopilar información de\s*',
        r'utilizar.*herramienta.*para\s*',
        r'web_search para\s*',
        r'búsqueda.*web.*sobre\s*',
        r'información actualizada sobre\s*',
        r'información específica sobre\s*',
        r'datos específicos de\s*',
        r'realizar.*búsqueda.*sobre\s*',
        r'encontrar información sobre\s*',
        r'conseguir datos de\s*'
    ]
    
    cleaned = text.lower()
    
    for pattern in generic_patterns:
        cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
    
    # Limpiar espacios múltiples
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

def _extract_named_entities(text: str) -> Set[str]:
    """🏷️ Extraer entidades importantes (nombres, lugares, organizaciones)"""
    
    entities = set()
    
    # PAÍSES Y NACIONALIDADES
    countries_and_nationalities = [
        'argentina', 'argentino', 'argentinos', 'argentina', 
        'brasil', 'brasileño', 'brazil',
        'españa', 'español', 'españoles', 'spain',
        'italia', 'italiano', 'italy',
        'francia', 'francés', 'france',
        'alemania', 'alemán', 'germany',
        'inglaterra', 'inglés', 'england',
        'portugal', 'portugués',
        'chile', 'chileno',
        'uruguay', 'uruguayo',
        'colombia', 'colombiano',
        'méxico', 'mexicano', 'mexico',
        'perú', 'peruano',
        'ecuador', 'ecuatoriano'
    ]
    
    for country in countries_and_nationalities:
        if country in text.lower():
            entities.add(country)
    
    # DEPORTES Y TÉRMINOS DEPORTIVOS
    sports_terms = [
        'fútbol', 'futbol', 'soccer', 'football',
        'selección', 'seleccion', 'nacional', 'equipo',
        'mundial', 'copa', 'américa', 'champions',
        'liga', 'torneo', 'campeonato',
        'jugador', 'jugadores', 'player', 'players',
        'entrenador', 'técnico', 'coach',
        'estadio', 'cancha'
    ]
    
    for term in sports_terms:
        if term in text.lower():
            entities.add(term)
    
    # AÑOS Y FECHAS
    years = re.findall(r'\b(20\d{2})\b', text)
    for year in years:
        entities.add(year)
    
    # NOMBRES PROPIOS (empiezan con mayúscula)
    # Buscar secuencias de palabras que empiezan con mayúscula
    proper_nouns = re.findall(r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*\b', text)
    for noun in proper_nouns:
        if len(noun) > 3 and not noun.lower().startswith(('buscar', 'información', 'sobre')):
            entities.add(noun.lower())
    
    # TÉRMINOS TÉCNICOS ESPECÍFICOS
    technical_terms = [
        'inteligencia artificial', 'ia', 'ai', 'machine learning',
        'blockchain', 'bitcoin', 'ethereum', 'crypto',
        'covid', 'coronavirus', 'pandemic', 'vaccine',
        'climate', 'clima', 'environment', 'sostenible',
        'economy', 'economía', 'inflation', 'inflación',
        'politics', 'política', 'election', 'elección',
        'technology', 'tecnología', 'innovation', 'innovación'
    ]
    
    for term in technical_terms:
        if term in text.lower():
            entities.add(term)
    
    return entities

def _extract_thematic_keywords(text: str) -> Set[str]:
    """🎯 Extraer keywords temáticos específicos del dominio"""
    
    keywords = set()
    text_lower = text.lower()
    
    # PATRONES TEMÁTICOS ESPECÍFICOS
    thematic_patterns = {
        # Deportes
        'deportes': ['gol', 'goles', 'partido', 'partidos', 'resultado', 'resultados',
                    'clasificación', 'tabla', 'posiciones', 'fixture',
                    'transferencia', 'fichaje', 'lesión', 'suspendido'],
        
        # Política y gobierno
        'politica': ['gobierno', 'presidente', 'ministro', 'congreso', 'senado',
                    'diputado', 'ley', 'decreto', 'reforma', 'política',
                    'elección', 'candidato', 'partido político'],
        
        # Economía
        'economia': ['precio', 'precios', 'inflación', 'dólar', 'peso',
                    'mercado', 'inversión', 'empresa', 'negocio',
                    'trabajo', 'empleo', 'salario', 'sueldo'],
        
        # Tecnología
        'tecnologia': ['software', 'aplicación', 'app', 'sistema',
                      'internet', 'digital', 'online', 'plataforma',
                      'algoritmo', 'datos', 'base de datos'],
        
        # Salud
        'salud': ['médico', 'hospital', 'tratamiento', 'medicina',
                 'síntoma', 'enfermedad', 'vacuna', 'virus'],
        
        # Educación
        'educacion': ['universidad', 'estudiante', 'profesor', 'curso',
                     'carrera', 'título', 'educación', 'aprendizaje']
    }
    
    # Buscar keywords temáticos en el texto
    for theme, theme_keywords in thematic_patterns.items():
        for keyword in theme_keywords:
            if keyword in text_lower:
                keywords.add(keyword)
    
    # BUSCAR VERBOS DE ACCIÓN RELEVANTES
    action_verbs = ['comprar', 'vender', 'analizar', 'comparar', 'estudiar', 
                   'desarrollar', 'implementar', 'mejorar', 'optimizar',
                   'crear', 'diseñar', 'construir', 'establecer']
    
    for verb in action_verbs:
        if verb in text_lower:
            keywords.add(verb)
    
    return keywords

def _build_optimized_query(entities: Set[str], keywords: Set[str], original_text: str) -> str:
    """🔨 Construir query optimizado combinando entidades y keywords"""
    
    # Combinar todos los términos
    all_terms = list(entities) + list(keywords)
    
    # Eliminar stop words
    stop_words = {
        'de', 'del', 'la', 'el', 'en', 'con', 'para', 'por', 'sobre',
        'un', 'una', 'y', 'o', 'que', 'se', 'es', 'son', 'está', 'están',
        'fue', 'ser', 'han', 'ha', 'su', 'sus', 'le', 'les', 'lo', 'los',
        'las', 'al', 'pero', 'como', 'más', 'muy', 'puede', 'pueden',
        'desde', 'hasta', 'entre', 'durante', 'antes', 'después',
        'información', 'datos', 'buscar', 'obtener', 'encontrar'
    }
    
    filtered_terms = []
    for term in all_terms:
        if term and len(term) > 2 and term.lower() not in stop_words:
            filtered_terms.append(term)
    
    # Priorizar términos más específicos
    prioritized_terms = []
    
    # PRIORIDAD 1: Nombres propios y entidades específicas
    for term in filtered_terms:
        if any(char.isupper() for char in term) or re.match(r'20\d{2}', term):
            prioritized_terms.append(term)
    
    # PRIORIDAD 2: Términos temáticos relevantes
    for term in filtered_terms:
        if term not in prioritized_terms and len(term) > 4:
            prioritized_terms.append(term)
    
    # PRIORIDAD 3: Términos generales pero útiles
    for term in filtered_terms:
        if term not in prioritized_terms:
            prioritized_terms.append(term)
    
    # Construir query final
    if prioritized_terms:
        # Tomar los términos más importantes (máximo 6)
        final_terms = prioritized_terms[:6]
        return ' '.join(final_terms)
    else:
        # Fallback: extraer palabras significativas del texto original
        words = re.findall(r'\b[a-záéíóúñA-ZÁÉÍÓÚÑ]{4,}\b', original_text)
        significant_words = [w for w in words if w.lower() not in stop_words][:4]
        return ' '.join(significant_words) if significant_words else "noticias actualidad 2025"

def _validate_and_optimize_length(query: str) -> str:
    """✅ Validar y optimizar la longitud del query final"""
    
    # Limpiar espacios múltiples
    query = re.sub(r'\s+', ' ', query).strip()
    
    # Si el query es muy corto, agregar contexto temporal
    if len(query) < 10:
        current_year = datetime.now().year
        query = f"{query} {current_year}"
    
    # Si es muy largo, tomar solo las primeras palabras más importantes
    words = query.split()
    if len(words) > 6:
        query = ' '.join(words[:6])
    
    # Si está vacío o muy genérico, usar fallback
    generic_terms = ['información', 'datos', 'buscar', 'sobre']
    if not query or all(term in generic_terms for term in query.split()):
        query = f"noticias actualidad {datetime.now().year}"
    
    return query

# FUNCIÓN DE UTILIDAD PARA TESTING
def test_query_extraction():
    """🧪 Función de testing para verificar la extracción de queries"""
    
    test_cases = [
        {
            'title': 'Buscar información sobre la selección argentina 2025',
            'description': 'Necesito datos actualizados sobre los jugadores convocados',
            'expected_keywords': ['selección', 'argentina', '2025', 'jugadores']
        },
        {
            'title': 'Investigar sobre inteligencia artificial',
            'description': 'Obtener información sobre los últimos avances en IA',
            'expected_keywords': ['inteligencia', 'artificial', 'ia', 'avances']
        },
        {
            'title': 'Analizar la inflación en Argentina 2024',
            'description': 'Datos económicos sobre el impacto de la inflación',
            'expected_keywords': ['inflación', 'argentina', '2024', 'económicos']
        }
    ]
    
    print("🧪 TESTING SMART QUERY EXTRACTION")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        title = test_case['title']
        description = test_case['description']
        
        # Extraer query
        smart_query = extract_smart_search_query(title, description)
        
        print(f"\nTest {i}:")
        print(f"  Input Title: {title}")
        print(f"  Input Description: {description}")
        print(f"  Smart Query: '{smart_query}'")
        print(f"  Expected Keywords: {test_case['expected_keywords']}")
        
        # Verificar si contiene keywords esperados
        found_keywords = []
        for keyword in test_case['expected_keywords']:
            if keyword.lower() in smart_query.lower():
                found_keywords.append(keyword)
        
        print(f"  Found Keywords: {found_keywords}")
        print(f"  Match Score: {len(found_keywords)}/{len(test_case['expected_keywords'])}")

if __name__ == "__main__":
    test_query_extraction()