"""
Suite de Pruebas para el Agente Mitosis Mejorado
Valida el funcionamiento de todos los componentes integrados
"""

import unittest
import tempfile
import os
import time
import json
from unittest.mock import Mock, patch, MagicMock

# Importar componentes del agente
from model_manager import ModelManager, UnifiedModel, ModelProvider
from memory_manager import MemoryManager, Message, TaskMemory, KnowledgeItem
from task_manager import TaskManager, Task, TaskPhase, TaskStatus
from enhanced_prompts import EnhancedPromptManager, PromptType
from agent_core import MitosisAgent, AgentConfig, AgentState

class TestModelManager(unittest.TestCase):
    """Pruebas para el gestor de modelos"""
    
    def setUp(self):
        self.model_manager = ModelManager()
    
    def test_model_manager_initialization(self):
        """Prueba la inicialización del gestor de modelos"""
        self.assertIsNotNone(self.model_manager.ollama_service)
        self.assertIsNotNone(self.model_manager.openrouter_service)
        self.assertEqual(len(self.model_manager.unified_models), 0)
    
    @patch('ollama_service.OllamaService.is_available')
    @patch('ollama_service.OllamaService.detect_models')
    def test_refresh_models_ollama(self, mock_detect, mock_available):
        """Prueba la actualización de modelos de Ollama"""
        # Simular Ollama disponible con modelos
        mock_available.return_value = True
        mock_detect.return_value = [
            Mock(name="llama2", size=4000000000),
            Mock(name="codellama", size=7000000000)
        ]
        
        success = self.model_manager.refresh_models()
        
        self.assertTrue(success)
        self.assertGreater(len(self.model_manager.unified_models), 0)
        
        # Verificar que los modelos tienen el prefijo correcto
        ollama_models = [m for m in self.model_manager.unified_models if m.provider == ModelProvider.OLLAMA]
        self.assertGreater(len(ollama_models), 0)
        self.assertTrue(all(m.id.startswith("ollama:") for m in ollama_models))
    
    def test_select_best_model_preferences(self):
        """Prueba la selección de modelos con preferencias"""
        # Añadir modelos simulados
        local_model = UnifiedModel(
            id="ollama:llama2",
            name="llama2",
            provider=ModelProvider.OLLAMA,
            cost_per_1k_tokens=0.0,
            capabilities=["general"]
        )
        
        remote_model = UnifiedModel(
            id="openrouter:gpt-3.5-turbo",
            name="GPT-3.5 Turbo",
            provider=ModelProvider.OPENROUTER,
            cost_per_1k_tokens=0.002,
            capabilities=["general"]
        )
        
        self.model_manager.unified_models = [local_model, remote_model]
        
        # Probar preferencia por modelos locales
        self.model_manager.prefer_local = True
        selected = self.model_manager.select_best_model("general")
        self.assertEqual(selected.provider, ModelProvider.OLLAMA)
        
        # Probar sin preferencia local
        self.model_manager.prefer_local = False
        selected = self.model_manager.select_best_model("general")
        # Debería seleccionar el más barato (local en este caso)
        self.assertEqual(selected.provider, ModelProvider.OLLAMA)

class TestMemoryManager(unittest.TestCase):
    """Pruebas para el gestor de memoria"""
    
    def setUp(self):
        # Usar base de datos temporal
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.memory_manager = MemoryManager(db_path=self.temp_db.name)
    
    def tearDown(self):
        # Limpiar base de datos temporal
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_add_message_to_short_term(self):
        """Prueba añadir mensajes a la memoria a corto plazo"""
        message = self.memory_manager.add_message("user", "Hola, ¿cómo estás?")
        
        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Hola, ¿cómo estás?")
        self.assertEqual(len(self.memory_manager.short_term_memory), 1)
    
    def test_conversation_context_generation(self):
        """Prueba la generación de contexto de conversación"""
        # Añadir varios mensajes
        self.memory_manager.add_message("user", "Hola")
        self.memory_manager.add_message("assistant", "¡Hola! ¿En qué puedo ayudarte?")
        self.memory_manager.add_message("user", "Necesito ayuda con Python")
        
        context = self.memory_manager.get_conversation_context(max_tokens=1000)
        
        self.assertIn("user: Hola", context)
        self.assertIn("assistant: ¡Hola!", context)
        self.assertIn("user: Necesito ayuda con Python", context)
    
    def test_knowledge_base_operations(self):
        """Prueba las operaciones de la base de conocimientos"""
        # Añadir conocimiento
        knowledge_id = self.memory_manager.add_knowledge(
            content="Python es un lenguaje de programación",
            category="programming",
            source="test",
            confidence=0.9,
            tags=["python", "programming"]
        )
        
        self.assertIsNotNone(knowledge_id)
        
        # Buscar conocimiento
        results = self.memory_manager.search_knowledge("Python")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Python es un lenguaje de programación")
    
    def test_task_memory_persistence(self):
        """Prueba la persistencia de memoria de tareas"""
        task_memory = TaskMemory(
            task_id="test-task",
            title="Tarea de prueba",
            description="Una tarea para testing",
            status="active",
            created_at=time.time(),
            updated_at=time.time(),
            phases=[{"id": 1, "title": "Fase 1"}]
        )
        
        # Guardar tarea
        self.memory_manager.save_task_memory(task_memory)
        
        # Recuperar tarea
        retrieved = self.memory_manager.get_task_memory("test-task")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, "Tarea de prueba")

