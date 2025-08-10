"""
🧠 GENERADOR INTELIGENTE DE KEYWORDS - SOLUCIÓN COMPLETA V2.0
Reemplaza la lógica destructiva de _extract_clean_keywords_static()
con un sistema inteligente que preserva el contexto esencial

RESUELVE: 
- Keywords inútiles como "REALIZA INFORME"
- Pérdida de contexto importante
- Búsquedas genéricas sin resultados

IMPLEMENTA:
- Preservación de entidades nombradas (personas, lugares)
- Extracción inteligente de conceptos principales
- Múltiples variantes de búsqueda específicas
- Contexto temporal y geográfico automático
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class IntelligentKeywordGenerator:
    """🎯 Generador inteligente de keywords y términos de búsqueda"""
    
    def __init__(self):
        # Entidades importantes que SIEMPRE deben preservarse
        self.preserve_entities = {
            'personas': ['milei', 'javier', 'biden', 'musk', 'elon', 'trump', 'cristina', 'massa', 
                        'alberto', 'fernández', 'macri', 'mauricio', 'cristiano', 'messi', 'lionel'],
            'lugares': ['argentina', 'buenos', 'aires', 'córdoba', 'mendoza', 'españa', 'madrid', 
                       'barcelona', 'valencia', 'méxico', 'colombia', 'chile', 'usa', 'eeuu'],
            'organizaciones': ['fifa', 'onu', 'oea', 'mercosur', 'gobierno', 'congress', 'senate'],
            'tecnologia': ['inteligencia', 'artificial', 'blockchain', 'bitcoin', 'crypto', 'tesla', 
                          'apple', 'google', 'microsoft', 'meta', 'openai', 'chatgpt'],
            'conceptos': ['economía', 'política', 'inflación', 'dólar', 'peso', 'elecciones', 
                         'democracia', 'libertad', 'socialismo', 'capitalismo', 'crisis'],
            'temporal': ['2024', '2025', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                        'actual', 'reciente', 'nuevo', 'última', 'último'],
            'musica': ['arctic', 'monkeys', 'banda', 'música', 'rock', 'discografía', 'álbum', 
                      'canción', 'concierto', 'gira', 'festival'],
            'anime_manga': ['attack', 'titan', 'shingeki', 'kyojin', 'eren', 'mikasa', 'armin', 'levi', 
                           'anime', 'manga', 'naruto', 'one', 'piece', 'dragon', 'ball', 'studio', 
                           'ghibli', 'miyazaki', 'otaku', 'cosplay'],
            'entretenimiento': ['netflix', 'disney', 'marvel', 'dc', 'comics', 'superhero', 'movie', 
                               'film', 'serie', 'temporada', 'episodio', 'actor', 'actress', 'director']
        }
        
        # Palabras meta que deben eliminarse COMPLETAMENTE
        self.meta_words = {
            'instrucciones': ['buscar', 'información', 'sobre', 'acerca', 'utilizar', 'herramienta', 
                             'web_search', 'realizar', 'generar', 'crear', 'obtener', 'necesario',
                             'completar', 'específico', 'datos', 'análisis', 'informe', 'recopilar',
                             'desarrollar', 'estrategia', 'búsqueda', 'actual', 'actuales', 'web'],
            'conectores': ['para', 'con', 'por', 'desde', 'hasta', 'durante', 'mediante', 'según',
                          'ante', 'bajo', 'contra', 'entre', 'hacia', 'según', 'sin', 'tras'],
            'articulos': ['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas'],
            'pronombres': ['que', 'cual', 'quien', 'donde', 'cuando', 'como', 'este', 'esta', 'ese', 'esa']
        }
        
        # Patrones problemáticos que indican queries mal formados
        self.problematic_patterns = [
            r'\brealiza\s+informe\b',
            r'\butilizar\s+herramienta\b', 
            r'\bweb_search\s+para\b',
            r'\binformación\s+específica\s+sobre\b',
            r'\bgenera\s+(un|una)\s+(análisis|informe|reporte)\b',
            r'\brecopilar\s+datos\s+de\s+mercado\b',
            r'\brealizar\s+una\s+búsqueda\s+web\b',
            r'\bdesarrollar\s+una\s+estrategia\b',
            r'\bobtener\s+datos\s+actuales\b'
        ]
    
    def get_intelligent_keywords(self, query_text: str) -> str:
        """🎯 FUNCIÓN PRINCIPAL: Generar keywords inteligentes"""
        
        if not query_text or len(query_text.strip()) < 3:
            return "información actualizada"
        
        print(f"🧠 INTELLIGENT GENERATOR INPUT: '{query_text}'")
        
        # 1. Detectar si es query problemático
        if self._is_problematic_query(query_text):
            print("⚠️ PROBLEMATIC QUERY detectado - aplicando corrección especial")
            return self._fix_problematic_query(query_text)
        
        # 2. Extraer entidades importantes (nombres propios, conceptos clave)
        entities = self._extract_important_entities(query_text)
        
        # 3. Extraer conceptos principales 
        concepts = self._extract_main_concepts(query_text)
        
        # 4. Combinar y optimizar
        result = self._combine_and_optimize(entities, concepts, query_text)
        
        print(f"✅ INTELLIGENT RESULT: '{query_text}' → '{result}'")
        return result
    
    def get_multiple_search_variants(self, query_text: str, count: int = 3) -> List[str]:
        """🔄 Generar múltiples variantes de búsqueda para diversidad"""
        
        base_keywords = self.get_intelligent_keywords(query_text)
        variants = [base_keywords]
        
        # Variante 1: Con contexto temporal
        if '2025' not in base_keywords and '2024' not in base_keywords:
            variants.append(f"{base_keywords} 2025 actualidad")
        
        # Variante 2: Con especificidad geográfica si aplicable
        if any(lugar in query_text.lower() for lugar in self.preserve_entities['lugares']):
            variants.append(f"{base_keywords} noticias recientes")
        else:
            variants.append(f"{base_keywords} información completa")
        
        # Variante 3: Con enfoque específico
        if any(persona in query_text.lower() for persona in self.preserve_entities['personas']):
            variants.append(f"{base_keywords} biografía trayectoria")
        elif any(tech in query_text.lower() for tech in self.preserve_entities['tecnologia']):
            variants.append(f"{base_keywords} definición características")
        else:
            variants.append(f"{base_keywords} guía completa")
        
        return variants[:count]
    
    def _is_problematic_query(self, query_text: str) -> bool:
        """🚨 Detectar queries problemáticos que generan keywords inútiles"""
        
        query_lower = query_text.lower()
        
        # Verificar patrones problemáticos conocidos
        for pattern in self.problematic_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Verificar si tiene muchas palabras meta vs. pocas entidades
        meta_count = sum(1 for category in self.meta_words.values() 
                        for word in category if word in query_lower)
        
        entity_count = sum(1 for category in self.preserve_entities.values()
                          for entity in category if entity in query_lower)
        
        # Si hay más de 3 palabras meta y menos de 1 entidad, es problemático
        return meta_count > 3 and entity_count < 1
    
    def _fix_problematic_query(self, query_text: str) -> str:
        """🔧 Reparar queries problemáticos extrayendo el tema real"""
        
        query_lower = query_text.lower()
        
        # Buscar patrones específicos de tema
        theme_patterns = [
            r'sobre\s+"([^"]+)"',  # sobre "tema"
            r'sobre\s+([a-záéíóúñ\s]+?)(?:\s+en\s|\s+con\s|$)',  # sobre tema
            r'información.*?([a-záéíóúñ]{4,}(?:\s+[a-záéíóúñ]{4,})*)',  # información tema
            r'análisis.*?([a-záéíóúñ]{4,}(?:\s+[a-záéíóúñ]{4,})*)',  # análisis tema
            r'mercado\s+objetivo.*?(redes\s+sociales|social\s+media|marketing)',  # mercado + marketing
            r'tendencias\s+de\s+(redes\s+sociales|social\s+media|marketing)',  # tendencias marketing
            r'estrategia\s+de\s+(marketing|redes\s+sociales|social\s+media)',  # estrategia marketing
            r'comportamiento\s+de\s+la\s+audiencia',  # comportamiento audiencia
        ]
        
        for pattern in theme_patterns:
            match = re.search(pattern, query_text, re.IGNORECASE)
            if match:
                theme = match.group(1).strip()
                print(f"🔧 TEMA EXTRAÍDO DE QUERY PROBLEMÁTICO: '{theme}'")
                return self._clean_and_enhance_theme(theme)
        
        # Buscar conceptos específicos del contexto de marketing
        marketing_concepts = ['marketing', 'redes sociales', 'social media', 'audiencia', 
                             'mercado', 'tendencias', 'comportamiento', 'digital', 'contenido']
        
        found_concepts = []
        for concept in marketing_concepts:
            if concept in query_lower:
                found_concepts.append(concept)
        
        if found_concepts:
            result = ' '.join(found_concepts[:3]) + ' 2025'
            print(f"🔧 CONCEPTOS MARKETING EXTRAÍDOS: '{result}'")
            return result
        
        # Si no se encuentra patrón, usar extracción de entidades de emergencia
        words = re.findall(r'\b[a-záéíóúñA-ZÁÉÍÓÚÑ]{4,}\b', query_text)
        significant_words = []
        
        for word in words:
            word_lower = word.lower()
            # Incluir si es entidad importante o no es palabra meta
            if (any(word_lower in entities for entities in self.preserve_entities.values()) or
                not any(word_lower in metas for metas in self.meta_words.values())):
                significant_words.append(word_lower)
        
        if significant_words:
            result = ' '.join(significant_words[:4])
            print(f"🔧 EMERGENCIA - Palabras significativas extraídas: '{result}'")
            return result
        
        # Último recurso
        return "marketing digital redes sociales 2025"
    
    def _clean_and_enhance_theme(self, theme: str) -> str:
        """✨ Limpiar y mejorar tema extraído"""
        
        # Remover comillas y espacios extra
        clean_theme = re.sub(r'["\']', '', theme).strip()
        
        # Si el tema es muy corto, agregarlo contexto relevante
        if len(clean_theme.split()) < 2:
            if any(keyword in clean_theme.lower() for keyword in ['marketing', 'social', 'redes']):
                return f"{clean_theme} estrategias marketing digital 2025"
            elif 'inteligencia' in clean_theme.lower():
                return f"{clean_theme} tendencias aplicaciones 2025"
            else:
                return f"{clean_theme} información completa actualizada 2025"
        
        # Si ya es un buen tema, agregar contexto temporal
        if '2024' not in clean_theme and '2025' not in clean_theme:
            return f"{clean_theme} 2025"
        
        return clean_theme
    
    def _extract_important_entities(self, query_text: str) -> List[str]:
        """🏷️ Extraer entidades importantes (nombres propios, conceptos clave)"""
        
        entities = []
        query_lower = query_text.lower()
        
        # Buscar todas las entidades de alta prioridad
        for category, entity_list in self.preserve_entities.items():
            for entity in entity_list:
                if entity in query_lower:
                    entities.append(entity)
        
        # Buscar nombres propios adicionales (Capitalizados)
        proper_nouns = re.findall(r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*\b', query_text)
        for noun in proper_nouns:
            if len(noun) > 3:
                entities.append(noun.lower())
        
        # Remover duplicados manteniendo orden
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity not in seen:
                seen.add(entity)
                unique_entities.append(entity)
        
        return unique_entities[:6]  # Máximo 6 entidades más importantes
    
    def _extract_main_concepts(self, query_text: str) -> List[str]:
        """💡 Extraer conceptos principales del texto"""
        
        concepts = []
        
        # Extraer palabras significativas (4+ caracteres)
        words = re.findall(r'\b[a-záéíóúñA-ZÁÉÍÓÚÑ]{4,}\b', query_text)
        
        for word in words:
            word_lower = word.lower()
            
            # Incluir si NO es palabra meta
            is_meta = any(word_lower in meta_category for meta_category in self.meta_words.values())
            
            if not is_meta and len(word_lower) >= 4:
                concepts.append(word_lower)
        
        return concepts[:8]  # Máximo 8 conceptos
    
    def _combine_and_optimize(self, entities: List[str], concepts: List[str], original_query: str) -> str:
        """⚡ Combinar y optimizar entidades y conceptos"""
        
        # 1. Priorizar entidades (son más importantes)
        important_terms = entities[:3]  # Top 3 entidades
        
        # 2. Agregar conceptos que no sean repetitivos
        for concept in concepts:
            if (concept not in important_terms and 
                len(important_terms) < 6 and
                not any(concept in term for term in important_terms)):  # Evitar redundancia
                important_terms.append(concept)
        
        # 3. Si muy pocos términos, agregar contexto inteligente
        if len(important_terms) < 2:
            # Agregar contexto basado en tipo de consulta
            if any(persona in original_query.lower() for persona in self.preserve_entities['personas']):
                important_terms.append('biografía')
            elif any(tech in original_query.lower() for tech in self.preserve_entities['tecnologia']):
                important_terms.append('información')
            else:
                important_terms.append('actualidad')
        
        # 4. Construir resultado final
        result = ' '.join(important_terms[:5])  # Máximo 5 términos
        
        # 5. Agregar año si no está presente y el resultado es corto
        if ('2024' not in result and '2025' not in result and 
            len(result.split()) < 4):
            result += ' 2025'
        
        return result

# Funciones públicas para usar desde unified_web_search_tool.py
def get_intelligent_keywords(query_text: str) -> str:
    """🎯 Función principal para generar keywords inteligentes"""
    generator = IntelligentKeywordGenerator()
    return generator.get_intelligent_keywords(query_text)

def get_multiple_search_variants(query_text: str, count: int = 3) -> List[str]:
    """🔄 Generar múltiples variantes de búsqueda"""
    generator = IntelligentKeywordGenerator()
    return generator.get_multiple_search_variants(query_text, count)

# Testing directo si se ejecuta como script
if __name__ == "__main__":
    # Tests de casos problemáticos reportados por el usuario
    test_cases = [
        "Buscar información sobre 'Javier Milei' en bing y explorar los primeros resultados",
        "realizar análisis de datos específicos sobre inteligencia artificial",  
        "genera informe sobre Arctic Monkeys discografía",
        "utilizar herramienta web_search para obtener datos económicos Argentina",
        "información específica sobre inflación Argentina 2024"
    ]
    
    print("🧪 TESTING INTELLIGENT KEYWORD GENERATOR")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🔍 TEST {i}: {test}")
        result = get_intelligent_keywords(test)
        print(f"✅ RESULT: {result}")
        
        variants = get_multiple_search_variants(test, 2)
        print(f"🔄 VARIANTS: {variants}")
        print("-" * 40)

# Instancia global para usar en unified_web_search_tool.py
intelligent_keyword_generator = IntelligentKeywordGenerator()

def get_intelligent_keywords(query: str, num_variants: int = 1) -> str:
    """
    🎯 FUNCIÓN PRINCIPAL PARA REEMPLAZAR LAS FUNCIONES PROBLEMÁTICAS
    
    Args:
        query: Query original del usuario
        num_variants: Número de variantes (por defecto 1)
        
    Returns:
        str: Keywords inteligentes optimizados
    """
    if num_variants == 1:
        return intelligent_keyword_generator.get_intelligent_keywords(query)
    else:
        variants = intelligent_keyword_generator.get_multiple_search_variants(query, num_variants)
        return variants[0] if variants else "información actualizada"

def get_multiple_search_variants(query: str, num_variants: int = 3) -> List[str]:
    """
    📊 GENERAR MÚLTIPLES VARIANTES PARA BÚSQUEDAS DIVERSIFICADAS
    
    Args:
        query: Query original del usuario  
        num_variants: Número de variantes a generar
        
    Returns:
        List[str]: Lista de keywords variantes
    """
    return intelligent_keyword_generator.get_multiple_search_variants(query, num_variants)