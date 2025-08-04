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
from .adapters.mitosis_ollama_chat import MitosisOllamaChatModel
from .services.ollama_service import OllamaService

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
            
            # Initialize browser-use Agent with our LLM
            self.browser_use_agent = Agent(
                task="Navegación web inteligente para el usuario",
                llm=self.llm_model,
                browser_session=self.browser_session,
                use_vision=True,  # Enable vision for better understanding
                max_failures=3,   # Resilience
                save_conversation_path=f"/tmp/browser_conversations/{self.task_id}.json"
            )
            
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

    def navigate(self, url: str, wait_for_load: bool = True):
        """
        Navigate to a URL with real-time event tracking
        
        Args:
            url: URL to navigate to
            wait_for_load: Whether to wait for page load completion
        """
        if not self.is_initialized:
            raise RuntimeError("Browser not initialized. Call initialize_browser() first.")
        
        try:
            self.websocket_manager.send_log_message(
                self.task_id, 
                "info", 
                f"🚀 Navegando a: {url}"
            )
            
            # Send URL change event before navigation
            self._on_url_changed(url)
            
            if self.browser_type == "playwright":
                self.page.goto(url, wait_until='networkidle' if wait_for_load else 'commit')
            elif self.browser_type == "selenium":
                self.driver.get(url)
                if wait_for_load:
                    time.sleep(2)  # Basic wait for Selenium
                
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
                
                self.websocket_manager.send_log_message(
                    self.task_id, 
                    "info", 
                    f"📄 Página cargada (Selenium): {title} ({current_url})"
                )
            
        except Exception as e:
            error_msg = f"❌ Error navegando a {url}: {str(e)}"
            logger.error(error_msg)
            self.websocket_manager.send_log_message(self.task_id, "error", error_msg)
            raise

    def click_element(self, selector: str):
        """Click an element with real-time tracking"""
        try:
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
            
            self.websocket_manager.send_log_message(
                self.task_id, 
                "info", 
                f"👆 Click realizado en: {selector}"
            )
            
        except Exception as e:
            error_msg = f"❌ Error haciendo click en {selector}: {str(e)}"
            logger.error(error_msg)
            self.websocket_manager.send_log_message(self.task_id, "error", error_msg)
            raise

    def type_text(self, selector: str, text: str):
        """Type text in an element with real-time tracking"""
        try:
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
            
            self.websocket_manager.send_log_message(
                self.task_id, 
                "info", 
                f"⌨️ Texto introducido en {selector}: {text[:50]}..."
            )
            
        except Exception as e:
            error_msg = f"❌ Error escribiendo en {selector}: {str(e)}"
            logger.error(error_msg)
            self.websocket_manager.send_log_message(self.task_id, "error", error_msg)
            raise

    def get_page_content(self) -> str:
        """Get current page content"""
        try:
            if self.browser_type == "playwright":
                return self.page.content()
            elif self.browser_type == "selenium":
                return self.driver.page_source
        except Exception as e:
            logger.error(f"Error getting page content: {e}")
            return ""

    def get_current_url(self) -> str:
        """Get current URL"""
        try:
            if self.browser_type == "playwright":
                return self.page.url if self.page else ""
            elif self.browser_type == "selenium":
                return self.driver.current_url if self.driver else ""
        except Exception as e:
            logger.error(f"Error getting current URL: {e}")
            return ""

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