class TestTaskManager(unittest.TestCase):
    """Pruebas para el gestor de tareas"""
    
    def setUp(self):
        # Crear gestor de memoria temporal
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.memory_manager = MemoryManager(db_path=self.temp_db.name)
        self.task_manager = TaskManager(self.memory_manager)
    
    def tearDown(self):
        # Detener monitoreo y limpiar
        self.task_manager._stop_monitoring_thread()
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_create_task(self):
        """Prueba la creación de tareas"""
        phases = [
            {"id": 1, "title": "Análisis", "required_capabilities": ["analysis"]},
            {"id": 2, "title": "Implementación", "required_capabilities": ["coding"]}
        ]
        
        task_id = self.task_manager.create_task(
            title="Tarea de prueba",
            description="Una tarea para testing",
            goal="Completar las pruebas",
            phases=phases
        )
        
        self.assertIsNotNone(task_id)
        self.assertIn(task_id, self.task_manager.active_tasks)
        
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.title, "Tarea de prueba")
        self.assertEqual(len(task.phases), 2)
    
    def test_task_lifecycle(self):
        """Prueba el ciclo de vida completo de una tarea"""
        phases = [
            {"id": 1, "title": "Fase 1", "required_capabilities": ["general"]},
            {"id": 2, "title": "Fase 2", "required_capabilities": ["general"]}
        ]
        
        # Crear tarea
        task_id = self.task_manager.create_task(
            title="Tarea de ciclo de vida",
            description="Prueba del ciclo completo",
            goal="Validar el flujo de trabajo",
            phases=phases
        )
        
        # Iniciar tarea
        success = self.task_manager.start_task(task_id)
        self.assertTrue(success)
        
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.status, TaskStatus.ACTIVE)
        self.assertEqual(task.current_phase_id, 1)
        
        # Avanzar fase
        success = self.task_manager.advance_phase(task_id, 1, 2, {"result": "Fase 1 completada"})
        self.assertTrue(success)
        
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.current_phase_id, 2)
        
        # Completar tarea
        success = self.task_manager.complete_task(task_id, {"final_result": "Tarea completada"})
        self.assertTrue(success)
        
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.status, TaskStatus.COMPLETED)
    
    def test_task_progress_tracking(self):
        """Prueba el seguimiento del progreso de tareas"""
        phases = [
            {"id": 1, "title": "Fase 1", "required_capabilities": ["general"]},
            {"id": 2, "title": "Fase 2", "required_capabilities": ["general"]},
            {"id": 3, "title": "Fase 3", "required_capabilities": ["general"]}
        ]
        
        task_id = self.task_manager.create_task(
            title="Tarea de progreso",
            description="Prueba de seguimiento",
            goal="Validar el progreso",
            phases=phases
        )
        
        self.task_manager.start_task(task_id)
        
        # Verificar progreso inicial
        progress = self.task_manager.get_task_progress(task_id)
        self.assertEqual(progress["progress_percentage"], 0.0)
        self.assertEqual(progress["total_phases"], 3)
        
        # Avanzar una fase
        self.task_manager.advance_phase(task_id, 1, 2)
        progress = self.task_manager.get_task_progress(task_id)
        self.assertAlmostEqual(progress["progress_percentage"], 33.33, places=1)

