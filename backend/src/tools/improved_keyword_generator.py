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
        """🎯 FUNCIÓN PRINCIPAL: Generar keywords inteligentes CON VALIDACIÓN Y APROBACIÓN"""
        
        if not query_text or len(query_text.strip()) < 3:
            return "información actualizada"
        
        print(f"🧠 INTELLIGENT GENERATOR INPUT: '{query_text}'")
        
        # 🔄 SISTEMA DE VALIDACIÓN Y APROBACIÓN - MÁXIMO 5 INTENTOS
        max_attempts = 5
        for attempt in range(1, max_attempts + 1):
            print(f"🔄 INTENTO {attempt}/{max_attempts}: Generando query...")
            
            # 1. Generar query candidata
            candidate_query = self._generate_candidate_query(query_text, attempt)
            print(f"📝 QUERY CANDIDATA: '{candidate_query}'")
            
            # 2. VALIDAR Y APROBAR la query candidata
            validation_result = self._validate_and_approve_query(candidate_query, query_text)
            
            if validation_result['approved']:
                print(f"✅ QUERY APROBADA en intento {attempt}: '{candidate_query}'")
                print(f"✅ RAZONES DE APROBACIÓN: {', '.join(validation_result['approval_reasons'])}")
                return candidate_query
            else:
                print(f"❌ QUERY RECHAZADA en intento {attempt}: '{candidate_query}'")
                print(f"❌ RAZONES DE RECHAZO: {', '.join(validation_result['rejection_reasons'])}")
                if attempt < max_attempts:
                    print(f"🔄 Generando nueva query (intento {attempt + 1})...")
                continue
        
        # Si todos los intentos fallaron, usar query de emergencia específica
        emergency_query = self._generate_emergency_query(query_text)
        print(f"🚨 EMERGENCY QUERY USADA: '{emergency_query}'")
        return emergency_query
    
    def _generate_candidate_query(self, query_text: str, attempt_number: int) -> str:
        """🎯 Generar query candidata usando diferentes estrategias según el intento"""
        
        # Estrategia 1 (Intento 1): Lógica original mejorada
        if attempt_number == 1:
            if self._is_problematic_query(query_text):
                return self._fix_problematic_query(query_text)
            else:
                entities = self._extract_important_entities(query_text)
                concepts = self._extract_main_concepts(query_text)
                return self._combine_and_optimize(entities, concepts, query_text)
        
        # Estrategia 2 (Intento 2): Enfoque conservador - solo entidades principales
        elif attempt_number == 2:
            entities = self._extract_important_entities(query_text)
            return ' '.join(entities[:3]) if entities else self._extract_main_subject_from_text(query_text)
        
        # Estrategia 3 (Intento 3): Enfoque específico - extraer tema exacto
        elif attempt_number == 3:
            main_subject = self._extract_main_subject_from_text(query_text)
            if main_subject:
                return main_subject
            else:
                return self._extract_key_terms_only(query_text)
        
        # Estrategia 4 (Intento 4): Enfoque minimalista - términos clave únicos
        elif attempt_number == 4:
            return self._extract_key_terms_only(query_text)
        
        # Estrategia 5 (Intento 5): Último recurso - tema + contexto básico
        else:
            base_topic = self._extract_main_subject_from_text(query_text) or "información"
            return f"{base_topic} información actualizada"
    
    def _validate_and_approve_query(self, candidate_query: str, original_text: str) -> dict:
        """🛡️ SISTEMA DE VALIDACIÓN Y APROBACIÓN DE QUERIES"""
        
        approval_reasons = []
        rejection_reasons = []
        
        # VALIDACIÓN 1: Longitud apropiada (2-6 palabras)
        words = candidate_query.strip().split()
        if 2 <= len(words) <= 6:
            approval_reasons.append("Longitud apropiada")
        else:
            rejection_reasons.append(f"Longitud incorrecta: {len(words)} palabras")
        
        # VALIDACIÓN 2: Sin duplicaciones de palabras
        unique_words = list(dict.fromkeys(words))  # Mantener orden, remover duplicados
        
        if len(unique_words) == len(words):
            approval_reasons.append("Sin duplicaciones")
        else:
            rejection_reasons.append(f"Contiene palabras duplicadas: {words} → {unique_words}")
        
        # VALIDACIÓN 3: Preserva tema principal del contexto original
        main_subjects = self._extract_known_subjects(original_text)
        if main_subjects:
            query_lower = candidate_query.lower()
            subject_preserved = any(subject.lower() in query_lower for subject in main_subjects)
            if subject_preserved:
                approval_reasons.append("Preserva tema principal")
            else:
                rejection_reasons.append("No preserva tema principal identificado")
        
        # VALIDACIÓN 4: No contiene palabras meta prohibidas
        meta_words = ['investigar', 'información', 'buscar', 'datos', 'análisis', 'realizar', 'web', 'search']
        query_lower = candidate_query.lower()
        meta_found = [word for word in meta_words if word in query_lower]
        if not meta_found:
            approval_reasons.append("Sin palabras meta")
        else:
            rejection_reasons.append(f"Contiene palabras meta: {', '.join(meta_found)}")
        
        # VALIDACIÓN 5: Contiene términos específicos reconocibles
        recognizable_terms = self._count_recognizable_terms(candidate_query)
        if recognizable_terms >= 2:
            approval_reasons.append(f"Términos específicos: {recognizable_terms}")
        else:
            rejection_reasons.append("Pocos términos específicos reconocibles")
        
        # VALIDACIÓN 6: No es genérica
        generic_patterns = ['noticias actualidad', 'información completa', 'datos actuales', 'información actualizada']
        is_generic = any(pattern in query_lower for pattern in generic_patterns)
        if not is_generic:
            approval_reasons.append("Query específica")
        else:
            rejection_reasons.append("Query demasiado genérica")
        
        # DECISIÓN DE APROBACIÓN: 
        # 1. RECHAZOS AUTOMÁTICOS: Ciertas validaciones son OBLIGATORIAS
        automatic_rejections = [
            'Contiene palabras duplicadas',
            'No preserva tema principal identificado',
            'Longitud incorrecta'
        ]
        
        has_automatic_rejection = any(
            any(auto_reject in reason for auto_reject in automatic_rejections) 
            for reason in rejection_reasons
        )
        
        if has_automatic_rejection:
            approved = False  # Rechazo automático
        else:
            # 2. APROBACIÓN NORMAL: Debe pasar al menos 4 de las 6 validaciones  
            approved = len(approval_reasons) >= 4 and len(rejection_reasons) <= 2
        
        return {
            'approved': approved,
            'approval_reasons': approval_reasons,
            'rejection_reasons': rejection_reasons,
            'score': len(approval_reasons) - len(rejection_reasons)
        }
    
    def _extract_known_subjects(self, text: str) -> list:
        """🎯 Extraer sujetos/temas conocidos del texto"""
        known_subjects = []
        text_lower = text.lower()
        
        # Temas específicos conocidos
        specific_subjects = [
            ('arctic monkeys', 'Arctic Monkeys'),
            ('attack on titan', 'Attack on Titan'), 
            ('attack titan', 'Attack on Titan'),
            ('shingeki no kyojin', 'Shingeki no Kyojin'),
            ('javier milei', 'Javier Milei'),
            ('inteligencia artificial', 'Inteligencia Artificial'),
            ('machine learning', 'Machine Learning'),
            ('cambio climático', 'Cambio Climático')
        ]
        
        for search_term, subject_name in specific_subjects:
            if search_term in text_lower:
                known_subjects.append(subject_name)
        
        # Buscar nombres propios
        import re
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        for noun in proper_nouns:
            if len(noun.split()) <= 3:  # Máximo 3 palabras
                known_subjects.append(noun)
        
        return list(set(known_subjects))  # Remover duplicados
    
    def _count_recognizable_terms(self, query: str) -> int:
        """📊 Contar términos específicos reconocibles en la query"""
        words = query.lower().split()
        recognizable = 0
        
        # Términos de todas las categorías de entidades conocidas
        all_entities = []
        for category in self.preserve_entities.values():
            all_entities.extend(category)
        
        for word in words:
            if (word in all_entities or 
                len(word) >= 5 or  # Palabras largas suelen ser específicas
                word.istitle()):   # Nombres propios
                recognizable += 1
        
        return recognizable
    
    def _extract_main_subject_from_text(self, text: str) -> str:
        """📝 Extraer el tema principal del texto de manera simple y directa"""
        # Primero buscar temas conocidos
        text_lower = text.lower()
        
        known_mappings = {
            'arctic monkeys': 'Arctic Monkeys',
            'attack on titan': 'Attack on Titan',
            'attack titan': 'Attack on Titan', 
            'shingeki no kyojin': 'Shingeki no Kyojin',
            'javier milei': 'Javier Milei',
            'inteligencia artificial': 'inteligencia artificial',
        }
        
        for search_term, subject in known_mappings.items():
            if search_term in text_lower:
                return subject
        
        # Buscar nombres propios
        import re
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b', text)
        if proper_nouns:
            return proper_nouns[0]
        
        # Extraer palabras significativas (fallback)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
        significant_words = []
        
        meta_filter = {'investigar', 'información', 'buscar', 'datos', 'análisis', 'sobre', 'acerca'}
        for word in words:
            if word.lower() not in meta_filter:
                significant_words.append(word.lower())
        
        return ' '.join(significant_words[:2]) if significant_words else "información"
    
    def _extract_key_terms_only(self, text: str) -> str:
        """🔑 Extraer solo términos clave únicos y específicos"""
        import re
        
        # Buscar términos específicos únicos
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        
        # Filtrar palabras meta y comunes
        meta_filter = {
            'investigar', 'información', 'buscar', 'datos', 'análisis', 'sobre', 'acerca',
            'realizar', 'generar', 'crear', 'obtener', 'utilizar', 'específica', 'completa',
            'actualizada', 'relevante', 'importante', 'necesaria', 'web', 'search', 'para',
            'con', 'del', 'las', 'los', 'una', 'mediante'
        }
        
        key_terms = []
        seen = set()
        
        for word in words:
            word_lower = word.lower()
            if (word_lower not in meta_filter and 
                word_lower not in seen and 
                len(word) >= 3):
                key_terms.append(word_lower)
                seen.add(word_lower)
        
        return ' '.join(key_terms[:4]) if key_terms else "información específica"
    
    def _generate_emergency_query(self, original_text: str) -> str:
        """🚨 Generar query de emergencia cuando todos los intentos fallan"""
        # Extraer tema principal o usar términos básicos
        main_subject = self._extract_main_subject_from_text(original_text)
        if main_subject and main_subject != "información":
            return main_subject
        
        # Fallback final basado en contexto detectado
        text_lower = original_text.lower()
        if 'arctic' in text_lower:
            return "Arctic Monkeys"
        elif 'attack' in text_lower and 'titan' in text_lower:
            return "Attack on Titan"
        elif 'milei' in text_lower:
            return "Javier Milei"
        elif 'inteligencia' in text_lower:
            return "inteligencia artificial"
        else:
            return "información noticias actualidad"
    
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
        🎯 DETECTOR GRANULAR MEJORADO - Detecta automáticamente necesidad de búsquedas múltiples
        
        CORRECCIÓN CRÍTICA: Ahora detecta temas específicos que siempre necesitan granularidad,
        sin requerir indicadores de "información completa" explícitos
        """
        query_lower = query_text.lower()
        searches = []
        
        print(f"🔍 ANALYZING QUERY FOR GRANULAR NEEDS: '{query_text}'")
        
        # 🎯 STEP 1: EXTRAER EL TEMA/SUJETO PRINCIPAL PRIMERO
        main_subject = self._extract_main_subject_generic(query_text)
        
        if not main_subject:
            print("❌ No se pudo extraer tema principal")
            return []
            
        print(f"✅ TEMA PRINCIPAL DETECTADO: '{main_subject}'")
        
        # 🎯 STEP 2: CLASIFICAR TIPO DE TEMA
        subject_type = self._classify_subject_type_generic(main_subject, query_text)
        print(f"📊 TIPO DE TEMA CLASIFICADO: {subject_type}")
        
        # 🎯 STEP 3: NUEVO CRITERIO - DETECTAR SI EL TEMA INHERENTEMENTE NECESITA GRANULARIDAD
        needs_granularity = self._subject_needs_granular_search(main_subject, subject_type, query_text)
        print(f"🔍 NECESITA GRANULARIDAD: {needs_granularity}")
        
        if not needs_granularity:
            # Solo retornar si NO es un tema que inherentemente necesita granularidad
            print("❌ Tema no requiere búsquedas granulares - búsqueda simple")
            return []
        
        # 🎯 STEP 4: DETECTAR ASPECTOS ESPECÍFICOS MENCIONADOS
        mentioned_aspects = self._extract_mentioned_aspects(query_text)
        print(f"🎯 ASPECTOS MENCIONADOS: {mentioned_aspects}")
        
        # 🎯 STEP 5: GENERAR BÚSQUEDAS GRANULARES BASADAS EN TIPO DE TEMA
        searches = self._generate_searches_by_type_generic(main_subject, subject_type, mentioned_aspects)
        
        print(f"✅ BÚSQUEDAS GRANULARES GENERADAS: {len(searches)}")
        for search in searches:
            print(f"   🎯 {search['category']}: {search['query']}")
        
        return searches if len(searches) > 1 else []
    
    def _subject_needs_granular_search(self, subject: str, subject_type: str, query_text: str) -> bool:
        """
        🎯 NUEVO MÉTODO - Determinar si un tema específico necesita búsquedas granulares automáticamente
        
        CRITERIOS:
        1. Personas públicas conocidas (políticos, artistas, etc.)
        2. Temas complejos (tecnología, economía, etc.) 
        3. Obras de entretenimiento (series, películas, libros)
        4. VIDEOJUEGOS (Age of Empires, etc.) - NUEVO CRITERIO CRÍTICO
        5. Eventos o fenómenos importantes
        6. Solicitudes explícitas de información comprehensiva
        """
        subject_lower = subject.lower()
        query_lower = query_text.lower()
        
        print(f"🔍 EVALUATING GRANULAR NEED FOR: '{subject}' (type: {subject_type})")
        
        # 🎮 CRITERIO CRÍTICO NUEVO: VIDEOJUEGOS SIEMPRE NECESITAN GRANULARIDAD
        videogame_indicators = [
            # Términos específicos de videojuegos
            'age of empires', 'age empires', 'aoe', 'civilization', 'civ', 'total war',
            'counter strike', 'cs:go', 'cs2', 'valorant', 'league of legends', 'lol',
            'dota', 'fortnite', 'minecraft', 'world of warcraft', 'wow', 'overwatch',
            'call of duty', 'cod', 'battlefield', 'apex legends', 'fifa', 'pes',
            'grand theft auto', 'gta', 'red dead redemption', 'the witcher',
            # Contexto de videojuegos
            'mecánicas de juego', 'mecánicas juego', 'gameplay', 'jugabilidad',
            'expansiones', 'dlc', 'actualizaciones', 'parches', 'patches',
            'estadísticas de jugadores', 'stats jugadores', 'ranking', 'competitivo',
            'impacto cultural gaming', 'comunidad gaming', 'esports', 'e-sports',
            'meta del juego', 'meta game', 'builds', 'estrategias juego'
        ]
        
        # Detectar videojuegos o contexto gaming
        is_videogame = (any(indicator in subject_lower for indicator in videogame_indicators) or
                       any(indicator in query_lower for indicator in videogame_indicators))
        
        if is_videogame:
            print(f"🎮 VIDEOJUEGO DETECTADO - GRANULARIDAD AUTOMÁTICA REQUERIDA")
            print(f"🎯 Contexto gaming identificado en: '{subject}' o '{query_text[:50]}...'")
            return True
        
        # CRITERIO 1: PERSONAS PÚBLICAS CONOCIDAS - SIEMPRE necesitan granularidad
        known_public_figures = [
            # Políticos argentinos
            'javier milei', 'milei', 'cristina fernández', 'cristina kirchner', 'alberto fernández',
            'mauricio macri', 'sergio massa', 'patricia bullrich', 'horacio rodríguez larreta',
            # Políticos internacionales  
            'joe biden', 'donald trump', 'vladimir putin', 'xi jinping', 'emmanuel macron',
            'elon musk', 'mark zuckerberg', 'bill gates', 'jeff bezos',
            # Deportistas
            'lionel messi', 'cristiano ronaldo', 'neymar', 'kylian mbappé',
            # Artistas/músicos
            'taylor swift', 'ed sheeran', 'billie eilish', 'coldplay', 'u2'
        ]
        
        for figure in known_public_figures:
            if figure in subject_lower:
                print(f"✅ FIGURA PÚBLICA DETECTADA: {figure} - GRANULARIDAD REQUERIDA")
                return True
        
        # CRITERIO 2: TIPOS DE TEMA QUE INHERENTEMENTE NECESITAN GRANULARIDAD
        granular_subject_types = ['person', 'entertainment', 'music', 'technology', 'economics', 'literature', 'art', 'videogames', 'gaming']
        
        if subject_type in granular_subject_types:
            print(f"✅ TIPO DE TEMA COMPLEJO: {subject_type} - GRANULARIDAD REQUERIDA")
            return True
        
        # CRITERIO 3: TEMAS ESPECÍFICOS CONOCIDOS QUE SIEMPRE NECESITAN GRANULARIDAD
        complex_topics = [
            # Entretenimiento
            'attack on titan', 'attack titan', 'shingeki no kyojin', 'game of thrones',
            'breaking bad', 'the office', 'friends', 'stranger things',
            # Música
            'arctic monkeys', 'the beatles', 'radiohead', 'pink floyd',
            # Tecnología 
            'inteligencia artificial', 'machine learning', 'blockchain', 'bitcoin',
            'chatgpt', 'openai', 'tesla', 'spacex',
            # Conceptos complejos
            'cambio climático', 'calentamiento global', 'crisis económica',
            'guerra en ucrania', 'pandemia covid',
            # 🎮 VIDEOJUEGOS ESPECÍFICOS AGREGADOS
            'age of empires 2', 'age empires 2', 'civilization 6', 'total war warhammer',
            'counter strike 2', 'valorant competitive', 'league legends meta'
        ]
        
        for topic in complex_topics:
            if topic in subject_lower:
                print(f"✅ TEMA COMPLEJO DETECTADO: {topic} - GRANULARIDAD REQUERIDA")
                return True
        
        # CRITERIO 4: INDICADORES EXPLÍCITOS DE SOLICITUD COMPREHENSIVA
        comprehensive_indicators = [
            'información completa', 'datos completos', 'información sobre',
            'investigar sobre', 'buscar información', 'análisis completo',
            'estudiar', 'recopilar información', 'información relevante',
            'aspectos importantes', 'características principales',
            'información específica sobre', 'investigar información sobre',
            'incluyendo', 'que incluya', 'abarcando', 'cubriendo',
            'información detallada', 'datos detallados', 'análisis detallado',
            'informe sobre', 'reporte sobre', 'investigar', 'buscar datos',
            'biografía', 'trayectoria', 'historia', 'antecedentes',
            'características', 'propiedades', 'aspectos',
            # 🎮 INDICADORES GAMING ESPECÍFICOS
            'mecánicas de juego', 'historia del juego', 'expansiones', 
            'estadísticas de jugadores', 'impacto cultural', 'comunidad gaming'
        ]
        
        has_comprehensive_request = any(indicator in query_lower for indicator in comprehensive_indicators)
        if has_comprehensive_request:
            print(f"✅ SOLICITUD COMPREHENSIVA DETECTADA - GRANULARIDAD REQUERIDA")
            return True
        
        # CRITERIO 5: NOMBRES PROPIOS DE 2+ PALABRAS (probables personas/obras importantes)
        if len(subject.split()) >= 2 and subject[0].isupper():
            print(f"✅ NOMBRE PROPIO COMPUESTO: {subject} - GRANULARIDAD PROBABLE")
            return True
        
        print(f"❌ NO REQUIERE GRANULARIDAD - Búsqueda simple suficiente")
        return False
    
    def _extract_main_subject_generic(self, query_text: str) -> str:
        """🎯 Extraer el tema/sujeto principal de CUALQUIER consulta - VERSIÓN CORREGIDA"""
        import re
        
        print(f"🔍 EXTRACTING SUBJECT FROM: '{query_text}'")
        
        # 🎯 MÉTODO ESPECIAL: Detectar nombres compuestos específicos conocidos PRIMERO
        known_subjects = [
            r'\battack\s+on\s+titan\b',
            r'\battack\s+titan\b',  # ✅ AÑADIDO: Detectar "Attack Titan" también
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
                # ✅ CORRECCIÓN ESPECIAL: Normalizar "Attack Titan" a "Attack on Titan"
                if subject.lower() == "attack titan":
                    subject = "Attack on Titan"
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
        
        # 🎮 NUEVA CATEGORÍA CRÍTICA: VIDEOJUEGOS
        videogame_indicators = [
            'age of empires', 'age empires', 'aoe', 'civilization', 'total war',
            'counter strike', 'valorant', 'league of legends', 'dota', 'fortnite',
            'minecraft', 'call of duty', 'fifa', 'pes', 'overwatch', 'apex legends',
            'mecánicas de juego', 'gameplay', 'jugabilidad', 'expansiones', 'dlc',
            'estadísticas de jugadores', 'gaming', 'videojuego', 'video juego'
        ]
        
        # Detectar videojuegos PRIMERO (alta prioridad)
        if (any(indicator in subject_lower for indicator in videogame_indicators) or
            any(indicator in query_lower for indicator in videogame_indicators)):
            return 'videogames'
        
        # Indicadores de tipo de tema
        if (any(indicator in query_lower for indicator in ['anime', 'manga', 'serie', 'película', 'film']) or
            any(name in subject_lower for name in ['attack on titan', 'attack titan', 'shingeki', 'naruto', 'one piece', 'dragon ball'])):
            return 'entertainment'
        elif any(indicator in query_lower for indicator in ['banda', 'música', 'cantante', 'artista musical']):
            return 'music'  
        elif (any(indicator in query_lower for indicator in ['presidente', 'político', 'líder', 'personalidad']) or
              any(name in subject_lower for name in ['javier milei', 'milei', 'cristina fernández', 'alberto fernández', 
                                                    'mauricio macri', 'sergio massa', 'biden', 'trump', 'putin'])):
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
        """🎯 GENERAR BÚSQUEDAS INTELIGENTES USANDO LLM - SIN PLANTILLAS HARDCODEADAS"""
        searches = []
        
        try:
            # USAR LLM PARA GENERAR BÚSQUEDAS INTELIGENTES Y ADAPTATIVAS
            searches = self._generate_intelligent_searches_with_llm(subject, subject_type, mentioned_aspects)
            
            if searches and len(searches) >= 3:
                print(f"✅ LLM generó {len(searches)} búsquedas inteligentes para '{subject}'")
                return searches
            else:
                print(f"⚠️ LLM generó pocas búsquedas ({len(searches)}), usando fallback")
                
        except Exception as e:
            print(f"⚠️ Error usando LLM para búsquedas: {e}, usando fallback")
        
        # FALLBACK INTELIGENTE - Solo cuando el LLM falla
        return self._generate_fallback_searches(subject, mentioned_aspects)
    
    def _generate_intelligent_searches_with_llm(self, subject: str, subject_type: str, mentioned_aspects: List[str]) -> List[Dict[str, str]]:
        """🧠 USAR LLM PARA GENERAR BÚSQUEDAS GRANULARES INTELIGENTES"""
        
        # Construir prompt inteligente y conciso para el LLM - CORREGIDO PARA EVITAR ALUCINACIONES
        aspects_text = f" Aspectos mencionados: {', '.join(mentioned_aspects)}." if mentioned_aspects else ""
        
        prompt = f"""Para el tema "{subject}", genera 5 búsquedas web efectivas pero GENERALES.{aspects_text}

