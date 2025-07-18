# 🛡️ CONFIGURACIÓN ROBUSTA PERMANENTE - MITOSIS

## ⚠️ ADVERTENCIA IMPORTANTE
**NUNCA modifiques directamente la configuración de supervisor o ejecutes `yarn start` en producción.**

## 🔧 SCRIPTS AUTOMÁTICOS DISPONIBLES

### 1. Deployment Robusto
```bash
/app/scripts/robust-deploy.sh
```
- Ejecuta SIEMPRE antes de hacer cambios
- Garantiza producción estable
- Auto-corrige configuraciones

### 2. Auto-Build
```bash
/app/scripts/auto-build.sh
```
- Construye automáticamente para producción
- Se ejecuta automáticamente en cada restart
- Detecta y corrige modo desarrollo

### 3. Monitoreo de Estabilidad
```bash
/app/scripts/stability-monitor.sh
```
- Monitorea constantemente el estado
- Auto-corrige si detecta desarrollo
- Logs detallados de estado

## 🚨 COMANDOS SEGUROS

### Para hacer cambios en el código:
```bash
# 1. Hacer cambios en el código
# 2. Ejecutar deployment robusto
/app/scripts/robust-deploy.sh
```

### Para verificar estado:
```bash
sudo supervisorctl status
```

### Para reiniciar servicios:
```bash
sudo supervisorctl restart all
```

## ❌ COMANDOS PROHIBIDOS EN PRODUCCIÓN

```bash
# ❌ NUNCA USAR ESTOS COMANDOS:
yarn start                    # Inicia modo desarrollo
npm start                     # Inicia modo desarrollo
vite                         # Servidor desarrollo
supervisorctl stop frontend  # Sin usar robust-deploy
```

## 🔍 VERIFICACIÓN DE ESTADO

### Frontend en Producción:
```bash
# Debe mostrar proceso "serve"
pgrep -f "serve.*dist"
```

### Backend Funcionando:
```bash
# Debe responder "healthy"
curl http://localhost:8001/health
```

## 🛠️ CONFIGURACIÓN DEFENSIVA

### package.json
- `npm start` ahora ejecuta producción automáticamente
- `npm run dev` claramente marcado como desarrollo
- `npm run production` para producción explícita

### Supervisor
- Frontend siempre ejecuta auto-build primero
- Monitoreo automático de estabilidad
- Auto-corrección sin intervención manual

## 📊 MONITOREO CONTINUO

El sistema incluye:
- ✅ Verificación cada 30 segundos
- ✅ Auto-corrección automática
- ✅ Logs detallados
- ✅ Alertas de estado
- ✅ Prevención de modo desarrollo

## 🎯 RESULTADO ESPERADO

- ✅ Sin reinicios constantes
- ✅ Estabilidad permanente
- ✅ Inmune a cambios accidentales
- ✅ Auto-corrección automática
- ✅ Performance optimizada