"""Browser agent implementation using browser-use."""

import asyncio
import time
from typing import Any, Dict, Optional, Union
from browser_use import Browser, Agent
# from langchain.chat_models import ChatOpenAI
try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from src.agent.base_agent import BaseAgent, AgentResult
from src.config.settings import settings
from src.utils.logger import logger, log_execution_time, log_errors


class BrowserAgent(BaseAgent):
    """Agent that controls web browser for automation tasks."""
    
    def __init__(self, name: str = "BrowserAgent", config: Optional[Dict[str, Any]] = None):
        logger.log("initialized the Browser Agent")
        super().__init__(name, config)
        self.browser: Optional[Browser] = None
        self.agent: Optional[Agent] = None
        self.llm = None
        
    async def initialize(self) -> None:
        """Initialize browser and agent resources."""
        try:
            self.logger.info(f"Initializing {self.name}...")
            
            # Initialize LLM
            self.llm = self._create_llm()
            
            # Initialize browser
            self.browser = await self._create_browser()
            
            # Initialize agent
            self.agent = Agent(
                browser=self.browser,
                llm=self.llm,
                max_steps=settings.agent_max_steps
            )
            
            self._is_initialized = True
            self.logger.info(f"{self.name} initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.name}: {str(e)}")
            raise
    
    def _create_llm(self) -> Union[ChatAnthropic, ChatGoogleGenerativeAI]: # type: ignore # to add ChatOpenAI
        """Create LLM instance based on configuration."""
        # OpenAI
        # if settings.openai_api_key and "gpt" in settings.llm_model:
        #     return ChatOpenAI(
        #         api_key=settings.openai_api_key,
        #         model_name=settings.llm_model,
        #         temperature=settings.llm_temperature,
        #         max_tokens=settings.llm_max_tokens
        #     )
        
        # Anthropic
        if settings.anthropic_api_key and "claude" in settings.llm_model:
            if ChatAnthropic is None:
                raise ImportError("langchain-anthropic not installed. Install with: pip install langchain-anthropic")
            return ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens
            )
        
        # Google Gemini
        elif settings.google_api_key and "gemini" in settings.llm_model:
            if ChatGoogleGenerativeAI is None:
                raise ImportError("langchain-google-genai not installed. Install with: pip install langchain-google-genai")
            return ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_output_tokens=settings.llm_max_tokens
            )
        
        else:
            raise ValueError(
                "No valid LLM configuration found. Please set one of: "
                "OPENAI_API_KEY (with gpt model), "
                "ANTHROPIC_API_KEY (with claude model), or "
                "GOOGLE_API_KEY (with gemini model)"
            )
    
    async def _create_browser(self) -> Browser:
        """Create and configure browser instance."""
        return Browser(
            headless=settings.browser_headless,
            viewport_width=settings.browser_viewport_width,
            viewport_height=settings.browser_viewport_height,
            timeout=settings.browser_timeout
        )
    
    @retry(
        stop=stop_after_attempt(settings.agent_retry_attempts),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception)
    )
    @log_execution_time
    @log_errors
    async def execute(self, task: Any, **kwargs) -> AgentResult:
        """
        Execute a browser task.
        
        Args:
            task: Task object or string description
            **kwargs: Additional arguments
            
        Returns:
            AgentResult with execution details
        """
        if not self._is_initialized:
            await self.initialize()
        
        start_time = time.time()
        steps_taken = 0
        
        try:
            self.logger.info(f"Executing task: {task}")
            
            # Validate domain if URL is provided
            if "url" in kwargs:
                self._validate_domain(kwargs["url"])
            
            # Execute task
            if isinstance(task, str):
                # Simple string task
                result = await self.agent.run(task, **kwargs)
            else:
                # Complex task object
                result = await self._execute_complex_task(task, **kwargs)
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                success=True,
                data=result,
                steps_taken=self.agent.steps_taken if hasattr(self.agent, 'steps_taken') else steps_taken,
                execution_time=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {str(e)}")
            execution_time = time.time() - start_time
            
            return AgentResult(
                success=False,
                error=str(e),
                steps_taken=steps_taken,
                execution_time=execution_time
            )
    
    async def _execute_complex_task(self, task: Any, **kwargs) -> Any:
        """Execute a complex task object."""
        # This method should be overridden for specific task types
        if hasattr(task, 'execute'):
            return await task.execute(self.agent, **kwargs)
        else:
            raise ValueError(f"Unknown task type: {type(task)}")
    
    def _validate_domain(self, url: str) -> None:
        """Validate if domain is allowed."""
        if not settings.allowed_domains:
            return  # No restrictions
        
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        if domain and not any(allowed in domain for allowed in settings.allowed_domains):
            raise ValueError(f"Domain {domain} is not in allowed domains list")
    
    async def cleanup(self) -> None:
        """Clean up browser resources."""
        try:
            self.logger.info(f"Cleaning up {self.name}...")
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            self.agent = None
            self._is_initialized = False
            
            self.logger.info(f"{self.name} cleaned up successfully")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
    
    async def take_screenshot(self, filename: str) -> str:
        """
        Take a screenshot of current page.
        
        Args:
            filename: Path to save screenshot
            
        Returns:
            Path to saved screenshot
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized")
        
        await self.browser.screenshot(filename)
        self.logger.info(f"Screenshot saved to {filename}")
        return filename
    
    async def get_page_content(self) -> str:
        """
        Get current page content.
        
        Returns:
            HTML content of current page
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized")
        
        return await self.browser.get_content()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        status = super().get_status()
        status.update({
            "browser_active": self.browser is not None,
            "llm_model": settings.llm_model,
            "headless": settings.browser_headless
        })
        return status