class TestEnhancedPromptManager(unittest.TestCase):
    """Pruebas para el gestor de prompts mejorado"""
    
    def setUp(self):
        # Crear dependencias simuladas
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.memory_manager = MemoryManager(db_path=self.temp_db.name)
        self.task_manager = TaskManager(self.memory_manager)
        self.prompt_manager = EnhancedPromptManager(self.memory_manager, self.task_manager)
    
    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_template_loading(self):
        """Prueba la carga de plantillas por defecto"""
        templates = self.prompt_manager.list_templates()
        
        # Verificar que se cargaron las plantillas esperadas
        expected_templates = [
            "main_system", "task_planning", "phase_execution",
            "tool_selection", "reflection", "error_handling", "user_interaction"
        ]
        
        for template_name in expected_templates:
            self.assertIn(template_name, templates)
    
    def test_system_prompt_generation(self):
        """Prueba la generación del prompt del sistema"""
        # Añadir algunos mensajes a la memoria
        self.memory_manager.add_message("user", "Hola")
        self.memory_manager.add_message("assistant", "¡Hola! ¿En qué puedo ayudarte?")
        
        prompt = self.prompt_manager.generate_system_prompt(
            context="El usuario solicita ayuda"
        )
        
        self.assertIsInstance(prompt, str)
        self.assertIn("Manus", prompt)
        self.assertIn("El usuario solicita ayuda", prompt)
    
    def test_task_planning_prompt(self):
        """Prueba la generación de prompts de planificación"""
        prompt = self.prompt_manager.generate_task_planning_prompt(
            goal="Crear una aplicación web",
            description="Desarrollar una aplicación web simple con Flask",
            context="El usuario quiere aprender desarrollo web"
        )
        
        self.assertIsInstance(prompt, str)
        self.assertIn("Crear una aplicación web", prompt)
        self.assertIn("Flask", prompt)
        self.assertIn("JSON", prompt)  # Debe incluir formato de respuesta
    
    def test_prompt_optimization(self):
        """Prueba la optimización de longitud de prompts"""
        # Crear un prompt muy largo
        long_prompt = "INSTRUCCIONES: " + "A" * 20000  # Muy largo
        
        optimized = self.prompt_manager.optimize_prompt_length(long_prompt, max_tokens=1000)
        
        # Verificar que se redujo la longitud
        self.assertLess(len(optimized), len(long_prompt))
        self.assertIn("INSTRUCCIONES", optimized)  # Debe mantener partes importantes

class TestMitosisAgent(unittest.TestCase):
    """Pruebas para el agente Mitosis completo"""
    
    def setUp(self):
        # Configuración de prueba
        self.config = AgentConfig(
            memory_db_path=tempfile.NamedTemporaryFile(delete=False, suffix='.db').name,
            debug_mode=True,
            log_level="DEBUG"
        )
        
        # Crear agente con mocks para evitar dependencias externas
        with patch('model_manager.ModelManager.refresh_models'):
            self.agent = MitosisAgent(self.config)
    
    def tearDown(self):
        # Limpiar
        self.agent.shutdown()
        if os.path.exists(self.config.memory_db_path):
            os.unlink(self.config.memory_db_path)
    
    def test_agent_initialization(self):
        """Prueba la inicialización del agente"""
        self.assertEqual(self.agent.state, AgentState.IDLE)
        self.assertIsNotNone(self.agent.memory_manager)
        self.assertIsNotNone(self.agent.task_manager)
        self.assertIsNotNone(self.agent.model_manager)
        self.assertIsNotNone(self.agent.prompt_manager)
    
    def test_session_management(self):
        """Prueba la gestión de sesiones"""
        session_id = self.agent.start_session()
        
        self.assertIsNotNone(session_id)
        self.assertEqual(self.agent.current_session_id, session_id)
        
        # Verificar que se añadió mensaje de inicio
        messages = self.agent.memory_manager.get_recent_messages()
        self.assertGreater(len(messages), 0)
        self.assertEqual(messages[0].role, "system")
    
    @patch('model_manager.ModelManager.select_best_model')
    @patch('model_manager.ModelManager.load_model')
    @patch('model_manager.ModelManager.chat_completion')
    def test_process_user_message(self, mock_chat, mock_load, mock_select):
        """Prueba el procesamiento de mensajes del usuario"""
        # Configurar mocks
        mock_model = UnifiedModel(
            id="test:model",
            name="Test Model",
            provider=ModelProvider.OLLAMA
        )
        mock_select.return_value = mock_model
        mock_load.return_value = True
        mock_chat.return_value = "¡Hola! ¿En qué puedo ayudarte?"
        
        # Procesar mensaje
        response = self.agent.process_user_message("Hola, ¿cómo estás?")
        
        self.assertIsInstance(response, str)
        self.assertIn("Hola", response)
        
        # Verificar que se llamaron los métodos esperados
        mock_select.assert_called_once()
        mock_load.assert_called_once()
        mock_chat.assert_called_once()
    
    def test_agent_status(self):
        """Prueba la obtención del estado del agente"""
        status = self.agent.get_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn("agent_name", status)
        self.assertIn("state", status)
        self.assertIn("statistics", status)
        self.assertIn("memory_stats", status)
        self.assertIn("task_manager_status", status)

