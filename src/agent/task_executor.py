"""Task executor for managing and running tasks."""

import asyncio
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from collections import deque

from src.agent.browser_agent_v1 import BrowserAgent
from src.tasks.base_task import BaseTask, TaskResult, TaskStatus, TaskPriority
from src.utils.logger import LoggerMixin
from src.config.settings import settings


class TaskQueue:
    """Priority queue for tasks."""
    
    def __init__(self):
        self.queues = {
            TaskPriority.CRITICAL: deque(),
            TaskPriority.HIGH: deque(),
            TaskPriority.MEDIUM: deque(),
            TaskPriority.LOW: deque()
        }
        self._lock = asyncio.Lock()
        
    async def add(self, task: BaseTask) -> None:
        """Add task to queue."""
        async with self._lock:
            self.queues[task.priority].append(task)
    
    async def get(self) -> Optional[BaseTask]:
        """Get highest priority task."""
        async with self._lock:
            for priority in [TaskPriority.CRITICAL, TaskPriority.HIGH, 
                           TaskPriority.MEDIUM, TaskPriority.LOW]:
                queue = self.queues[priority]
                if queue:
                    return queue.popleft()
        return None
    
    async def size(self) -> int:
        """Get total queue size."""
        async with self._lock:
            return sum(len(q) for q in self.queues.values())
    
    async def clear(self) -> None:
        """Clear all queues."""
        async with self._lock:
            for queue in self.queues.values():
                queue.clear()


class TaskExecutor(LoggerMixin):
    """Executor for running tasks with browser agents."""
    
    def __init__(
        self,
        max_concurrent_tasks: int = 5,
        max_agents: int = 3
    ):
        """
        Initialize task executor.
        
        Args:
            max_concurrent_tasks: Maximum number of concurrent tasks
            max_agents: Maximum number of browser agents
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_agents = max_agents
        self.task_queue = TaskQueue()
        self.agents: List[BrowserAgent] = []
        self.active_tasks: Dict[str, BaseTask] = {}
        self.completed_tasks: List[TaskResult] = []
        self._running = False
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        
    async def initialize(self) -> None:
        """Initialize executor and agents."""
        self.logger.info("Initializing task executor...")
        
        # Create browser agents
        for i in range(self.max_agents):
            agent = BrowserAgent(name=f"BrowserAgent-{i}")
            await agent.initialize()
            self.agents.append(agent)
        
        self._running = True
        self.logger.info(f"Task executor initialized with {len(self.agents)} agents")
    
    async def add_task(self, task: BaseTask) -> None:
        """
        Add task to execution queue.
        
        Args:
            task: Task to execute
        """
        if not task.validate():
            raise ValueError(f"Invalid task: {task.task_id}")
        
        await self.task_queue.add(task)
        self.logger.info(f"Added task {task.task_id} to queue")
    
    async def add_tasks(self, tasks: List[BaseTask]) -> None:
        """
        Add multiple tasks to execution queue.
        
        Args:
            tasks: List of tasks to execute
        """
        for task in tasks:
            await self.add_task(task)
    
    async def execute_task(self, task: BaseTask) -> TaskResult:
        """
        Execute a single task.
        
        Args:
            task: Task to execute
            
        Returns:
            TaskResult with execution details
        """
        # Get available agent
        agent = await self._get_available_agent()
        if not agent:
            raise RuntimeError("No available agents")
        
        self.active_tasks[task.task_id] = task
        
        try:
            self.logger.info(f"Executing task {task.task_id} with {agent.name}")
            result = await task.execute(agent)
            
            self.completed_tasks.append(result)
            self.logger.info(
                f"Task {task.task_id} completed with status {result.status.value}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Task {task.task_id} failed: {str(e)}")
            result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                completed_at=datetime.utcnow()
            )
            self.completed_tasks.append(result)
            return result
            
        finally:
            self.active_tasks.pop(task.task_id, None)
    
    async def run(self) -> None:
        """Run the task executor."""
        self.logger.info("Starting task executor...")
        
        while self._running:
            # Check for tasks in queue
            if await self.task_queue.size() == 0:
                await asyncio.sleep(0.1)
                continue
            
            # Check if we can run more tasks
            if len(self.active_tasks) >= self.max_concurrent_tasks:
                await asyncio.sleep(0.1)
                continue
            
            # Get next task
            task = await self.task_queue.get()
            if task:
                # Execute task asynchronously
                asyncio.create_task(self.execute_task(task))
    
    async def stop(self) -> None:
        """Stop the task executor."""
        self.logger.info("Stopping task executor...")
        self._running = False
        
        # Wait for active tasks to complete
        while self.active_tasks:
            await asyncio.sleep(0.1)
        
        # Cleanup agents
        for agent in self.agents:
            await agent.cleanup()
        
        self.agents.clear()
        self._executor.shutdown(wait=True)
        
        self.logger.info("Task executor stopped")
    
    async def _get_available_agent(self) -> Optional[BrowserAgent]:
        """Get an available agent."""
        # In a more sophisticated implementation, this would track
        # which agents are busy and return an available one
        if self.agents:
            return self.agents[0]
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get executor status."""
        return {
            "running": self._running,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "queue_size": asyncio.run(self.task_queue.size()),
            "agents": [agent.get_status() for agent in self.agents]
        }
    
    def get_task_results(self) -> List[TaskResult]:
        """Get all completed task results."""
        return self.completed_tasks.copy()
    
    def clear_completed_tasks(self) -> None:
        """Clear completed tasks list."""
        self.completed_tasks.clear()