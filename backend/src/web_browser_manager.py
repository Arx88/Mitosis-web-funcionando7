"""
Web Browser Manager for Real-time Web Navigation Tracking
Implements Playwright and Selenium integration for browser automation with real-time event capture
"""

import os
import sys
import time
import base64
import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class WebBrowserManager:
    """
    Comprehensive web browser manager supporting both Playwright and Selenium
    with real-time event capture and WebSocket integration
    """
    
    def __init__(self, websocket_manager, task_id: str, browser_type: str = "playwright"):
        """
        Initialize WebBrowserManager
        
        Args:
            websocket_manager: WebSocketManager instance for real-time updates
            task_id: Task ID for event tracking
            browser_type: 'playwright' or 'selenium'
        """
        self.websocket_manager = websocket_manager
        self.task_id = task_id
        self.browser_type = browser_type
        self.browser = None
        self.page = None  # For Playwright
        self.driver = None  # For Selenium
        self.is_initialized = False
        
        # Create screenshots directory
        self.screenshots_dir = Path(f"/tmp/screenshots/{task_id}")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🌐 WebBrowserManager initialized for task {task_id} using {browser_type}")

    def initialize_browser(self):
        """Initialize browser instance with event listeners"""
        try:
            if self.browser_type == "playwright":
                self._initialize_playwright()
            elif self.browser_type == "selenium":
                self._initialize_selenium()
            else:
                raise ValueError(f"Unsupported browser type: {self.browser_type}")
            
            self.is_initialized = True
            self.websocket_manager.send_log_message(
                self.task_id, 
                "info", 
                f"🌐 Navegador {self.browser_type} inicializado correctamente"
            )
            
        except Exception as e:
            error_msg = f"❌ Error inicializando navegador {self.browser_type}: {str(e)}"
            logger.error(error_msg)
            self.websocket_manager.send_log_message(self.task_id, "error", error_msg)
            raise

    def _initialize_playwright(self):
        """Initialize Playwright browser with event listeners"""
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
            
            # Setup event listeners
            self._setup_playwright_listeners()
            
            logger.info("✅ Playwright browser initialized successfully")
            
        except ImportError:
            raise ImportError("Playwright no está instalado. Use: pip install playwright && playwright install")
        except Exception as e:
            raise Exception(f"Error inicializando Playwright: {str(e)}")

    def _initialize_selenium(self):
        """Initialize Selenium browser with basic setup"""
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
            
            logger.info("✅ Selenium browser initialized successfully")
            
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