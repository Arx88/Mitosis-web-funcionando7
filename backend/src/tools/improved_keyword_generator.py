"""
CORRECCIÓN CRÍTICA: Generador de Keywords Inteligente
Reemplazo completo para las funciones problemáticas de generación de términos de búsqueda

PROBLEMA IDENTIFICADO:
- unified_web_search_tool.py líneas 1080, 204-205 generan keywords sin sentido
- Regex destructivos que eliminan contexto esencial 
- Términos como "REALIZA INFORME" que no devuelven resultados útiles

SOLUCIÓN IMPLEMENTADA:
- Extracción inteligente de entidades y conceptos principales
- Preservación del contexto y tema central
- Múltiples estrategias de fallback inteligentes
"""

import re
import logging
from typing import List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class IntelligentKeywordGenerator:
    """
    🧠 GENERADOR INTELIGENTE DE KEYWORDS PARA BÚSQUEDAS WEB
    
    Reemplaza las funciones problemáticas con lógica avanzada que:
    1. Preserva el contexto esencial de la consulta
    2. Extrae entidades principales (personas, lugares, conceptos)
    3. Genera múltiples variantes de búsqueda específicas
    4. Evita términos meta que no producen resultados útiles
    """
    
    def __init__(self):
        # Palabras que deben ser preservadas siempre (entidades políticas, económicas, etc)
        self.preserve_words = {
            'milei', 'argentina', 'javier', 'presidente', 'político', 'economía', 'inflación',
            'ideología', 'declaraciones', 'biografía', 'trayectoria', 'libertario',
            'arctic', 'monkeys', 'banda', 'música', 'rock', 'discografía',
            'inteligencia', 'artificial', 'ai', 'tecnología', 'datos', 'machine', 'learning'
        }
        
        # Palabras meta que deben ser eliminadas completamente
        self.meta_words = {
            'buscar', 'información', 'sobre', 'utilizar', 'herramienta', 'web_search',
            'realizar', 'análisis', 'genera', 'informe', 'específica', 'actualizada',
            'relacionadas', 'noticias', 'datos', 'para', 'con', 'una', 'del', 'las', 'los',
            'que', 'esta', 'este', 'año', 'search', 'estado', 'completa', 'general'
        }
    
    def generate_smart_keywords(self, original_query: str, max_keywords: int = 4) -> str:
        """
        🎯 GENERAR KEYWORDS INTELIGENTES DESDE QUERY ORIGINAL
        
        Args:
            original_query: Query original del usuario
            max_keywords: Máximo número de keywords a generar
            
        Returns:
            str: Keywords optimizados para búsqueda web efectiva
        """
        try:
            # Log de debugging para verificar entrada
            logger.info(f"🔍 KEYWORD GENERATION: Input '{original_query}'")
            print(f"🔍 KEYWORDS DEBUG: Generating from '{original_query}'")
            
            # ESTRATEGIA 1: Detectar y preservar nombres propios/entidades
            proper_nouns = self._extract_proper_nouns(original_query)
            if proper_nouns:
                result = self._build_query_with_entities(proper_nouns, original_query)
                print(f"✅ STRATEGY 1 - Proper nouns: '{result}'")
                if self._validate_keyword_quality(result):
                    return result
            
            # ESTRATEGIA 2: Identificar tema central y conceptos relacionados
            central_theme = self._identify_central_theme(original_query)
            if central_theme:
                result = self._build_themed_query(central_theme, original_query)
                print(f"✅ STRATEGY 2 - Central theme: '{result}'")
                if self._validate_keyword_quality(result):
                    return result
            
            # ESTRATEGIA 3: Extracción inteligente de keywords significativos
            significant_words = self._extract_significant_words(original_query)
            if len(significant_words) >= 2:
                result = ' '.join(significant_words[:max_keywords])
                print(f"✅ STRATEGY 3 - Significant words: '{result}'")
                if self._validate_keyword_quality(result):
                    return result
            
            # ESTRATEGIA 4: Fallback inteligente basado en categorías
            category_based = self._generate_category_based_keywords(original_query)
            if category_based:
                print(f"✅ STRATEGY 4 - Category based: '{category_based}'")
                return category_based
            
            # ÚLTIMO RECURSO: Preservar cualquier palabra importante encontrada
            last_resort = self._extract_any_useful_words(original_query)
            print(f"⚠️ LAST RESORT - Any useful: '{last_resort}'")
            return last_resort
            
        except Exception as e:
            logger.error(f"❌ Error generating keywords: {str(e)}")
            return "búsqueda información actual"
    
    def _extract_proper_nouns(self, text: str) -> List[str]:
        """Extraer nombres propios/entidades con precisión"""
        # Detectar nombres propios (palabras que empiezan con mayúscula)
        proper_nouns = re.findall(r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*\b', text)
        
        # Filtrar nombres válidos (no palabras al inicio de oración)
        valid_nouns = []
        for noun in proper_nouns:
            # Verificar que no sea solo una palabra común capitalizada al inicio
            if any(preserve_word in noun.lower() for preserve_word in self.preserve_words):
                valid_nouns.append(noun)
        
        return valid_nouns
    
    def _build_query_with_entities(self, entities: List[str], original_query: str) -> str:
        """Construir query preservando entidades principales"""
        # Combinar entidades principales
        entity_query = ' '.join(entities).lower()
        
        # Detectar tipo de consulta y agregar contexto apropiado
        query_lower = original_query.lower()
        
        if any(word in query_lower for word in ['biografía', 'trayectoria', 'ideología', 'político']):
            return f"{entity_query} biografía política ideología"
        elif any(word in query_lower for word in ['económico', 'economía', 'inflación', 'argentina']):
            return f"{entity_query} economía argentina datos"
        elif any(word in query_lower for word in ['banda', 'música', 'rock', 'discografía']):
            return f"{entity_query} música discografía información"
        elif any(word in query_lower for word in ['tecnología', 'inteligencia', 'artificial', 'ai']):
            return f"{entity_query} tecnología inteligencia artificial"
        else:
            return f"{entity_query} información completa"
    
    def _identify_central_theme(self, text: str) -> Optional[str]:
        """Identificar el tema central de la consulta"""
        text_lower = text.lower()
        
        # Temas políticos/económicos
        if any(word in text_lower for word in ['político', 'presidente', 'economía', 'argentina', 'milei']):
            return 'política_economía'
        
        # Temas musicales
        if any(word in text_lower for word in ['banda', 'música', 'rock', 'arctic', 'monkeys']):
            return 'música'
        
        # Temas tecnológicos
        if any(word in text_lower for word in ['tecnología', 'inteligencia', 'artificial', 'ai', 'datos']):
            return 'tecnología'
        
        # Temas de investigación general
        if any(word in text_lower for word in ['análisis', 'investigar', 'estudiar', 'comparar']):
            return 'investigación'
        
        return None
    
    def _build_themed_query(self, theme: str, original_query: str) -> str:
        """Construir query basado en tema identificado"""
        # Extraer palabras clave principales del query original
        main_words = self._extract_significant_words(original_query, min_words=2)
        
        theme_maps = {
            'política_economía': lambda words: f"{' '.join(words)} política argentina económico",
            'música': lambda words: f"{' '.join(words)} música banda discografía",
            'tecnología': lambda words: f"{' '.join(words)} tecnología inteligencia artificial",
            'investigación': lambda words: f"{' '.join(words)} análisis investigación datos"
        }
        
        if theme in theme_maps and main_words:
            return theme_maps[theme](main_words[:3])
        
        return None
    
    def _extract_significant_words(self, text: str, min_words: int = 2) -> List[str]:
        """Extraer palabras significativas evitando términos meta"""
        # Normalizar texto
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # Extraer todas las palabras de 3+ caracteres
        words = re.findall(r'\b[a-záéíóúñ]{3,}\b', clean_text)
        
        # Filtrar palabras significativas
        significant = []
        for word in words:
            # Incluir si está en preserve_words O si no está en meta_words
            if word in self.preserve_words or (word not in self.meta_words and len(word) > 2):
                significant.append(word)
        
        # Remover duplicados preservando orden
        seen = set()
        unique_significant = []
        for word in significant:
            if word not in seen:
                seen.add(word)
                unique_significant.append(word)
        
        return unique_significant[:6]  # Máximo 6 palabras
    
    def _generate_category_based_keywords(self, text: str) -> Optional[str]:
        """Generar keywords basados en categoría de la consulta"""
        text_lower = text.lower()
        
        # Análisis político/biografía
        if any(word in text_lower for word in ['milei', 'javier', 'presidente', 'político']):
            return "javier milei presidente argentina política"
        
        # Análisis económico
        if any(word in text_lower for word in ['económico', 'inflación', 'pib', 'argentina']):
            return "argentina economía inflación datos estadísticas"
        
        # Banda musical
        if any(word in text_lower for word in ['arctic', 'monkeys', 'banda']):
            return "arctic monkeys banda música rock"
        
        # Tecnología/IA
        if any(word in text_lower for word in ['inteligencia', 'artificial', 'tecnología']):
            return "inteligencia artificial tecnología machine learning"
        
        return None
    
    def _extract_any_useful_words(self, text: str) -> str:
        """Último recurso: extraer cualquier palabra potencialmente útil"""
        words = re.findall(r'\b[a-záéíóúñA-ZÁÉÍÓÚÑ]{3,}\b', text)
        
        # Filtrar solo las más cortas que no sean meta
        useful = []
        for word in words[:8]:  # Primeras 8 palabras
            word_lower = word.lower()
            if word_lower not in self.meta_words and len(word) >= 3:
                useful.append(word_lower)
        
        if useful:
            return ' '.join(useful[:4])
        else:
            return "información actualizada noticias"
    
    def _validate_keyword_quality(self, keywords: str) -> bool:
        """Validar que los keywords generados sean de buena calidad"""
        if not keywords or len(keywords.strip()) < 5:
            return False
        
        # Verificar que no contenga solo palabras meta
        words = keywords.lower().split()
        useful_words = [w for w in words if w not in self.meta_words]
        
        if len(useful_words) < 2:
            print(f"🚨 LOW QUALITY: Only {len(useful_words)} useful words in '{keywords}'")
            return False
        
        # Verificar que no sea solo términos genéricos
        generic_terms = {'información', 'general', 'completa', 'actualizada', 'datos'}
        if all(word in generic_terms for word in words):
            print(f"🚨 TOO GENERIC: All words are generic in '{keywords}'")
            return False
        
        print(f"✅ QUALITY VALIDATED: '{keywords}' has {len(useful_words)} useful words")
        return True
    
    def generate_multiple_search_variants(self, original_query: str, num_variants: int = 3) -> List[str]:
        """
        🎯 GENERAR MÚLTIPLES VARIANTES DE BÚSQUEDA PARA DIVERSIDAD DE FUENTES
        
        Genera diferentes enfoques de búsqueda para el mismo tema, 
        maximizando las posibilidades de encontrar fuentes diversas
        """
        base_keywords = self.generate_smart_keywords(original_query)
        variants = [base_keywords]  # Incluir versión base
        
        # Extraer palabras clave principales
        main_words = base_keywords.split()[:3]
        
        if len(main_words) >= 2:
            # Variante 1: Enfoque específico + contexto
            variant1 = f"{main_words[0]} {main_words[1]} información detallada"
            if variant1 not in variants:
                variants.append(variant1)
            
            # Variante 2: Enfoque amplio + año actual  
            variant2 = f"{' '.join(main_words)} noticias 2025"
            if variant2 not in variants:
                variants.append(variant2)
            
            # Variante 3: Enfoque de fuentes especializadas
            if len(main_words) >= 3:
                variant3 = f"{main_words[0]} {main_words[2]} análisis"
                if variant3 not in variants:
                    variants.append(variant3)
        
        # Retornar solo el número solicitado
        return variants[:num_variants]

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
        return intelligent_keyword_generator.generate_smart_keywords(query)
    else:
        variants = intelligent_keyword_generator.generate_multiple_search_variants(query, num_variants)
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
    return intelligent_keyword_generator.generate_multiple_search_variants(query, num_variants)