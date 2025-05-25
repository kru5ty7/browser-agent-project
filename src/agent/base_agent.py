"""Base agent abstract class."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from src.utils.logger import LoggerMixin, logger


@dataclass
class AgentResult:
    """Result from agent execution."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    steps_taken: int = 0
    execution_time: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class BaseAgent(ABC, LoggerMixin):
    """Abstract base class for all agents."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize base agent.
        
        Args:
            name: Agent name for identification
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self._is_initialized = False
        
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent and its resources."""
        pass
    
    @abstractmethod
    async def execute(self, task: Any, **kwargs) -> AgentResult:
        """
        Execute a task.
        
        Args:
            task: Task to execute
            **kwargs: Additional arguments
            
        Returns:
            AgentResult with execution details
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up agent resources."""
        pass
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.cleanup()
    
    def validate_config(self) -> bool:
        """
        Validate agent configuration.
        
        Returns:
            True if configuration is valid
        """
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "name": self.name,
            "initialized": self._is_initialized,
            "config": self.config,
            "timestamp": datetime.utcnow().isoformat()
        }