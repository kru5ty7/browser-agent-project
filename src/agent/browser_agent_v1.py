"""Browser agent implementation using browser-use."""

import asyncio
import time
from typing import Any, Dict, Optional, Union
from browser_use import Agent
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    try:
        from langchain_community.chat_models import ChatOpenAI
    except ImportError:
        from langchain.chat_models import ChatOpenAI
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
        super().__init__(name, config)
        self.agent: Optional[Agent] = None
        self.llm = None
        
    async def initialize(self) -> None:
        """Initialize browser and agent resources."""
        try:
            self.logger.info(f"Initializing {self.name}...")
            
            # Initialize LLM
            self.llm = self._create_llm()
            
            self._is_initialized = True
            self.logger.info(f"{self.name} initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.name}: {str(e)}")
            raise
    
    def _create_llm(self) -> Union[ChatOpenAI, ChatAnthropic, ChatGoogleGenerativeAI]:
        """Create LLM instance based on configuration."""
        # OpenAI
        if settings.openai_api_key and "gpt" in settings.llm_model:
            return ChatOpenAI(
                api_key=settings.openai_api_key,
                model_name=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens
            )
        
        # Anthropic
        elif settings.anthropic_api_key and "claude" in settings.llm_model:
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
    
    @retry(
        stop=stop_after_attempt(settings.agent_retry_attempts),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception)
    )
    @log_execution_time
    @log_errors
    async def execute(self, task: Any, max_steps:int, **kwargs) -> AgentResult:
        """
        Execute a browser task using browser-use v0.2.2 API.
        
        Args:
            task: Task object or string description
            **kwargs: Additional arguments
            
        Returns:
            AgentResult with execution details
        """
        if not self._is_initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            self.logger.info(f"Executing task: {task}")
            
            # Create agent for this specific task
            if isinstance(task, str):
                # Simple string task
                self.agent = Agent(task=task, llm=self.llm)
                result = await self.agent.run(max_steps=max_steps)
            else:
                # Complex task object
                task_description = getattr(task, 'description', str(task))
                self.agent = Agent(task=task_description, llm=self.llm)
                result = await self._execute_complex_task(task, **kwargs)
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                success=True,
                data=result,
                steps_taken=getattr(self.agent, 'steps_taken', 0),
                execution_time=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {str(e)}")
            execution_time = time.time() - start_time
            
            return AgentResult(
                success=False,
                error=str(e),
                steps_taken=0,
                execution_time=execution_time
            )
    
    async def _execute_complex_task(self, task: Any, **kwargs) -> Any:
        """Execute a complex task object."""
        # For browser-use v0.2.2, we need to convert task to string
        if hasattr(task, 'execute'):
            # Let the task handle its own execution
            return await task.execute(self.agent, **kwargs)
        else:
            # Convert task to string description
            task_str = str(task)
            return await self.agent.run()
    
    async def cleanup(self) -> None:
        """Clean up browser resources."""
        try:
            self.logger.info(f"Cleaning up {self.name}...")
            
            # browser-use v0.2.2 handles cleanup internally
            self.agent = None
            self._is_initialized = False
            
            self.logger.info(f"{self.name} cleaned up successfully")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
    
    async def take_screenshot(self, filename: str) -> str:
        """
        Take a screenshot of current page.
        Note: This feature may not be available in browser-use v0.2.2
        """
        self.logger.warning("Screenshot feature may not be available in browser-use v0.2.2")
        return filename
    
    async def get_page_content(self) -> str:
        """
        Get current page content.
        Note: This feature may not be available in browser-use v0.2.2
        """
        self.logger.warning("Page content feature may not be available in browser-use v0.2.2")
        return ""
    
    def _validate_domain(self, url: str) -> None:
        """Validate if domain is allowed."""
        if not settings.allowed_domains:
            return  # No restrictions
        
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        if domain and not any(allowed in domain for allowed in settings.allowed_domains):
            raise ValueError(f"Domain {domain} is not in allowed domains list")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        status = super().get_status()
        status.update({
            "browser_active": self.browser is not None,
            "llm_model": settings.llm_model,
            "headless": settings.browser_headless
        })
        return status