"""Specific web automation task implementations."""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup

# Try to use lxml parser, fall back to html.parser if not available
try:
    import lxml
    HTML_PARSER = 'lxml'
except ImportError:
    HTML_PARSER = 'html.parser'

from src.tasks.base_task import BaseTask, TaskResult, TaskStatus, TaskPriority
from src.utils.logger import logger


class WebScrapingTask(BaseTask):
    """Task for scraping data from websites."""
    
    def __init__(
        self,
        task_id: str,
        url: str,
        selectors: Dict[str, str],
        wait_for_selector: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize web scraping task.
        
        Args:
            task_id: Unique task identifier
            url: URL to scrape
            selectors: CSS selectors for data extraction
            wait_for_selector: Selector to wait for before scraping
            description: Task description
            **kwargs: Additional task parameters
        """
        super().__init__(
            task_id=task_id,
            description=description or f"Scrape data from {url}",
            **kwargs
        )
        self.url = url
        self.selectors = selectors
        self.wait_for_selector = wait_for_selector
        
    def validate(self) -> bool:
        """Validate task parameters."""
        if not self.url or not self.url.startswith(('http://', 'https://')):
            self.logger.error(f"Invalid URL: {self.url}")
            return False
        
        if not self.selectors:
            self.logger.error("No selectors provided")
            return False
        
        return True
    
    async def execute(self, agent: Any, **kwargs) -> TaskResult:
        """Execute web scraping task."""
        result = TaskResult(
            task_id=self.task_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        try:
            await self.pre_execute(agent)
            
            # Navigate to URL
            self.logger.info(f"Navigating to {self.url}")
            await agent.browser.navigate(self.url)
            
            # Wait for selector if specified
            if self.wait_for_selector:
                self.logger.info(f"Waiting for selector: {self.wait_for_selector}")
                await agent.browser.wait_for_selector(self.wait_for_selector)
            
            # Extract data
            extracted_data = {}
            page_content = await agent.browser.get_content()
            soup = BeautifulSoup(page_content, HTML_PARSER)
            
            for key, selector in self.selectors.items():
                try:
                    elements = soup.select(selector)
                    if elements:
                        extracted_data[key] = [elem.get_text(strip=True) for elem in elements]
                        self.logger.debug(f"Extracted {len(elements)} items for {key}")
                    else:
                        extracted_data[key] = []
                        self.logger.warning(f"No elements found for selector: {selector}")
                except Exception as e:
                    self.logger.error(f"Error extracting {key}: {str(e)}")
                    extracted_data[key] = []
            
            result.data = extracted_data
            result.status = TaskStatus.COMPLETED
            result.metadata = {
                "url": self.url,
                "selectors_used": self.selectors,
                "extraction_count": {k: len(v) for k, v in extracted_data.items()}
            }
            
        except Exception as e:
            self.logger.error(f"Web scraping task failed: {str(e)}")
            result.status = TaskStatus.FAILED
            result.error = str(e)
        
        finally:
            result.completed_at = datetime.utcnow()
            await self.post_execute(agent, result)
        
        return result


class FormFillingTask(BaseTask):
    """Task for filling and submitting web forms."""
    
    def __init__(
        self,
        task_id: str,
        url: str,
        form_data: Dict[str, Any],
        submit_selector: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize form filling task.
        
        Args:
            task_id: Unique task identifier
            url: URL of the form
            form_data: Dictionary of field selectors and values
            submit_selector: Selector for submit button
            description: Task description
            **kwargs: Additional task parameters
        """
        super().__init__(
            task_id=task_id,
            description=description or f"Fill form at {url}",
            **kwargs
        )
        self.url = url
        self.form_data = form_data
        self.submit_selector = submit_selector
        
    def validate(self) -> bool:
        """Validate task parameters."""
        if not self.url or not self.url.startswith(('http://', 'https://')):
            self.logger.error(f"Invalid URL: {self.url}")
            return False
        
        if not self.form_data:
            self.logger.error("No form data provided")
            return False
        
        return True
    
    async def execute(self, agent: Any, **kwargs) -> TaskResult:
        """Execute form filling task."""
        result = TaskResult(
            task_id=self.task_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        try:
            await self.pre_execute(agent)
            
            # Navigate to URL
            self.logger.info(f"Navigating to {self.url}")
            await agent.browser.navigate(self.url)
            
            # Fill form fields
            filled_fields = []
            for selector, value in self.form_data.items():
                try:
                    self.logger.debug(f"Filling field {selector} with value")
                    await agent.browser.fill(selector, str(value))
                    filled_fields.append(selector)
                except Exception as e:
                    self.logger.error(f"Failed to fill field {selector}: {str(e)}")
            
            # Submit form if selector provided
            if self.submit_selector:
                self.logger.info(f"Submitting form using selector: {self.submit_selector}")
                await agent.browser.click(self.submit_selector)
                await asyncio.sleep(2)  # Wait for submission
            
            result.data = {
                "filled_fields": filled_fields,
                "submitted": bool(self.submit_selector)
            }
            result.status = TaskStatus.COMPLETED
            result.metadata = {
                "url": self.url,
                "form_fields": list(self.form_data.keys())
            }
            
        except Exception as e:
            self.logger.error(f"Form filling task failed: {str(e)}")
            result.status = TaskStatus.FAILED
            result.error = str(e)
        
        finally:
            result.completed_at = datetime.utcnow()
            await self.post_execute(agent, result)
        
        return result


class NavigationTask(BaseTask):
    """Task for navigating through multiple pages."""
    
    def __init__(
        self,
        task_id: str,
        urls: List[str],
        actions: Optional[List[Dict[str, Any]]] = None,
        description: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize navigation task.
        
        Args:
            task_id: Unique task identifier
            urls: List of URLs to navigate
            actions: Optional actions to perform on each page
            description: Task description
            **kwargs: Additional task parameters
        """
        super().__init__(
            task_id=task_id,
            description=description or f"Navigate through {len(urls)} pages",
            **kwargs
        )
        self.urls = urls
        self.actions = actions or []
        
    def validate(self) -> bool:
        """Validate task parameters."""
        if not self.urls:
            self.logger.error("No URLs provided")
            return False
        
        for url in self.urls:
            if not url.startswith(('http://', 'https://')):
                self.logger.error(f"Invalid URL: {url}")
                return False
        
        return True
    
    async def execute(self, agent: Any, **kwargs) -> TaskResult:
        """Execute navigation task."""
        result = TaskResult(
            task_id=self.task_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        try:
            await self.pre_execute(agent)
            
            visited_pages = []
            page_data = []
            
            for i, url in enumerate(self.urls):
                try:
                    self.logger.info(f"Navigating to {url} ({i+1}/{len(self.urls)})")
                    await agent.browser.navigate(url)
                    visited_pages.append(url)
                    
                    # Perform actions if specified
                    if i < len(self.actions) and self.actions[i]:
                        action = self.actions[i]
                        await self._perform_action(agent, action)
                    
                    # Collect page info
                    page_info = {
                        "url": url,
                        "title": await agent.browser.get_title(),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    page_data.append(page_info)
                    
                    # Small delay between navigations
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Failed to navigate to {url}: {str(e)}")
                    page_data.append({
                        "url": url,
                        "error": str(e)
                    })
            
            result.data = {
                "visited_pages": visited_pages,
                "page_data": page_data
            }
            result.status = TaskStatus.COMPLETED
            result.metadata = {
                "total_urls": len(self.urls),
                "successfully_visited": len(visited_pages)
            }
            
        except Exception as e:
            self.logger.error(f"Navigation task failed: {str(e)}")
            result.status = TaskStatus.FAILED
            result.error = str(e)
        
        finally:
            result.completed_at = datetime.utcnow()
            await self.post_execute(agent, result)
        
        return result
    
    async def _perform_action(self, agent: Any, action: Dict[str, Any]) -> None:
        """Perform an action on the current page."""
        action_type = action.get("type")
        
        if action_type == "click":
            selector = action.get("selector")
            if selector:
                await agent.browser.click(selector)
                
        elif action_type == "fill":
            selector = action.get("selector")
            value = action.get("value")
            if selector and value:
                await agent.browser.fill(selector, value)
                
        elif action_type == "wait":
            duration = action.get("duration", 1)
            await asyncio.sleep(duration)
            
        elif action_type == "screenshot":
            filename = action.get("filename", f"screenshot_{datetime.utcnow().timestamp()}.png")
            await agent.take_screenshot(filename)


class DataExtractionTask(BaseTask):
    """Task for extracting structured data from websites."""
    
    def __init__(
        self,
        task_id: str,
        url: str,
        extraction_prompt: str,
        output_format: Optional[str] = "json",
        description: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize data extraction task.
        
        Args:
            task_id: Unique task identifier
            url: URL to extract data from
            extraction_prompt: Prompt describing what data to extract
            output_format: Desired output format (json, csv, etc.)
            description: Task description
            **kwargs: Additional task parameters
        """
        super().__init__(
            task_id=task_id,
            description=description or f"Extract data from {url}",
            priority=TaskPriority.HIGH,
            **kwargs
        )
        self.url = url
        self.extraction_prompt = extraction_prompt
        self.output_format = output_format
        
    def validate(self) -> bool:
        """Validate task parameters."""
        if not self.url or not self.url.startswith(('http://', 'https://')):
            self.logger.error(f"Invalid URL: {self.url}")
            return False
        
        if not self.extraction_prompt:
            self.logger.error("No extraction prompt provided")
            return False
        
        return True
    
    async def execute(self, agent: Any, **kwargs) -> TaskResult:
        """Execute data extraction task."""
        result = TaskResult(
            task_id=self.task_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        try:
            await self.pre_execute(agent)
            
            # Navigate to URL
            self.logger.info(f"Navigating to {self.url}")
            await agent.browser.navigate(self.url)
            
            # Use agent to extract data based on prompt
            extraction_task = f"Extract the following data from this webpage: {self.extraction_prompt}. Return the data in {self.output_format} format."
            
            extracted_data = await agent.run(extraction_task)
            
            result.data = extracted_data
            result.status = TaskStatus.COMPLETED
            result.metadata = {
                "url": self.url,
                "extraction_prompt": self.extraction_prompt,
                "output_format": self.output_format
            }
            
        except Exception as e:
            self.logger.error(f"Data extraction task failed: {str(e)}")
            result.status = TaskStatus.FAILED
            result.error = str(e)
        
        finally:
            result.completed_at = datetime.utcnow()
            await self.post_execute(agent, result)
        
        return result