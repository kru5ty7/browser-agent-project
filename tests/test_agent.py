"""Tests for browser agent."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.agent.browser_agent_v1 import BrowserAgent
from src.agent.task_executor import TaskExecutor, TaskQueue
from src.tasks.base_task import TaskResult, TaskStatus, TaskPriority
from src.tasks.web_tasks import WebScrapingTask, FormFillingTask, NavigationTask


@pytest.fixture
async def mock_browser():
    """Create mock browser."""
    browser = AsyncMock()
    browser.navigate = AsyncMock()
    browser.get_content = AsyncMock(return_value="<html><body>Test</body></html>")
    browser.fill = AsyncMock()
    browser.click = AsyncMock()
    browser.close = AsyncMock()
    return browser


@pytest.fixture
async def mock_agent(mock_browser):
    """Create mock agent."""
    agent = AsyncMock()
    agent.browser = mock_browser
    agent.run = AsyncMock(return_value="Test result")
    return agent


class TestBrowserAgent:
    """Test BrowserAgent class."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization."""
        agent = BrowserAgent()
        assert agent.name == "BrowserAgent"
        assert not agent._is_initialized
        
    @pytest.mark.asyncio
    async def test_agent_context_manager(self):
        """Test agent context manager."""
        with patch('src.agent.browser_agent_v1.Browser') as mock_browser_class:
            mock_browser_class.return_value = AsyncMock()
            
            async with BrowserAgent() as agent:
                assert agent._is_initialized
            
            assert not agent._is_initialized
    
    @pytest.mark.asyncio
    async def test_execute_string_task(self, mock_agent):
        """Test executing string task."""
        with patch('src.agent.browser_agent_v1.Agent', return_value=mock_agent):
            agent = BrowserAgent()
            agent._is_initialized = True
            agent.agent = mock_agent
            
            result = await agent.execute("Test task")
            
            assert result.success
            assert result.data == "Test result"
            mock_agent.run.assert_called_once_with("Test task")
    
    @pytest.mark.asyncio
    async def test_execute_with_retry(self, mock_agent):
        """Test task execution with retry."""
        mock_agent.run.side_effect = [Exception("First attempt"), "Success"]
        
        with patch('src.agent.browser_agent_v1.Agent', return_value=mock_agent):
            agent = BrowserAgent()
            agent._is_initialized = True
            agent.agent = mock_agent
            
            with patch('src.config.settings.settings.agent_retry_attempts', 2):
                result = await agent.execute("Test task")
                
                assert result.success
                assert result.data == "Success"
                assert mock_agent.run.call_count == 2


class TestTaskQueue:
    """Test TaskQueue class."""
    
    @pytest.mark.asyncio
    async def test_queue_priority(self):
        """Test task queue priority ordering."""
        queue = TaskQueue()
        
        # Add tasks with different priorities
        low_task = Mock(priority=TaskPriority.LOW)
        medium_task = Mock(priority=TaskPriority.MEDIUM)
        high_task = Mock(priority=TaskPriority.HIGH)
        critical_task = Mock(priority=TaskPriority.CRITICAL)
        
        await queue.add(low_task)
        await queue.add(high_task)
        await queue.add(medium_task)
        await queue.add(critical_task)
        
        # Should get tasks in priority order
        assert await queue.get() == critical_task
        assert await queue.get() == high_task
        assert await queue.get() == medium_task
        assert await queue.get() == low_task
        assert await queue.get() is None
    
    @pytest.mark.asyncio
    async def test_queue_size(self):
        """Test queue size calculation."""
        queue = TaskQueue()
        
        assert await queue.size() == 0
        
        tasks = [Mock(priority=TaskPriority.MEDIUM) for _ in range(5)]
        for task in tasks:
            await queue.add(task)
        
        assert await queue.size() == 5
        
        await queue.get()
        assert await queue.size() == 4


class TestWebTasks:
    """Test web automation tasks."""
    
    @pytest.mark.asyncio
    async def test_web_scraping_task(self, mock_agent):
        """Test web scraping task."""
        task = WebScrapingTask(
            task_id="test-scrape",
            url="https://example.com",
            selectors={"title": "h1", "content": "p"}
        )
        
        assert task.validate()
        
        mock_agent.browser.get_content.return_value = """
        <html>
            <body>
                <h1>Test Title</h1>
                <p>Test content 1</p>
                <p>Test content 2</p>
            </body>
        </html>
        """
        
        result = await task.execute(mock_agent)
        
        assert result.status == TaskStatus.COMPLETED
        assert "title" in result.data
        assert "content" in result.data
        assert len(result.data["content"]) == 2
    
    @pytest.mark.asyncio
    async def test_form_filling_task(self, mock_agent):
        """Test form filling task."""
        task = FormFillingTask(
            task_id="test-form",
            url="https://example.com/form",
            form_data={"#username": "testuser", "#password": "testpass"},
            submit_selector="#submit"
        )
        
        assert task.validate()
        
        result = await task.execute(mock_agent)
        
        assert result.status == TaskStatus.COMPLETED
        assert result.data["submitted"]
        assert len(result.data["filled_fields"]) == 2
        
        # Verify form fields were filled
        mock_agent.browser.fill.assert_any_call("#username", "testuser")
        mock_agent.browser.fill.assert_any_call("#password", "testpass")
        mock_agent.browser.click.assert_called_once_with("#submit")
    
    @pytest.mark.asyncio
    async def test_navigation_task(self, mock_agent):
        """Test navigation task."""
        urls = ["https://example.com/1", "https://example.com/2"]
        task = NavigationTask(
            task_id="test-nav",
            urls=urls
        )
        
        assert task.validate()
        
        mock_agent.browser.get_title.return_value = "Test Page"
        
        result = await task.execute(mock_agent)
        
        assert result.status == TaskStatus.COMPLETED
        assert len(result.data["visited_pages"]) == 2
        assert result.data["visited_pages"] == urls
    
    @pytest.mark.asyncio
    async def test_invalid_task(self):
        """Test invalid task validation."""
        task = WebScrapingTask(
            task_id="invalid",
            url="not-a-url",
            selectors={}
        )
        
        assert not task.validate()


class TestTaskExecutor:
    """Test TaskExecutor class."""
    
    @pytest.mark.asyncio
    async def test_executor_initialization(self):
        """Test executor initialization."""
        executor = TaskExecutor(max_concurrent_tasks=3, max_agents=2)
        
        with patch('src.agent.browser_agent_v1.BrowserAgent') as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent_class.return_value = mock_agent
            
            await executor.initialize()
            
            assert len(executor.agents) == 2
            assert executor._running
    
    @pytest.mark.asyncio
    async def test_add_and_execute_task(self):
        """Test adding and executing tasks."""
        executor = TaskExecutor()
        
        task = Mock()
        task.validate.return_value = True
        task.execute = AsyncMock(return_value=TaskResult(
            task_id="test",
            status=TaskStatus.COMPLETED,
            data="result"
        ))
        
        await executor.add_task(task)
        assert await executor.task_queue.size() == 1
        
        # Mock agent
        mock_agent = AsyncMock()
        executor.agents = [mock_agent]
        
        result = await executor.execute_task(task)
        
        assert result.status == TaskStatus.COMPLETED
        assert result.data == "result"
        assert len(executor.completed_tasks) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])