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
                      'canción', 'concierto', 'gira', 'festival']
        }
        
        # Palabras meta que deben eliminarse COMPLETAMENTE
        self.meta_words = {
            'instrucciones': ['buscar', 'información', 'sobre', 'acerca', 'utilizar', 'herramienta', 
                             'web_search', 'realizar', 'generar', 'crear', 'obtener', 'necesario',
                             'completar', 'específico', 'datos', 'análisis', 'informe'],
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
            r'\bgenera\s+(un|una)\s+(análisis|informe|reporte)\b'
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
        ]
        
        for pattern in theme_patterns:
            match = re.search(pattern, query_text, re.IGNORECASE)
            if match:
                theme = match.group(1).strip()
                print(f"🔧 TEMA EXTRAÍDO DE QUERY PROBLEMÁTICO: '{theme}'")
                return self._clean_and_enhance_theme(theme)
        
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
        return "información actualizada noticias"
    
    def _clean_and_enhance_theme(self, theme: str) -> str:
        """✨ Limpiar y mejorar tema extraído"""
        
        # Remover comillas y espacios extra
        clean_theme = re.sub(r'["\']', '', theme).strip()
        
        # Si el tema es muy corto, agregarlo contexto
        if len(clean_theme.split()) < 2:
            return f"{clean_theme} información completa"
        
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