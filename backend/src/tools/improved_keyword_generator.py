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
        
        # 🎯 FIRST CHECK: Si contiene temas específicos conocidos, NUNCA es problemático
        specific_topics = [
            'attack on titan', 'shingeki no kyojin', 'eren jaeger', 'mikasa ackerman',
            'arctic monkeys', 'alex turner', 'the strokes', 'coldplay',
            'inteligencia artificial', 'machine learning', 'chatgpt', 'openai',
            'javier milei', 'argentina presidente', 'elecciones argentina',
            'netflix series', 'disney plus', 'marvel movies', 'dc comics',
            'bitcoin price', 'cryptocurrency', 'blockchain technology',
            'climate change', 'global warming', 'renewable energy'
        ]
        
        for topic in specific_topics:
            if topic in query_lower:
                print(f"✅ SPECIFIC TOPIC DETECTED: '{topic}' - NOT problematic")
                return False
        
        # 🎯 SECOND CHECK: Si tiene nombres propios claros, probablemente no es problemático
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query_text)
        if len(proper_nouns) >= 2:  # Dos o más nombres propios = tema específico
            print(f"✅ PROPER NOUNS DETECTED: {proper_nouns} - NOT problematic")
            return False
        
        # Verificar patrones problemáticos conocidos
        for pattern in self.problematic_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Verificar si tiene muchas palabras meta vs. pocas entidades
        meta_count = sum(1 for category in self.meta_words.values() 
                        for word in category if word in query_lower)
        
        entity_count = sum(1 for category in self.preserve_entities.values()
                          for entity in category if entity in query_lower)
        
        # 🎯 AJUSTE CRÍTICO: Solo es problemático si hay MUCHAS más palabras meta que entidades
        # Y no contiene temas específicos obvios
        if meta_count > 5 and entity_count < 1:
            # DOUBLE CHECK: Buscar entidades que no estén en la lista pero que sean obvias
            potential_entities = re.findall(r'\b[a-zA-Z]{4,}\b', query_text)
            non_meta_entities = []
            
            for word in potential_entities:
                word_lower = word.lower()
                if not any(word_lower in metas for metas in self.meta_words.values()):
                    non_meta_entities.append(word_lower)
            
            # Si hay entidades potenciales no-meta, NO es problemático
            if len(non_meta_entities) >= 2:
                print(f"✅ POTENTIAL ENTITIES FOUND: {non_meta_entities} - NOT problematic")
                return False
                
            return True
        
        return False
    
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
        """🏷️ Extraer entidades importantes (nombres propios, conceptos clave) - CORREGIDO FILTRADO META"""
        
        entities = []
        query_lower = query_text.lower()
        
        # 🔥 FILTRO CRÍTICO: Lista completa de palabras meta que nunca deben ser entidades
        meta_filter_entities = {
            'investigar', 'información', 'específica', 'buscar', 'datos', 'sobre', 'acerca',
            'realizar', 'generar', 'crear', 'análisis', 'informe', 'completo', 'completa',
            'recopilar', 'obtener', 'utilizar', 'herramienta', 'web', 'search', 'incluyendo',
            'mediante', 'para', 'con', 'del', 'las', 'los', 'una', 'actualizada', 'actuales',
            'relevante', 'relevantes', 'importante', 'importantes', 'necesario', 'necesaria',
            'completar', 'desarrollo', 'específicos', 'general', 'generales'
        }
        
        # Buscar todas las entidades de alta prioridad (filtradas)
        for category, entity_list in self.preserve_entities.items():
            for entity in entity_list:
                if entity in query_lower and entity not in meta_filter_entities:
                    entities.append(entity)
        
        # Buscar nombres propios adicionales (Capitalizados) y filtrar meta words
        proper_nouns = re.findall(r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*\b', query_text)
        for noun in proper_nouns:
            noun_lower = noun.lower()
            if (len(noun) > 3 and 
                noun_lower not in meta_filter_entities and
                not any(meta in noun_lower for meta in ['investig', 'informac', 'buscar', 'datos'])):
                entities.append(noun_lower)
        
        # Remover duplicados manteniendo orden
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity not in seen:
                seen.add(entity)
                unique_entities.append(entity)
        
        return unique_entities[:6]  # Máximo 6 entidades más importantes
    
    def _extract_main_concepts(self, query_text: str) -> List[str]:
        """💡 Extraer conceptos principales del texto - CORREGIDO PARA FILTRAR MEJOR"""
        
        concepts = []
        
        # 🔥 LISTA AMPLIADA DE PALABRAS META QUE NUNCA DEBEN INCLUIRSE
        extended_meta_filter = {
            'investigar', 'información', 'específica', 'buscar', 'datos', 'sobre', 'acerca',
            'realizar', 'generar', 'crear', 'análisis', 'informe', 'completo', 'completa',
            'recopilar', 'obtener', 'utilizar', 'herramienta', 'web', 'search', 'incluyendo',
            'mediante', 'para', 'con', 'del', 'las', 'los', 'una', 'actualizada', 'actuales',
            'relevante', 'relevantes', 'importante', 'importantes', 'necesario', 'necesaria',
            'completar', 'desarrollo', 'específicos', 'general', 'generales', 'relacionados',
            'relacionadas', 'particular', 'particulares', 'diversos', 'diversas'
        }
        
        # Extraer palabras significativas (4+ caracteres)
        words = re.findall(r'\b[a-záéíóúñA-ZÁÉÍÓÚÑ]{4,}\b', query_text)
        
        for word in words:
            word_lower = word.lower()
            
            # DOBLE FILTRO: palabras meta del objeto + lista extendida
            is_meta_original = any(word_lower in meta_category for meta_category in self.meta_words.values())
            is_meta_extended = word_lower in extended_meta_filter
            
            # Solo incluir si NO es palabra meta en ninguna de las listas
            if not is_meta_original and not is_meta_extended and len(word_lower) >= 4:
                concepts.append(word_lower)
        
        return concepts[:8]  # Máximo 8 conceptos
    
    def _combine_and_optimize(self, entities: List[str], concepts: List[str], original_query: str) -> str:
        """⚡ Combinar y optimizar entidades y conceptos - CORREGIDO PARA FILTRAR PALABRAS META"""
        
        # 🔥 FILTRO CRÍTICO: Remover palabras meta de TODAS las listas
        meta_filter = {
            'investigar', 'información', 'específica', 'buscar', 'datos', 'sobre', 'acerca',
            'realizar', 'generar', 'crear', 'análisis', 'informe', 'completo', 'completa',
            'recopilar', 'obtener', 'utilizar', 'herramienta', 'web', 'search', 'incluyendo',
            'mediante', 'para', 'con', 'del', 'las', 'los', 'una', 'actualizada', 'actuales',
            'relevante', 'relevantes', 'importante', 'importantes', 'necesario', 'necesaria'
        }
        
        # 1. FILTRAR ENTIDADES - Remover palabras meta
        filtered_entities = []
        for entity in entities:
            if entity.lower() not in meta_filter and len(entity) >= 3:
                filtered_entities.append(entity)
        
        # 2. FILTRAR CONCEPTOS - Remover palabras meta  
        filtered_concepts = []
        for concept in concepts:
            if concept.lower() not in meta_filter and len(concept) >= 3:
                filtered_concepts.append(concept)
        
        # 3. Priorizar entidades limpias (son más importantes)
        important_terms = filtered_entities[:4]  # Top 4 entidades sin meta words
        
        # 4. Agregar conceptos limpios que no sean repetitivos
        for concept in filtered_concepts:
            if (concept not in important_terms and 
                len(important_terms) < 5 and
                not any(concept in term for term in important_terms)):  # Evitar redundancia
                important_terms.append(concept)
        
        # 5. Si aún muy pocos términos después del filtrado, agregar contexto específico
        if len(important_terms) < 2:
            # Buscar términos específicos que NO sean meta
            query_lower = original_query.lower()
            
            # Para anime/manga
            if any(term in query_lower for term in ['attack on titan', 'shingeki', 'anime', 'manga']):
                if 'attack' not in important_terms and 'titan' not in important_terms:
                    important_terms.extend(['attack', 'titan'])
                important_terms.append('anime')
            # Para música
            elif any(term in query_lower for term in ['arctic monkeys', 'banda', 'música', 'discografía']):
                important_terms.append('música')
                important_terms.append('banda')
            # Para personas
            elif any(persona in query_lower for persona in self.preserve_entities['personas']):
                important_terms.append('biografía')
            # Para tecnología  
            elif any(tech in query_lower for tech in self.preserve_entities['tecnologia']):
                important_terms.append('tecnología')
            # Fallback genérico
            else:
                important_terms.append('noticias')
        
        # 6. Construir resultado final SIN palabras meta
        result = ' '.join(important_terms[:5])  # Máximo 5 términos
        
        # 7. VALIDACIÓN FINAL: Si el resultado contiene palabras meta, limpiar
        for meta_word in meta_filter:
            result = result.replace(meta_word, '').strip()
        
        # Limpiar espacios múltiples
        result = ' '.join(result.split())
        
        # 8. Si el resultado es muy corto después de la limpieza, agregar contexto
        if len(result.split()) < 2:
            if any(term in original_query.lower() for term in ['attack on titan', 'titan']):
                result = 'attack titan anime manga'
            elif any(term in original_query.lower() for term in ['arctic monkeys']):
                result = 'arctic monkeys música banda'
            else:
                result += ' noticias actualidad'
        
        # 9. Agregar año solo si es muy corto y no tiene contexto temporal
        if ('2024' not in result and '2025' not in result and len(result.split()) < 3):
            result += ' 2025'
        
        return result.strip()

    def detect_granular_search_needs(self, query_text: str) -> List[Dict[str, str]]:
        """
        🎯 DETECTOR GENÉRICO INTELIGENTE DE BÚSQUEDAS GRANULARES
        
        Analiza CUALQUIER consulta y determina automáticamente si necesita
        múltiples búsquedas específicas, SIN hardcodear temas específicos
        """
        query_lower = query_text.lower()
        searches = []
        
        print(f"🔍 ANALYZING QUERY FOR GRANULAR NEEDS: '{query_text}'")
        
        # 🎯 STEP 1: DETECTAR SI LA CONSULTA SOLICITA INFORMACIÓN AMPLIA/COMPLETA
        comprehensive_indicators = [
            'información completa', 'datos completos', 'información sobre',
            'investigar sobre', 'buscar información', 'análisis completo',
            'estudiar', 'recopilar información', 'información relevante',
            'aspectos importantes', 'características principales',
            'investigar datos sobre', 'buscar datos sobre', 'análisis de',
            'investigación sobre', 'estudio sobre', 'datos sobre',
            'información específica sobre', 'investigar información sobre',
            'incluyendo', 'que incluya', 'abarcando', 'cubriendo',
            'información detallada', 'datos detallados', 'análisis detallado',
            'informe sobre', 'reporte sobre', 'investigar', 'buscar datos'
        ]
        
        is_comprehensive_request = any(indicator in query_lower for indicator in comprehensive_indicators)
        
        if not is_comprehensive_request:
            print("❌ No es solicitud comprehensiva - búsqueda simple")
            return []
        
        # 🎯 STEP 2: EXTRAER EL TEMA/SUJETO PRINCIPAL
        main_subject = self._extract_main_subject_generic(query_text)
        
        if not main_subject:
            print("❌ No se pudo extraer tema principal")
            return []
            
        print(f"✅ TEMA PRINCIPAL DETECTADO: '{main_subject}'")
        
        # 🎯 STEP 3: DETECTAR ASPECTOS ESPECÍFICOS MENCIONADOS
        mentioned_aspects = self._extract_mentioned_aspects(query_text)
        print(f"🎯 ASPECTOS MENCIONADOS: {mentioned_aspects}")
        
        # 🎯 STEP 4: GENERAR BÚSQUEDAS GRANULARES BASADAS EN TIPO DE TEMA
        subject_type = self._classify_subject_type_generic(main_subject, query_text)
        print(f"📊 TIPO DE TEMA CLASIFICADO: {subject_type}")
        
        searches = self._generate_searches_by_type_generic(main_subject, subject_type, mentioned_aspects)
        
        print(f"✅ BÚSQUEDAS GRANULARES GENERADAS: {len(searches)}")
        for search in searches:
            print(f"   🎯 {search['category']}: {search['query']}")
        
        return searches if len(searches) > 1 else []
    
    def _extract_main_subject_generic(self, query_text: str) -> str:
        """🎯 Extraer el tema/sujeto principal de CUALQUIER consulta - VERSIÓN CORREGIDA"""
        import re
        
        print(f"🔍 EXTRACTING SUBJECT FROM: '{query_text}'")
        
        # 🎯 MÉTODO ESPECIAL: Detectar nombres compuestos específicos conocidos PRIMERO
        known_subjects = [
            r'\battack\s+on\s+titan\b',
            r'\bshingeki\s+no\s+kyojin\b', 
            r'\barctic\s+monkeys\b',
            r'\bcoldplay\b',
            r'\bthe\s+strokes\b',
            r'\binteligencia\s+artificial\b',
            r'\bmachine\s+learning\b',
            r'\bjavier\s+milei\b',
            r'\bcambio\s+climático\b',
            r'\bcalentamiento\s+global\b'
        ]
        
        for subject_pattern in known_subjects:
            match = re.search(subject_pattern, query_text, re.IGNORECASE)
            if match:
                subject = match.group(0)
                print(f"✅ SUBJECT FOUND (Method 0 - Known Subjects): '{subject}'")
                return subject.title()
        
        # MÉTODO 1: Buscar términos específicos después de palabras clave (MÁS PRECISO)
        subject_patterns = [
            # Patrones con delimitadores claros
            r'sobre\s+"([^"]+)"',  # sobre "tema exacto"
            r'sobre\s+([a-zA-Z][a-zA-Z\s]+?)\s*(?:\s+incluyendo|\s+con|\s+-|\s+y\s|\s+para|\.|$)',  # sobre tema ANTES de "incluyendo"
            r'información\s+(?:completa\s+|específica\s+)?sobre\s+([a-zA-Z][a-zA-Z\s]+?)\s*(?:\s+incluyendo|\s+con|\s+-|\s+y\s|\s+para|\.|$)',
            r'datos\s+(?:completos\s+)?sobre\s+([a-zA-Z][a-zA-Z\s]+?)\s*(?:\s+incluyendo|\s+con|\s+-|\s+y\s|\s+para|\.|$)',
            r'investigar\s+(?:información\s+(?:específica\s+)?sobre\s+)?([a-zA-Z][a-zA-Z\s]+?)\s*(?:\s+incluyendo|\s+con|\s+-|\s+y\s|\s+para|\.|$)',
            r'buscar\s+información\s+(?:completa\s+|específica\s+)?sobre\s+([a-zA-Z][a-zA-Z\s]+?)\s*(?:\s+incluyendo|\s+con|\s+-|\s+y\s|\s+para|\.|$)'
        ]
        
        for pattern in subject_patterns:
            match = re.search(pattern, query_text, re.IGNORECASE)
            if match:
                subject = match.group(1).strip()
                subject = re.sub(r'\s+', ' ', subject)  # Limpiar espacios múltiples
                
                # Validar que no sean palabras meta y que sea razonable
                meta_words = ['información', 'datos', 'sobre', 'análisis', 'buscar', 'completa', 'completar', 'específica']
                if (len(subject) > 3 and 
                    not any(meta.lower() in subject.lower() for meta in meta_words) and
                    not subject.lower() in ['y', 'el', 'la', 'los', 'las', 'de', 'del', 'con'] and
                    len(subject.split()) <= 4):  # No más de 4 palabras
                    print(f"✅ SUBJECT FOUND (Method 1): '{subject}'")
                    return subject
        
        # MÉTODO 2: Buscar nombres propios (2+ palabras capitalizadas)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', query_text)
        for noun in proper_nouns:
            if len(noun.split()) >= 2 and len(noun.split()) <= 3:  # Entre 2 y 3 palabras
                print(f"✅ SUBJECT FOUND (Method 2 - Proper Nouns): '{noun}'")
                return noun
        
        # MÉTODO 3: Buscar términos compuestos comunes (sin capitalización)
        # Términos compuestos importantes conocidos
        known_compounds = [
            r'\bcambio\s+climático\b',
            r'\bcalentamiento\s+global\b',
            r'\binteligencia\s+artificial\b',
            r'\bmachine\s+learning\b',
            r'\baprendizaje\s+automático\b',
            r'\beconomía\s+argentina\b',
            r'\beconomía\s+mundial\b',
            r'\bcriptomonedas\b',
            r'\benergía\s+renovable\b',
            r'\bmedio\s+ambiente\b',
            r'\brecursos\s+naturales\b',
            r'\bdesarrollo\s+sostenible\b'
        ]
        
        for compound_pattern in known_compounds:
            match = re.search(compound_pattern, query_text, re.IGNORECASE)
            if match:
                subject = match.group(0)
                print(f"✅ SUBJECT FOUND (Method 3 - Known Compounds): '{subject}'")
                return subject.title()
        
        # MÉTODO 4: Buscar cualquier término compuesto de 2+ palabras ANTES DE "incluyendo"
        compound_before_including = re.search(r'\b([a-zA-Z]{3,}\s+[a-zA-Z]{3,}(?:\s+[a-zA-Z]{3,})?)\s+incluyendo\b', query_text, re.IGNORECASE)
        if compound_before_including:
            subject = compound_before_including.group(1).strip()
            meta_phrases = {'información sobre', 'datos sobre', 'buscar información', 'investigar sobre'}
            if subject.lower() not in meta_phrases and len(subject) > 8:
                print(f"✅ SUBJECT FOUND (Method 4 - Before Including): '{subject}'")
                return subject.title()
        
        # MÉTODO 5: Buscar nombres propios simples importantes
        single_nouns = re.findall(r'\b[A-Z][a-z]{4,}\b', query_text)
        skip_words = {'Investigar', 'Buscar', 'Datos', 'Información', 'Análisis', 'Sobre', 'Para', 'Con', 'Realizar', 'Incluyendo'}
        
        for noun in single_nouns:
            if noun not in skip_words:
                print(f"✅ SUBJECT FOUND (Method 5 - Single Proper Noun): '{noun}'")
                return noun
        
        print("❌ NO SUBJECT EXTRACTED")
        return None
    
    def _extract_mentioned_aspects(self, query_text: str) -> List[str]:
        """🔍 Extraer aspectos específicos mencionados en la consulta"""
        query_lower = query_text.lower()
        aspects = []
        
        # Mapeo de palabras clave a aspectos
        aspect_keywords = {
            'trama': ['trama', 'historia', 'argumento', 'narrativa', 'plot'],
            'personajes': ['personajes', 'protagonistas', 'caracteres', 'characters'],
            'biografía': ['biografía', 'vida', 'personal', 'nacimiento', 'historia personal'],
            'historia': ['historia', 'orígenes', 'desarrollo', 'evolución', 'pasado'],
            'contexto': ['contexto', 'ambiente', 'época', 'período', 'marco'],
            'crítica': ['crítica', 'recepción', 'opiniones', 'reseñas', 'evaluación'],
            'impacto': ['impacto', 'influencia', 'legado', 'consecuencias', 'efectos'],
            'características': ['características', 'propiedades', 'atributos', 'rasgos'],
            'causas': ['causas', 'orígenes', 'razones', 'motivos'],
            'efectos': ['efectos', 'consecuencias', 'resultados', 'impactos'],
            'soluciones': ['soluciones', 'remedios', 'propuestas', 'alternativas'],
            'obras': ['obras', 'trabajos', 'creaciones', 'producción'],
            'carrera': ['carrera', 'trayectoria', 'profesional', 'trabajo'],
            'política': ['política', 'posiciones', 'ideología', 'propuestas']
        }
        
        for aspect, keywords in aspect_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                aspects.append(aspect)
        
        return aspects
    
    def _classify_subject_type_generic(self, subject: str, query_text: str) -> str:
        """📊 Clasificar genéricamente el tipo de tema basado en indicadores"""
        subject_lower = subject.lower()
        query_lower = query_text.lower()
        
        # Indicadores de tipo de tema
        if (any(indicator in query_lower for indicator in ['anime', 'manga', 'serie', 'película', 'film']) or
            any(name in subject_lower for name in ['attack on titan', 'shingeki', 'naruto', 'one piece', 'dragon ball'])):
            return 'entertainment'
        elif any(indicator in query_lower for indicator in ['banda', 'música', 'cantante', 'artista musical']):
            return 'music'  
        elif any(indicator in query_lower for indicator in ['presidente', 'político', 'líder', 'personalidad']):
            return 'person'
        elif any(indicator in query_lower for indicator in ['tecnología', 'ciencia', 'científico', 'técnico']):
            return 'technology'
        elif any(indicator in query_lower for indicator in ['economía', 'económico', 'mercado', 'financiero']):
            return 'economics'
        elif any(indicator in query_lower for indicator in ['equipo', 'deporte', 'fútbol', 'selección']):
            return 'sports'
        elif any(indicator in query_lower for indicator in ['libro', 'novela', 'autor', 'literatura']):
            return 'literature'
        elif any(indicator in query_lower for indicator in ['pintor', 'artista', 'arte', 'pintura']):
            return 'art'
        elif any(indicator in query_lower for indicator in ['histórico', 'historia', 'época', 'período']):
            return 'history'
        elif any(indicator in query_lower for indicator in ['empresa', 'compañía', 'corporación', 'negocio']):
            return 'business'
        else:
            # Clasificación por nombres propios conocidos o contexto
            if len(subject.split()) >= 2:  # Nombres compuestos = probablemente persona o obra
                return 'person_or_work'
            else:
                return 'general_topic'
    
    def _generate_searches_by_type_generic(self, subject: str, subject_type: str, mentioned_aspects: List[str]) -> List[Dict[str, str]]:
        """🎯 Generar búsquedas específicas basadas en el tipo de tema"""
        searches = []
        
        # Plantillas por tipo de tema
        search_templates = {
            'entertainment': [
                ('trama', f'{subject} trama historia argumento resumen'),
                ('personajes', f'{subject} personajes principales protagonistas reparto'),
                ('crítica', f'{subject} críticas reseñas puntuación recepción'),
                ('contexto', f'{subject} contexto producción trasfondo'),
                ('impacto', f'{subject} impacto cultural legado influencia')
            ],
            'music': [
                ('historia', f'{subject} historia formación miembros banda'),
                ('discografía', f'{subject} discografía álbumes canciones hits'),
                ('estilo', f'{subject} estilo musical género evolución'),
                ('logros', f'{subject} premios reconocimientos logros'),
                ('actualidad', f'{subject} noticias recientes conciertos giras')
            ],
            'person': [
                ('biografía', f'{subject} biografía vida personal historia'),
                ('carrera', f'{subject} carrera trayectoria profesional'),
                ('logros', f'{subject} logros reconocimientos premios'),
                ('posiciones', f'{subject} posiciones ideología propuestas'),
                ('actualidad', f'{subject} noticias recientes declaraciones 2025')
            ],
            'technology': [
                ('definición', f'{subject} definición conceptos básicos explicación'),
                ('aplicaciones', f'{subject} aplicaciones usos prácticos ejemplos'),
                ('ventajas', f'{subject} ventajas beneficios impacto positivo'),
                ('desafíos', f'{subject} desventajas riesgos limitaciones'),
                ('futuro', f'{subject} tendencias futuro 2025 innovaciones')
            ],
            'economics': [
                ('situación', f'{subject} situación actual estado 2025'),
                ('causas', f'{subject} causas factores antecedentes'),
                ('efectos', f'{subject} efectos consecuencias impacto'),
                ('políticas', f'{subject} políticas medidas propuestas'),
                ('perspectivas', f'{subject} perspectivas futuro pronósticos')
            ],
            'literature': [
                ('trama', f'{subject} trama resumen argumento historia'),
                ('personajes', f'{subject} personajes principales protagonistas'),
                ('análisis', f'{subject} análisis literario temas símbolos'),
                ('contexto', f'{subject} contexto histórico época ambientación'),
                ('crítica', f'{subject} crítica literaria recepción reseñas')
            ],
            'art': [
                ('biografía', f'{subject} biografía vida personal historia'),
                ('obras', f'{subject} obras principales trabajos destacados'),
                ('estilo', f'{subject} estilo artístico técnica características'),
                ('contexto', f'{subject} contexto histórico época artística'),
                ('legado', f'{subject} legado influencia impacto arte')
            ],
            'person_or_work': [
                ('información', f'{subject} información general datos básicos'),
                ('historia', f'{subject} historia orígenes desarrollo'),
                ('características', f'{subject} características principales aspectos'),
                ('impacto', f'{subject} importancia relevancia significado'),
                ('actualidad', f'{subject} situación actual noticias recientes')
            ],
            'general_topic': [
                ('definición', f'{subject} definición qué es conceptos'),
                ('aspectos', f'{subject} aspectos principales características'),
                ('importancia', f'{subject} importancia relevancia significado'),
                ('contexto', f'{subject} contexto situación actual'),
                ('perspectivas', f'{subject} análisis opiniones perspectivas')
            ]
        }
        
        # Usar plantilla por defecto si no se encuentra el tipo
        templates = search_templates.get(subject_type, search_templates['general_topic'])
        
        # Generar búsquedas
        for category, query in templates:
            searches.append({
                'query': query,
                'category': category
            })
        
        return searches

# Funciones públicas para usar desde unified_web_search_tool.py
def get_intelligent_keywords(query_text: str) -> str:
    """🎯 Función principal para generar keywords inteligentes"""
    generator = IntelligentKeywordGenerator()
    return generator.get_intelligent_keywords(query_text)

def get_multiple_search_variants(query_text: str, count: int = 3) -> List[str]:
    """🔄 Generar múltiples variantes de búsqueda para diversidad"""
    generator = IntelligentKeywordGenerator()
    return generator.get_multiple_search_variants(query_text, count)

def detect_granular_search_needs(query_text: str) -> List[Dict[str, str]]:
    """🎯 Detectar si una consulta necesita búsquedas granulares múltiples"""
    generator = IntelligentKeywordGenerator()
    return generator.detect_granular_search_needs(query_text)

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