# PLAN DE LIMPIEZA DEL REPOSITORIO MITOSIS

## ANÁLISIS REALIZADO
- **Total de archivos encontrados**: 17,532
- **Archivos en directorio raíz**: ~150+
- **Categorías identificadas**: Testing, Demo, Documentación temporal, Scripts setup

## ARCHIVOS CORE QUE SE MANTIENEN (VERIFICADOS)
### ✅ Scripts Críticos
- `start_mitosis.sh` - Script principal de inicio (38 referencias encontradas)
- `/scripts/*` - Scripts de producción y monitoreo

### ✅ Bases de Datos
- `mitosis_memory.db` - Usado por memory_manager.py
- `unified_agent.db` - Usado por agent_unified.py

### ✅ Documentación Core
- `README.md` - Documentación principal
- `test_result.md` - Historial crítico del proyecto
- `.env` - Variables de entorno

### ✅ Aplicación Core
- `/backend/*` - Backend FastAPI
- `/frontend/*` - Frontend React
- `package.json`, `requirements.txt` - Dependencies

## FASE 1: ARCHIVOS DE TESTING TEMPORAL (SEGUROS)
### 🗑️ Archivos JSON de resultados de test (29 archivos)
```
autonomous_test_results.json
enhanced_mitosis_test_results.json
intention_classification_test_results.json
plan_action_test_results.json
test_results_icon_and_first_message.json
[... y 24 más]
```

### 🗑️ Archivos Python de testing (20+ archivos)
```
backend_test.py
mitosis_comprehensive_diagnostic.py
websocket_cors_test.py
autonomous_test.py
demo_agente_real_final.py
[... y 15+ más]
```

### 🗑️ Archivos HTML de demo (5 archivos)
```
demo_components.html
demo_fixes.html
test_chat_scroll.html
test_search.html
test_websocket.html
```

## CRITERIOS DE ELIMINACIÓN APLICADOS
1. **No referenciados** desde código funcional
2. **Solo aparecen** en otros archivos de test
3. **Archivos temporales** de desarrollo
4. **Demostraciones** y pruebas obsoletas
5. **Archivos con nombres** claramente temporales (test_, demo_, etc.)

## CRITERIOS DE PRESERVACIÓN
1. **Referenciado** desde aplicación core
2. **Mencionado** en start_mitosis.sh o test_result.md como importante
3. **Parte de dependencies** (package.json, requirements.txt)
4. **Archivos de configuración** (.env, configs)
5. **Documentación core** (README, docs principales)

## PRÓXIMAS FASES
- **FASE 2**: Documentación temporal y redundante
- **FASE 3**: Scripts de setup obsoletos (verificando dependencias)
- **FASE 4**: Archivos con errores de nombres (=*.*)