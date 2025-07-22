**PLAN DE ACCIÓN:**
1. Crear una aplicación cliente utilizando la biblioteca Socket.IO para JavaScript.
2. Configurar la conexión al servidor WebSocket mediante la función `io.connect()`.
3. Establecer un evento de conexión con el servidor mediante la función `on('connect')`.
4. Enviar un mensaje de prueba al servidor mediante la función `emit()` y recibir la respuesta en el cliente mediante la función `on('message')`.
5. Implementar una función para desconectar el cliente del servidor mediante la función `io.disconnect()`.
**Contenido detallado:**
Para conectar un cliente a través de WebSocket con Socket.IO, debemos seguir los siguientes pasos:
Primero, debemos crear una aplicación cliente utilizando la biblioteca Socket.IO para JavaScript. Esto se puede hacer mediante el siguiente código: