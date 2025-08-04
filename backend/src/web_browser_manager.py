"""
Web Browser Manager with browser-use Integration for Real-time Web Navigation Tracking
Implements browser-use Agent for intelligent browser automation with real-time event capture

🔄 REFACTORED FOR BROWSER-USE INTEGRATION
- Integrates browser-use Agent for AI-powered navigation
- Maintains backward compatibility with existing WebSocket events  
- Preserves screenshot functionality and real-time monitoring
- Uses MitosisOllamaChatModel for LLM integration
"""

import os
import sys
import time
import base64
import json
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from pathlib import Path

# browser-use imports
from browser_use import Agent
from browser_use.browser.session import BrowserSession
from browser_use.browser.profile import BrowserProfile

# Mitosis imports
try:
    from .adapters.mitosis_ollama_chat import MitosisOllamaChatModel
    from .services.ollama_service import OllamaService
except ImportError:
    # Fallback para cuando se importa directamente
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from adapters.mitosis_ollama_chat import MitosisOllamaChatModel
    from services.ollama_service import OllamaService

# Configure logging
logger = logging.getLogger(__name__)

class WebBrowserManager:
    """
    🤖 AI-Powered Web Browser Manager using browser-use
    
    Features:
    - browser-use Agent for intelligent navigation
    - Real-time WebSocket event capture
    - Screenshot functionality preserved
    - Backward compatible API
    - Integration with Mitosis LLM stack
    """
    
    def __init__(
        self, 
        websocket_manager, 
        task_id: str, 
        ollama_service: Optional[OllamaService] = None,
        browser_type: str = "browser-use"
    ):
        """
        Initialize WebBrowserManager with browser-use integration
        
        Args:
            websocket_manager: WebSocketManager instance for real-time updates
            task_id: Task ID for event tracking
            ollama_service: OllamaService instance for LLM integration
            browser_type: 'browser-use' (new default) or 'playwright' (legacy)
        """
        self.websocket_manager = websocket_manager
        self.task_id = task_id
        self.browser_type = browser_type
        
        # browser-use components
        self.browser_use_agent: Optional[Agent] = None
        self.browser_session: Optional[BrowserSession] = None
        self.llm_model: Optional[MitosisOllamaChatModel] = None
        
        # Legacy Playwright/Selenium support
        self.browser = None
        self.page = None  # For Playwright fallback
        self.driver = None  # For Selenium fallback
        
        # State management
        self.is_initialized = False
        self.current_url = ""
        self.current_task = ""
        
        # Create screenshots directory
        self.screenshots_dir = Path(f"/tmp/screenshots/{task_id}")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize LLM model
        if ollama_service:
            self.llm_model = MitosisOllamaChatModel.create_from_mitosis_config(
                ollama_service=ollama_service,
                model="llama3.1:8b"
            )
        else:
            # Fallback: create new OllamaService
            self.llm_model = MitosisOllamaChatModel(
                model="llama3.1:8b",
                host="https://66bd0d09b557.ngrok-free.app"
            )
        
        logger.info(f"🤖 WebBrowserManager initialized for task {task_id} using {browser_type}")
        logger.info(f"🧠 LLM Model: {self.llm_model.name}")

    async def initialize_browser(self):
        """
        🚀 Initialize browser-use Agent with async support
        """
        try:
            if self.browser_type == "browser-use":
                await self._initialize_browser_use()
            elif self.browser_type == "playwright":
                self._initialize_playwright_legacy()
            elif self.browser_type == "selenium":
                self._initialize_selenium_legacy()
            else:
                raise ValueError(f"Unsupported browser type: {self.browser_type}")
            
            self.is_initialized = True
            self.websocket_manager.send_log_message(
                self.task_id, 
                "info", 
                f"🤖 Navegador {self.browser_type} inicializado correctamente"
            )
            
            logger.info(f"✅ {self.browser_type} browser initialized successfully")
            
        except Exception as e:
            error_msg = f"❌ Error inicializando navegador {self.browser_type}: {str(e)}"
            logger.error(error_msg)
            self.websocket_manager.send_log_message(self.task_id, "error", error_msg)
            raise

    async def _initialize_browser_use(self):
        """
        🤖 Initialize browser-use Agent with Mitosis LLM integration
        """
        try:
            logger.info("🚀 Inicializando browser-use Agent...")
            
            # Create browser session
            self.browser_session = BrowserSession(
                headless=True,
                browser_profile=BrowserProfile(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
            )
            
            # Create Agent
            agent = Agent(
                task="Navegación web inteligente para el usuario",
                llm=self.llm_model,
                browser_session=self.browser_session,
                use_vision=True,  # Enable vision for better understanding
                max_failures=3,   # Resilience
                save_conversation_path=f"/tmp/browser_conversations/{self.task_id}.json"
            )
            
            # Create a wrapper to fix the max_steps issue
            class BrowserUseAgentWrapper:
                def __init__(self, agent):
                    self._agent = agent
                    
                async def run(self, task, max_steps=None, **kwargs):
                    """Wrapper run method that ensures max_steps is always an integer"""
                    # If max_steps is provided, ensure it's an integer
                    if max_steps is not None:
                        if isinstance(max_steps, str):
                            max_steps = int(max_steps)
                        elif not isinstance(max_steps, int):
                            max_steps = int(max_steps)
                    else:
                        max_steps = 3  # Default value as integer
                    
                    # Patch the agent's run method temporarily to fix the bug
                    original_run = self._agent.run
                    
                    async def patched_run(task_str, **run_kwargs):
                        # Force max_steps to be an integer in the actual call
                        run_kwargs['max_steps'] = max_steps
                        
                        # Call the original method without our wrapper parameters
                        return await original_run.__func__(self._agent, task_str, **run_kwargs)
                    
                    # Execute with the patched method
                    return await patched_run(task)
                
                def __getattr__(self, name):
                    """Delegate other attributes to the wrapped agent"""
                    return getattr(self._agent, name)
            
            # Wrap the agent to fix the max_steps bug
            self.browser_use_agent = BrowserUseAgentWrapper(agent)
            
            logger.info("✅ browser-use Agent inicializado exitosamente")
            
            # Send initialization event
            self.websocket_manager.send_browser_activity(
                self.task_id,
                "browser_initialized", 
                "", 
                "browser-use Agent", 
                ""
            )
            
        except Exception as e:
            logger.error(f"❌ Error inicializando browser-use Agent: {e}")
            raise

    def _initialize_playwright_legacy(self):
        """🔄 Legacy Playwright initialization (backward compatibility)"""
        try:
            from playwright.sync_api import sync_playwright
            
            self.playwright_instance = sync_playwright().start()
            self.browser = self.playwright_instance.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            self.page = self.browser.new_page()
            
            # Set user agent to avoid detection
            self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            # Setup event listeners for legacy mode
            self._setup_playwright_listeners()
            
            logger.info("✅ Legacy Playwright browser initialized successfully")
            
        except ImportError:
            raise ImportError("Playwright no está instalado. Use: pip install playwright && playwright install")
        except Exception as e:
            raise Exception(f"Error inicializando Playwright: {str(e)}")

    def _initialize_selenium_legacy(self):
        """🔄 Legacy Selenium initialization (backward compatibility)"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service as ChromeService
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-web-security')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            logger.info("✅ Legacy Selenium browser initialized successfully")
            
        except ImportError:
            raise ImportError("Selenium no está instalado. Use: pip install selenium webdriver-manager")
        except Exception as e:
            raise Exception(f"Error inicializando Selenium: {str(e)}")

    def _setup_playwright_listeners(self):
        """Setup Playwright event listeners for real-time tracking"""
        if not self.page:
            return
            
        # URL change listener
        def on_url_changed(url):
            self._on_url_changed(url)
            
        # Page load listener
        def on_page_loaded():
            self._on_page_loaded()
            
        # Request listener for network activity
        def on_request(request):
            self._on_request(request)
            
        # Response listener
        def on_response(response):
            self._on_response(response)
        
        # Setup listeners
        self.page.on("load", lambda: on_page_loaded())
        self.page.on("domcontentloaded", lambda: self._on_dom_ready())
        # Note: URL changes are tracked in navigate() method for better control

    def _on_url_changed(self, url: str):
        """Handle URL change event"""
        self.websocket_manager.send_browser_activity(
            self.task_id, 
            "url_changed", 
            url, 
            "", 
            ""
        )
        logger.info(f"🔄 URL changed: {url}")

    def _on_page_loaded(self):
        """Handle page load event"""
        current_url = self.get_current_url()
        title = self.get_page_title()
        screenshot_path = self._take_screenshot()
        
        self.websocket_manager.send_browser_activity(
            self.task_id, 
            "page_loaded", 
            current_url, 
            title, 
            screenshot_path
        )
        
        self.websocket_manager.send_log_message(
            self.task_id, 
            "info", 
            f"📄 Página cargada: {title} ({current_url})"
        )
        
        logger.info(f"✅ Page loaded: {title} - {current_url}")

    def _on_dom_ready(self):
        """Handle DOM content loaded event"""
        current_url = self.get_current_url()
        self.websocket_manager.send_log_message(
            self.task_id, 
            "info", 
            f"🔧 DOM listo: {current_url}"
        )

    def _on_request(self, request):
        """Handle network request event"""
        if request.resource_type in ['document', 'xhr', 'fetch']:
            self.websocket_manager.send_log_message(
                self.task_id, 
                "debug", 
                f"📡 Request: {request.method} {request.url}"
            )

    def _on_response(self, response):
        """Handle network response event"""
        if response.request.resource_type in ['document', 'xhr', 'fetch']:
            self.websocket_manager.send_log_message(
                self.task_id, 
                "debug", 
                f"📨 Response: {response.status} {response.url}"
            )

    # ========================================================================
    # NAVEGACIÓN PRINCIPAL CON BROWSER-USE AGENT
    # ========================================================================

    async def navigate(self, url: str, task_description: str = None):
        """
        🤖 Navigate to URL using browser-use Agent with AI intelligence
        
        Args:
            url: URL to navigate to
            task_description: Optional task description for context
        """
        if not self.is_initialized:
            raise RuntimeError("Browser not initialized. Call initialize_browser() first.")
        
        try:
            logger.info(f"🚀 Navegando a {url} con browser-use Agent...")
            
            self.current_url = url
            self.current_task = task_description or f"Navegar a {url}"
            
            # Send navigation start event
            self.websocket_manager.send_browser_activity(
                self.task_id,
                "navigation_started", 
                url, 
                "Iniciando navegación inteligente", 
                ""
            )
            
            self.websocket_manager.send_log_message(
                self.task_id, 
                "info", 
                f"🤖 Iniciando navegación inteligente a: {url}"
            )
            
            if self.browser_type == "browser-use":
                # Use browser-use Agent for intelligent navigation
                navigation_task = f"Navigate to {url}"
                if task_description:
                    navigation_task += f" and {task_description}"
                
                # Execute task with browser-use Agent with explicit max_steps
                try:
                    result = await self.browser_use_agent.run(navigation_task, max_steps=3)
                except TypeError as te:
                    # Fallback if max_steps is already configured elsewhere
                    logger.warning(f"browser-use max_steps conflict, using default: {te}")
                    result = await self.browser_use_agent.run(navigation_task)
                
                # Get current page info after navigation
                current_url = await self._get_current_url_async()
                page_title = await self._get_page_title_async()
                screenshot_path = await self._take_screenshot_async()
                
                # Send completion event
                self.websocket_manager.send_browser_activity(
                    self.task_id,
                    "navigation_completed", 
                    current_url, 
                    page_title, 
                    screenshot_path
                )
                
                self.websocket_manager.send_log_message(
                    self.task_id, 
                    "info", 
                    f"✅ Navegación completada: {page_title} ({current_url})"
                )
                
                return result
                
            else:
                # Fallback to legacy navigation
                return self._navigate_legacy(url)
            
        except Exception as e:
            error_msg = f"❌ Error navegando a {url}: {str(e)}"
            logger.error(error_msg)
            self.websocket_manager.send_log_message(self.task_id, "error", error_msg)
            raise

    async def click_element(self, selector: str, description: str = None):
        """
        🤖 Click element using browser-use Agent with AI understanding
        
        Args:
            selector: CSS selector or description of element to click
            description: Human-readable description for better AI understanding
        """
        try:
            logger.info(f"🖱️ Haciendo click con browser-use Agent: {selector}")
            
            if self.browser_type == "browser-use":
                # Use AI to understand and click element
                click_task = f"Click on the element with selector '{selector}'"
                if description:
                    click_task += f" which is described as: {description}"
                
                # Send click start event
                self.websocket_manager.send_browser_activity(
                    self.task_id,
                    "click_started", 
                    await self._get_current_url_async(), 
                    f"Clicking: {description or selector}", 
                    ""
                )
                
                self.websocket_manager.send_log_message(
                    self.task_id, 
                    "info", 
                    f"🖱️ Haciendo click inteligente: {description or selector}"
                )
                
                # Execute click with browser-use Agent
                result = await self.browser_use_agent.run(click_task)
                
                # Get updated page info after click
                current_url = await self._get_current_url_async()
                page_title = await self._get_page_title_async()
                screenshot_path = await self._take_screenshot_async()
                
                # Send completion event
                self.websocket_manager.send_browser_activity(
                    self.task_id,
                    "click_completed", 
                    current_url, 
                    page_title, 
                    screenshot_path
                )
                
                self.websocket_manager.send_log_message(
                    self.task_id, 
                    "info", 
                    f"✅ Click completado: {description or selector}"
                )
                
                return result
                
            else:
                # Fallback to legacy click
                return self._click_element_legacy(selector)
            
        except Exception as e:
            error_msg = f"❌ Error haciendo click en {selector}: {str(e)}"
            logger.error(error_msg)
            self.websocket_manager.send_log_message(self.task_id, "error", error_msg)
            raise

    async def type_text(self, selector: str, text: str, description: str = None):
        """
        🤖 Type text using browser-use Agent with AI understanding
        
        Args:
            selector: CSS selector or description of input field
            text: Text to type
            description: Human-readable description for better AI understanding  
        """
        try:
            logger.info(f"⌨️ Escribiendo texto con browser-use Agent: {selector}")
            
            if self.browser_type == "browser-use":
                # Use AI to understand and type in element
                type_task = f"Type the text '{text}' into the element with selector '{selector}'"
                if description:
                    type_task += f" which is described as: {description}"
                
                # Send typing start event
                self.websocket_manager.send_browser_activity(
                    self.task_id,
                    "typing_started", 
                    await self._get_current_url_async(), 
                    f"Typing in: {description or selector}", 
                    ""
                )
                
                self.websocket_manager.send_log_message(
                    self.task_id, 
                    "info", 
                    f"⌨️ Escribiendo texto inteligente: {text[:50]}... en {description or selector}"
                )
                
                # Execute typing with browser-use Agent
                result = await self.browser_use_agent.run(type_task)
                
                # Get updated page info after typing
                current_url = await self._get_current_url_async()
                page_title = await self._get_page_title_async()
                screenshot_path = await self._take_screenshot_async()
                
                # Send completion event
                self.websocket_manager.send_browser_activity(
                    self.task_id,
                    "typing_completed", 
                    current_url, 
                    page_title, 
                    screenshot_path
                )
                
                self.websocket_manager.send_log_message(
                    self.task_id, 
                    "info", 
                    f"✅ Texto introducido: {text[:50]}... en {description or selector}"
                )
                
                return result
                
            else:
                # Fallback to legacy typing
                return self._type_text_legacy(selector, text)
            
        except Exception as e:
            error_msg = f"❌ Error escribiendo en {selector}: {str(e)}"
            logger.error(error_msg)
            self.websocket_manager.send_log_message(self.task_id, "error", error_msg)
            raise

    async def extract_data(self, task_description: str) -> Dict[str, Any]:
        """
        🤖 Extract data from current page using browser-use Agent intelligence
        
        Args:
            task_description: Description of what data to extract
            
        Returns:
            Dict containing extracted data
        """
        try:
            logger.info(f"🔍 Extrayendo datos con browser-use Agent: {task_description}")
            
            if self.browser_type == "browser-use":
                # Use AI to extract data intelligently
                extract_task = f"Extract data from the current page: {task_description}"
                
                # Send extraction start event
                self.websocket_manager.send_browser_activity(
                    self.task_id,
                    "extraction_started", 
                    await self._get_current_url_async(), 
                    f"Extracting: {task_description}", 
                    ""
                )
                
                self.websocket_manager.send_log_message(
                    self.task_id, 
                    "info", 
                    f"🔍 Extrayendo datos: {task_description}"
                )
                
                # Execute extraction with browser-use Agent with explicit max_steps
                try:
                    result = await self.browser_use_agent.run(extract_task, max_steps=2)
                except TypeError as te:
                    # Fallback if max_steps is already configured elsewhere
                    logger.warning(f"browser-use max_steps conflict in extract_data, using default: {te}")
                    result = await self.browser_use_agent.run(extract_task)
                
                # Process result into structured data
                extracted_data = {
                    "task": task_description,
                    "url": await self._get_current_url_async(),
                    "timestamp": datetime.now().isoformat(),
                    "result": result,
                    "success": True
                }
                
                # Send completion event
                screenshot_path = await self._take_screenshot_async()
                self.websocket_manager.send_browser_activity(
                    self.task_id,
                    "extraction_completed", 
                    extracted_data["url"], 
                    f"Data extracted: {task_description}", 
                    screenshot_path
                )
                
                self.websocket_manager.send_log_message(
                    self.task_id, 
                    "info", 
                    f"✅ Datos extraídos exitosamente: {task_description}"
                )
                
                return extracted_data
                
            else:
                # Fallback to legacy extraction (basic)
                return self._extract_data_legacy(task_description)
            
        except Exception as e:
            error_msg = f"❌ Error extrayendo datos: {str(e)}"
            logger.error(error_msg)
            self.websocket_manager.send_log_message(self.task_id, "error", error_msg)
            return {
                "task": task_description,
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }

    async def perform_complex_task(self, task_description: str) -> Dict[str, Any]:
        """
        🤖 Perform complex multi-step browser task using browser-use Agent
        
        Args:
            task_description: Natural language description of the task to perform
            
        Returns:
            Dict containing task results
        """
        try:
            logger.info(f"🎯 Ejecutando tarea compleja: {task_description}")
            
            if self.browser_type == "browser-use":
                # Send task start event
                self.websocket_manager.send_browser_activity(
                    self.task_id,
                    "complex_task_started", 
                    await self._get_current_url_async(), 
                    f"Starting: {task_description}", 
                    ""
                )
                
                self.websocket_manager.send_log_message(
                    self.task_id, 
                    "info", 
                    f"🎯 Iniciando tarea compleja: {task_description}"
                )
                
                # Execute complex task with browser-use Agent
                result = await self.browser_use_agent.run(task_description)
                
                # Get final page info
                current_url = await self._get_current_url_async()
                page_title = await self._get_page_title_async()
                screenshot_path = await self._take_screenshot_async()
                
                # Process result
                task_result = {
                    "task": task_description,
                    "url": current_url,
                    "title": page_title,
                    "timestamp": datetime.now().isoformat(),
                    "result": result,
                    "success": True
                }
                
                # Send completion event
                self.websocket_manager.send_browser_activity(
                    self.task_id,
                    "complex_task_completed", 
                    current_url, 
                    page_title, 
                    screenshot_path
                )
                
                self.websocket_manager.send_log_message(
                    self.task_id, 
                    "info", 
                    f"✅ Tarea compleja completada: {task_description}"
                )
                
                return task_result
                
            else:
                # No fallback for complex tasks - require browser-use
                raise RuntimeError("Complex tasks require browser-use Agent. Please use browser_type='browser-use'")
            
        except Exception as e:
            error_msg = f"❌ Error ejecutando tarea compleja: {str(e)}"
            logger.error(error_msg)
            self.websocket_manager.send_log_message(self.task_id, "error", error_msg)
            return {
                "task": task_description,
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }

    # ========================================================================
    # MÉTODOS AUXILIARES PARA BROWSER-USE
    # ========================================================================

    async def _get_current_url_async(self) -> str:
        """Get current URL async for browser-use"""
        try:
            if self.browser_use_agent and hasattr(self.browser_use_agent, 'browser_session'):
                # Try to get URL from browser-use session
                if hasattr(self.browser_use_agent.browser_session, 'page'):
                    page = self.browser_use_agent.browser_session.page
                    if page:
                        return page.url
            return self.current_url
        except Exception as e:
            logger.warning(f"Could not get current URL: {e}")
            return self.current_url or ""

    async def _get_page_title_async(self) -> str:
        """Get page title async for browser-use"""
        try:
            if self.browser_use_agent and hasattr(self.browser_use_agent, 'browser_session'):
                if hasattr(self.browser_use_agent.browser_session, 'page'):
                    page = self.browser_use_agent.browser_session.page
                    if page:
                        return await page.title()
            return "Página sin título"
        except Exception as e:
            logger.warning(f"Could not get page title: {e}")
            return "Página sin título"

    async def _take_screenshot_async(self) -> str:
        """Take screenshot async for browser-use"""
        try:
            if self.browser_use_agent and hasattr(self.browser_use_agent, 'browser_session'):
                if hasattr(self.browser_use_agent.browser_session, 'page'):
                    page = self.browser_use_agent.browser_session.page
                    if page:
                        timestamp = int(time.time() * 1000)
                        filename = f"browser_use_screenshot_{timestamp}.png"
                        screenshot_path = self.screenshots_dir / filename
                        
                        await page.screenshot(path=str(screenshot_path), quality=20, full_page=False)
                        
                        # Return relative URL for frontend access
                        return f"/api/files/screenshots/{self.task_id}/{filename}"
            return ""
        except Exception as e:
            logger.warning(f"Could not take screenshot: {e}")
            return ""

    # ========================================================================
    # MÉTODOS LEGACY PARA BACKWARD COMPATIBILITY
    # ========================================================================

    def _navigate_legacy(self, url: str, wait_for_load: bool = True):
        """Legacy navigation for Playwright/Selenium"""
        self._on_url_changed(url)
        
        if self.browser_type == "playwright":
            self.page.goto(url, wait_until='networkidle' if wait_for_load else 'commit')
        elif self.browser_type == "selenium":
            self.driver.get(url)
            if wait_for_load:
                time.sleep(2)
            
            # Manual event triggering for Selenium
            current_url = self.driver.current_url
            title = self.driver.title
            screenshot_path = self._take_screenshot()
            
            self.websocket_manager.send_browser_activity(
                self.task_id, 
                "page_loaded", 
                current_url, 
                title, 
                screenshot_path
            )

    def _click_element_legacy(self, selector: str):
        """Legacy click for Playwright/Selenium"""
        if self.browser_type == "playwright":
            self.page.click(selector)
        elif self.browser_type == "selenium":
            from selenium.webdriver.common.by import By
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            element.click()
        
        self.websocket_manager.send_browser_activity(
            self.task_id, 
            "click", 
            self.get_current_url(), 
            f"Click en: {selector}", 
            ""
        )

    def _type_text_legacy(self, selector: str, text: str):
        """Legacy typing for Playwright/Selenium"""
        if self.browser_type == "playwright":
            self.page.fill(selector, text)
        elif self.browser_type == "selenium":
            from selenium.webdriver.common.by import By
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            element.clear()
            element.send_keys(text)
        
        self.websocket_manager.send_browser_activity(
            self.task_id, 
            "input", 
            self.get_current_url(), 
            f"Texto introducido en: {selector}", 
            ""
        )

    def _extract_data_legacy(self, task_description: str) -> Dict[str, Any]:
        """Legacy data extraction (basic)"""
        try:
            content = self.get_page_content()
            return {
                "task": task_description,
                "url": self.get_current_url(),
                "content_length": len(content),
                "timestamp": datetime.now().isoformat(),
                "method": "legacy",
                "success": True
            }
        except Exception as e:
            return {
                "task": task_description,
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }

    # ========================================================================
    # UTILIDADES Y MÉTODOS DE COMPATIBILIDAD
    # ========================================================================

    def get_page_content(self) -> str:
        """Get current page content (sync for backward compatibility)"""
        try:
            if self.browser_type == "playwright":
                return self.page.content()
            elif self.browser_type == "selenium":
                return self.driver.page_source
            elif self.browser_type == "browser-use":
                # For browser-use, we'll need to implement this differently
                logger.warning("get_page_content not directly supported with browser-use. Use extract_data instead.")
                return ""
        except Exception as e:
            logger.error(f"Error getting page content: {e}")
            return ""

    def get_current_url(self) -> str:
        """Get current URL (sync for backward compatibility)"""
        try:
            if self.browser_type == "playwright":
                return self.page.url if self.page else ""
            elif self.browser_type == "selenium":
                return self.driver.current_url if self.driver else ""
            elif self.browser_type == "browser-use":
                return self.current_url
        except Exception as e:
            logger.error(f"Error getting current URL: {e}")
            return ""

    def get_page_title(self) -> str:
        """Get page title (sync for backward compatibility)"""
        try:
            if self.browser_type == "playwright":
                return self.page.title() if self.page else ""
            elif self.browser_type == "selenium":
                return self.driver.title if self.driver else ""
            elif self.browser_type == "browser-use":
                # For browser-use, this would need async call - return cached or empty
                return "Título no disponible en modo síncrono"
        except Exception as e:
            logger.error(f"Error getting page title: {e}")
            return ""

    def _take_screenshot(self) -> str:
        """Take screenshot (sync for backward compatibility)"""
        try:
            timestamp = int(time.time() * 1000)
            filename = f"screenshot_{timestamp}.png"
            screenshot_path = self.screenshots_dir / filename
            
            if self.browser_type == "playwright":
                self.page.screenshot(path=str(screenshot_path), quality=20, full_page=False)
            elif self.browser_type == "selenium":
                self.driver.save_screenshot(str(screenshot_path))
            elif self.browser_type == "browser-use":
                # browser-use screenshots need async - skip for sync calls
                logger.warning("Screenshot skipped for browser-use in sync mode. Use async methods.")
                return ""
            
            return f"/api/files/screenshots/{self.task_id}/{filename}"
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return ""

    # ========================================================================
    # CLEANUP Y CIERRE
    # ========================================================================

    async def close(self):
        """Close browser and cleanup resources"""
        try:
            if self.browser_use_agent:
                # Close browser-use agent
                if hasattr(self.browser_use_agent, 'browser_session'):
                    if hasattr(self.browser_use_agent.browser_session, 'close'):
                        await self.browser_use_agent.browser_session.close()
                logger.info("✅ browser-use Agent closed")
            
            if self.browser:
                # Close legacy Playwright browser
                self.browser.close()
                if hasattr(self, 'playwright_instance'):
                    self.playwright_instance.stop()
                logger.info("✅ Legacy Playwright browser closed")
            
            if self.driver:
                # Close legacy Selenium driver
                self.driver.quit()
                logger.info("✅ Legacy Selenium driver closed")
            
            self.is_initialized = False
            
            self.websocket_manager.send_log_message(
                self.task_id, 
                "info", 
                "🔒 Navegador cerrado correctamente"
            )
            
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            if self.is_initialized:
                # Run async close in sync context if needed
                if self.browser_type == "browser-use":
                    # For browser-use, we need async cleanup
                    logger.warning("browser-use cleanup requires async context. Use close() method explicitly.")
                else:
                    # Sync cleanup for legacy browsers
                    if self.browser:
                        self.browser.close()
                        if hasattr(self, 'playwright_instance'):
                            self.playwright_instance.stop()
                    if self.driver:
                        self.driver.quit()
        except Exception as e:
            logger.error(f"Error in WebBrowserManager destructor: {e}")

    # ========================================================================
    # MÉTODOS DE COMPATIBILIDAD CON PLAYWRIGHT LISTENER SYSTEM
    # ========================================================================

    def _setup_playwright_listeners(self):
        """Setup Playwright event listeners for legacy mode"""
        if not self.page:
            return
        
        def on_url_changed(url):
            self._on_url_changed(url)
        
        def on_page_loaded():
            self._on_page_loaded()
        
        def on_request(request):
            self._on_request(request)
        
        def on_response(response):
            self._on_response(response)
        
        self.page.on("load", lambda: on_page_loaded())
        self.page.on("domcontentloaded", lambda: self._on_dom_ready())

    def _on_url_changed(self, url: str):
        """Handle URL change event (legacy)"""
        self.websocket_manager.send_browser_activity(
            self.task_id, 
            "url_changed", 
            url, 
            "", 
            ""
        )
        logger.info(f"🔄 URL changed: {url}")

    def _on_page_loaded(self):
        """Handle page load event (legacy)"""
        current_url = self.get_current_url()
        title = self.get_page_title()
        screenshot_path = self._take_screenshot()
        
        self.websocket_manager.send_browser_activity(
            self.task_id, 
            "page_loaded", 
            current_url, 
            title, 
            screenshot_path
        )
        
        self.websocket_manager.send_log_message(
            self.task_id, 
            "info", 
            f"📄 Página cargada: {title} ({current_url})"
        )

    def _on_dom_ready(self):
        """Handle DOM content loaded event (legacy)"""
        current_url = self.get_current_url()
        self.websocket_manager.send_log_message(
            self.task_id, 
            "info", 
            f"🔧 DOM listo: {current_url}"
        )

    def _on_request(self, request):
        """Handle network request event (legacy)"""
        if request.resource_type in ['document', 'xhr', 'fetch']:
            self.websocket_manager.send_log_message(
                self.task_id, 
                "debug", 
                f"📡 Request: {request.method} {request.url}"
            )

    def _on_response(self, response):
        """Handle network response event (legacy)"""
        if response.request.resource_type in ['document', 'xhr', 'fetch']:
            self.websocket_manager.send_log_message(
                self.task_id, 
                "debug", 
                f"📨 Response: {response.status} {response.url}"
            )

    def get_page_title(self) -> str:
        """Get current page title"""
        try:
            if self.browser_type == "playwright":
                return self.page.title() if self.page else ""
            elif self.browser_type == "selenium":
                return self.driver.title if self.driver else ""
        except Exception as e:
            logger.error(f"Error getting page title: {e}")
            return ""

    def _take_screenshot(self) -> str:
        """Take screenshot and return accessible URL"""
        try:
            timestamp = int(time.time() * 1000)
            screenshot_name = f"screenshot_{timestamp}.png"
            screenshot_path = self.screenshots_dir / screenshot_name
            
            if self.browser_type == "playwright":
                self.page.screenshot(path=str(screenshot_path))
            elif self.browser_type == "selenium":
                self.driver.save_screenshot(str(screenshot_path))
            
            # Return URL accessible for frontend (served by Flask endpoint)
            return f"/api/files/screenshots/{self.task_id}/{screenshot_name}"
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return ""

    def extract_data(self, selector: str) -> Dict[str, Any]:
        """Extract data from page elements with real-time progress"""
        try:
            data = {}
            
            if self.browser_type == "playwright":
                elements = self.page.query_selector_all(selector)
                data = {
                    "count": len(elements),
                    "elements": [elem.text_content() for elem in elements[:10]]  # Limit to 10
                }
            elif self.browser_type == "selenium":
                from selenium.webdriver.common.by import By
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                data = {
                    "count": len(elements),
                    "elements": [elem.text for elem in elements[:10]]  # Limit to 10
                }
            
            # Send data collection update
            self.websocket_manager.send_data_collection_update(
                self.task_id,
                f"extract-{selector}",
                f"Extraídos {data['count']} elementos usando selector: {selector}",
                data
            )
            
            return data
            
        except Exception as e:
            error_msg = f"❌ Error extrayendo datos con selector {selector}: {str(e)}"
            logger.error(error_msg)
            self.websocket_manager.send_log_message(self.task_id, "error", error_msg)
            return {}

    def close_browser(self):
        """Close browser and cleanup"""
        try:
            if self.browser_type == "playwright" and self.browser:
                self.browser.close()
                if hasattr(self, 'playwright_instance'):
                    self.playwright_instance.stop()
            elif self.browser_type == "selenium" and self.driver:
                self.driver.quit()
            
            self.is_initialized = False
            
            self.websocket_manager.send_log_message(
                self.task_id, 
                "info", 
                f"🔚 Navegador {self.browser_type} cerrado correctamente"
            )
            
            logger.info(f"✅ Browser {self.browser_type} closed successfully")
            
        except Exception as e:
            error_msg = f"❌ Error cerrando navegador: {str(e)}"
            logger.error(error_msg)
            self.websocket_manager.send_log_message(self.task_id, "error", error_msg)

    def wait_for_element(self, selector: str, timeout: int = 30):
        """Wait for element to appear"""
        try:
            if self.browser_type == "playwright":
                self.page.wait_for_selector(selector, timeout=timeout * 1000)
            elif self.browser_type == "selenium":
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.webdriver.common.by import By
                wait = WebDriverWait(self.driver, timeout)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            
            self.websocket_manager.send_log_message(
                self.task_id, 
                "info", 
                f"✅ Elemento encontrado: {selector}"
            )
            
        except Exception as e:
            error_msg = f"❌ Timeout esperando elemento {selector}: {str(e)}"
            logger.error(error_msg)
            self.websocket_manager.send_log_message(self.task_id, "error", error_msg)
            raise