class TestIntegration(unittest.TestCase):
    """Pruebas de integración entre componentes"""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Crear componentes integrados
        self.memory_manager = MemoryManager(db_path=self.temp_db.name)
        self.task_manager = TaskManager(self.memory_manager)
        self.model_manager = ModelManager()
        self.prompt_manager = EnhancedPromptManager(self.memory_manager, self.task_manager)
    
    def tearDown(self):
        self.task_manager._stop_monitoring_thread()
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_memory_task_integration(self):
        """Prueba la integración entre memoria y gestión de tareas"""
        # Crear tarea
        phases = [{"id": 1, "title": "Test Phase", "required_capabilities": ["general"]}]
        task_id = self.task_manager.create_task(
            title="Integration Test",
            description="Test integration",
            goal="Validate integration",
            phases=phases
        )
        
        # Verificar que se guardó en memoria
        task_memory = self.memory_manager.get_task_memory(task_id)
        self.assertIsNotNone(task_memory)
        self.assertEqual(task_memory.title, "Integration Test")
    
    def test_prompt_context_integration(self):
        """Prueba la integración de contexto en prompts"""
        # Añadir mensajes a memoria
        self.memory_manager.add_message("user", "¿Puedes ayudarme?")
        self.memory_manager.add_message("assistant", "¡Por supuesto!")
        
        # Crear tarea
        phases = [{"id": 1, "title": "Help Phase", "required_capabilities": ["general"]}]
        task_id = self.task_manager.create_task(
            title="Help Task",
            description="Help the user",
            goal="Provide assistance",
            phases=phases
        )
        self.task_manager.start_task(task_id)
        
        # Generar prompt del sistema
        system_prompt = self.prompt_manager.generate_system_prompt()
        
        # Verificar que incluye contexto de memoria y tarea
        self.assertIn("¿Puedes ayudarme?", system_prompt)
        self.assertIn("Help Task", system_prompt)

def run_performance_tests():
    """Ejecuta pruebas de rendimiento básicas"""
    print("\n🚀 Ejecutando pruebas de rendimiento...")
    
    # Prueba de rendimiento de memoria
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        memory_manager = MemoryManager(db_path=temp_db.name)
        
        # Medir tiempo de inserción de mensajes
        start_time = time.time()
        for i in range(1000):
            memory_manager.add_message("user", f"Mensaje de prueba {i}")
        insert_time = time.time() - start_time
        
        print(f"  ✅ Inserción de 1000 mensajes: {insert_time:.2f}s")
        
        # Medir tiempo de búsqueda
        memory_manager.add_knowledge(
            "Python es un lenguaje de programación",
            "programming",
            "test",
            0.9
        )
        
        start_time = time.time()
        for i in range(100):
            results = memory_manager.search_knowledge("Python")
        search_time = time.time() - start_time
        
        print(f"  ✅ 100 búsquedas en conocimiento: {search_time:.2f}s")
        
    finally:
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)

def run_all_tests():
    """Ejecuta todas las pruebas"""
    print("🧪 Iniciando suite de pruebas del Agente Mitosis Mejorado\n")
    
    # Crear suite de pruebas
    test_suite = unittest.TestSuite()
    
    # Añadir clases de prueba
    test_classes = [
        TestModelManager,
        TestMemoryManager,
        TestTaskManager,
        TestEnhancedPromptManager,
        TestMitosisAgent,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Ejecutar pruebas de rendimiento
    run_performance_tests()
    
    # Resumen
    print(f"\n📊 Resumen de pruebas:")
    print(f"  ✅ Pruebas exitosas: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  ❌ Pruebas fallidas: {len(result.failures)}")
    print(f"  🚨 Errores: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Fallos:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n🚨 Errores:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

