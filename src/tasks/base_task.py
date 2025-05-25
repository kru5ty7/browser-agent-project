"""Base task class for defining browser automation tasks."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.utils.logger import LoggerMixin


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    """Result from task execution."""
    task_id: str
    status: TaskStatus
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def execution_time(self) -> Optional[float]:
        """Calculate execution time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class BaseTask(ABC, LoggerMixin):
    """Abstract base class for all tasks."""
    
    def __init__(
        self,
        task_id: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        timeout: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base task.
        
        Args:
            task_id: Unique task identifier
            description: Human-readable task description
            priority: Task priority level
            timeout: Task timeout in seconds
            metadata: Additional task metadata
        """
        self.task_id = task_id
        self.description = description
        self.priority = priority
        self.timeout = timeout
        self.metadata = metadata or {}
        self.status = TaskStatus.PENDING
        self.created_at = datetime.utcnow()
        
    @abstractmethod
    async def execute(self, agent: Any, **kwargs) -> TaskResult:
        """
        Execute the task.
        
        Args:
            agent: Browser agent instance
            **kwargs: Additional arguments
            
        Returns:
            TaskResult with execution details
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """
        Validate task parameters.
        
        Returns:
            True if task is valid
        """
        pass
    
    async def pre_execute(self, agent: Any) -> None:
        """Hook called before task execution."""
        self.logger.debug(f"Pre-executing task {self.task_id}")
        self.status = TaskStatus.RUNNING
    
    async def post_execute(self, agent: Any, result: TaskResult) -> None:
        """Hook called after task execution."""
        self.logger.debug(f"Post-executing task {self.task_id}")
        self.status = result.status
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "timeout": self.timeout,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    def __str__(self) -> str:
        """String representation of task."""
        return f"{self.__class__.__name__}(id={self.task_id}, status={self.status.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"{self.__class__.__name__}("
            f"task_id={self.task_id!r}, "
            f"description={self.description!r}, "
            f"priority={self.priority}, "
            f"status={self.status})"
        )