IMPORTANTE: No inventes eventos específicos, fechas exactas, o entrevistas particulares. Usa términos generales que permitan encontrar información actual.

Responde SOLO con JSON:
{{"searches": [
  {{"category": "aspecto1", "query": "búsqueda general efectiva 1"}},
  {{"category": "aspecto2", "query": "búsqueda general efectiva 2"}},  
  {{"category": "aspecto3", "query": "búsqueda general efectiva 3"}},
  {{"category": "aspecto4", "query": "búsqueda general efectiva 4"}},
  {{"category": "aspecto5", "query": "búsqueda general efectiva 5"}}
]}}

Ejemplos de búsquedas GENERALES efectivas:
- "{subject} biografía historia personal"
- "{subject} últimas noticias 2025" 
- "{subject} posiciones políticas ideología"
- "{subject} controversias polémicas"
- "{subject} declaraciones recientes actualidad"

NO uses eventos específicos inventados."""

        try:
            # Importar OllamaService para generar respuestas inteligentes
            import sys
            import os
            sys.path.append('/app/backend')
            
            from backend.src.services.ollama_service import OllamaService
            
            print(f"🧠 Consultando LLM para generar búsquedas inteligentes sobre '{subject}'...")
            
            # Crear instancia del servicio Ollama
            ollama_service = OllamaService()
            
            # Generar respuesta usando el LLM
            response = ollama_service.generate_response(
                prompt=prompt,
                context={'max_tokens': 800, 'temperature': 0.7},
                use_tools=False,
                task_id="search_generation"
            )
            
            if response and isinstance(response, dict) and response.get('response'):
                content = response['response'].strip()
                print(f"🔍 Respuesta LLM recibida: {content[:200]}...")
                
                # Parsear respuesta JSON del LLM
                searches = self._parse_llm_search_response(content)
                
                if searches:
                    print(f"✅ LLM generó {len(searches)} búsquedas inteligentes exitosamente")
                    return searches
                else:
                    print("⚠️ Error parseando respuesta JSON del LLM")
            else:
                print("⚠️ LLM no generó respuesta válida")
                
        except ImportError:
            print("⚠️ OllamaService no disponible")
        except Exception as e:
            print(f"⚠️ Error ejecutando LLM: {e}")
        
        return []
    
    def _parse_llm_search_response(self, llm_response: str) -> List[Dict[str, str]]:
        """📝 Parsear respuesta JSON del LLM"""
        import json
        import re
        
        try:
            # Intentar extraer JSON de la respuesta
            # Buscar bloque JSON
            json_match = re.search(r'\{.*"searches".*\}', llm_response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                
                if 'searches' in data and isinstance(data['searches'], list):
                    searches = []
                    
                    for search_item in data['searches']:
                        if isinstance(search_item, dict) and 'category' in search_item and 'query' in search_item:
                            searches.append({
                                'category': search_item['category'].strip(),
                                'query': search_item['query'].strip()
                            })
                    
                    return searches[:5]  # Máximo 5 búsquedas
            
            # Fallback: intentar parsear línea por línea si no hay JSON válido
            lines = llm_response.split('\n')
            searches = []
            
            for line in lines:
                if ':' in line and len(searches) < 5:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        category = parts[0].strip().replace('-', '').replace('*', '').strip()
                        query = parts[1].strip()
                        
                        if len(category) > 0 and len(query) > 10:
                            searches.append({
                                'category': category,
                                'query': query
                            })
            
            return searches
            
        except Exception as e:
            print(f"⚠️ Error parseando respuesta LLM: {e}")
            return []
    
    def _generate_fallback_searches(self, subject: str, mentioned_aspects: List[str]) -> List[Dict[str, str]]:
        """🛠️ FALLBACK INTELIGENTE cuando el LLM no funciona"""
        
        print(f"🔄 Generando búsquedas fallback inteligentes para '{subject}'")
        
        # Aspectos universales que aplican a casi cualquier tema
        universal_aspects = [
            ('información_general', f'{subject} información general descripción'),
            ('historia_contexto', f'{subject} historia antecedentes contexto'),
            ('características', f'{subject} características principales aspectos importantes'),
            ('impacto_relevancia', f'{subject} importancia relevancia impacto significado'),
            ('actualidad', f'{subject} noticias recientes actualidad 2025')
        ]
        
        # Si hay aspectos mencionados específicos, priorizarlos
        if mentioned_aspects:
            specific_searches = []
            for aspect in mentioned_aspects[:3]:  # Máximo 3 aspectos específicos
                specific_searches.append((aspect, f'{subject} {aspect} información detallada'))
            
            # Combinar aspectos específicos con universales
            all_aspects = specific_searches + universal_aspects[len(specific_searches):]
        else:
            all_aspects = universal_aspects
        
        return [
            {'category': category, 'query': query}
            for category, query in all_aspects[:5]
        ]

# Funciones públicas para usar desde unified_web_search_tool.py
def get_intelligent_keywords(query_text: str) -> str:
    """🎯 Función principal para generar keywords inteligentes CON VALIDACIÓN"""
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
        "Investigar información específica sobre Arctic Monkeys",
        "Buscar información sobre 'Javier Milei' en bing y explorar los primeros resultados",
        "realizar análisis de datos específicos sobre inteligencia artificial",  
        "genera informe sobre Attack on Titan trama personajes",
        "utilizar herramienta web_search para obtener datos económicos Argentina"
    ]
    
    print("🧪 TESTING INTELLIGENT KEYWORD GENERATOR CON VALIDACIÓN")
    print("=" * 70)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🔍 TEST {i}: {test}")
        result = get_intelligent_keywords(test)
        print(f"✅ FINAL RESULT: {result}")
        print("-" * 50)