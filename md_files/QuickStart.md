# Quick Start Guide - Testing the Browser Agent

## 1. Initial Setup

### Step 1: Create and Configure Environment

```bash
# Create .env file from template
copy .env.example .env

# Edit .env file and add your API key
# Open .env in a text editor and add:
# OPENAI_API_KEY=your_actual_api_key_here
```

### Step 2: Create Test Directories

```bash
# Create necessary directories
mkdir logs
mkdir output
mkdir screenshots
```

## 2. Test Basic Functionality

### Test 1: Interactive Mode (Easiest)

```bash
python main.py interactive
```

Then try these commands:
- `Navigate to https://quotes.toscrape.com and tell me what the first quote says`
- `Go to https://www.wikipedia.org and extract the featured article title`
- `exit` (to quit)

### Test 2: Simple Web Scraping

First, create a test selector file:

```json
# Save as: test_selectors.json
{
  "quotes": ".quote .text",
  "authors": ".quote .author"
}
```

Run the scraping task:
```bash
python main.py single --task scrape --url https://quotes.toscrape.com --selectors test_selectors.json --output quotes_output.json
```

### Test 3: Data Extraction with AI

```bash
python main.py single --task extract --url https://en.wikipedia.org/wiki/Python_(programming_language) --prompt "Extract the creator's name and the year Python was first released" --output python_info.json
```

## 3. Test Batch Processing

### Create a Simple Batch File

```json
# Save as: test_batch.json
[
  {
    "type": "scrape",
    "task_id": "quotes-page-1",
    "url": "https://quotes.toscrape.com/page/1/",
    "selectors": {
      "quotes": ".quote .text",
      "authors": ".quote .author"
    },
    "description": "Scrape first page of quotes"
  },
  {
    "type": "navigate",
    "task_id": "visit-multiple-pages",
    "urls": [
      "https://quotes.toscrape.com/page/1/",
      "https://quotes.toscrape.com/page/2/"
    ],
    "description": "Navigate through pages"
  },
  {
    "type": "extract",
    "task_id": "extract-python-info",
    "url": "https://www.python.org",
    "extraction_prompt": "What is the latest Python version mentioned on the homepage?",
    "output_format": "json",
    "description": "Extract Python version info"
  }
]
```

Run batch tasks:
```bash
python main.py batch --tasks-file test_batch.json
```

## 4. Test Different Options

### Run in Headless Mode (No Browser Window)
```bash
python main.py single --task scrape --url https://quotes.toscrape.com --selectors test_selectors.json --headless
```

### Enable Debug Logging
```bash
python main.py single --task scrape --url https://quotes.toscrape.com --selectors test_selectors.json --debug
```

## 5. Create Custom Test Scripts

### Simple Test Script

```python
# Save as: test_agent.py
import asyncio
from src.agent.browser_agent_v1 import BrowserAgent

async def test_simple_navigation():
    """Test basic browser navigation."""
    async with BrowserAgent() as agent:
        result = await agent.execute(
            "Navigate to https://www.example.com and tell me the page title"
        )
        print(f"Success: {result.success}")
        print(f"Result: {result.data}")

if __name__ == "__main__":
    asyncio.run(test_simple_navigation())
```

### Test Multiple Tasks

```python
# Save as: test_multiple_tasks.py
import asyncio
from src.agent.browser_agent_v1 import BrowserAgent
from src.tasks.web_tasks import WebScrapingTask, DataExtractionTask

async def test_multiple_tasks():
    """Test multiple task types."""
    async with BrowserAgent() as agent:
        # Test 1: Web Scraping
        scrape_task = WebScrapingTask(
            task_id="test-scrape",
            url="https://quotes.toscrape.com",
            selectors={
                "first_quote": ".quote:first-child .text",
                "first_author": ".quote:first-child .author"
            }
        )
        
        result1 = await agent.execute(scrape_task)
        print(f"Scraping result: {result1.data}")
        
        # Test 2: AI Extraction
        extract_task = DataExtractionTask(
            task_id="test-extract",
            url="https://www.python.org",
            extraction_prompt="What are the main features of Python mentioned?",
            output_format="json"
        )
        
        result2 = await agent.execute(extract_task)
        print(f"Extraction result: {result2.data}")

if __name__ == "__main__":
    asyncio.run(test_multiple_tasks())
```

## 6. Verify Results

After running tests, check:

1. **Output Files**:
   - Check `output/` directory for JSON files
   - Check `logs/` directory for log files
   - Check `screenshots/` if any were taken

2. **Log Files**:
   ```bash
   # View latest logs
   type logs\agent.log
   ```

3. **JSON Output**:
   ```bash
   # View scraped data
   type quotes_output.json
   ```

## 7. Common Test Scenarios

### Test Form Filling

```json
# Save as: search_form.json
{
  "input[name='q']": "browser automation python"
}
```

```bash
python main.py single --task fill_form --url https://www.google.com --form-data search_form.json --submit-selector "input[type='submit']"
```

### Test Navigation with Actions

```json
# Save as: nav_actions.json
[
  {
    "type": "wait",
    "duration": 2
  },
  {
    "type": "screenshot",
    "filename": "page_screenshot.png"
  }
]
```

```bash
python main.py single --task navigate --urls https://quotes.toscrape.com https://quotes.toscrape.com/page/2/ --actions nav_actions.json
```

## 8. Troubleshooting Tests

### If Browser Doesn't Open:
- Check if Chrome is installed
- Try with `--headless` flag
- Check logs for errors

### If API Calls Fail:
- Verify your API key in .env
- Check internet connection
- Try a simpler prompt

### If Selectors Don't Work:
- Visit the website manually
- Use browser DevTools to verify selectors
- Try simpler selectors like "h1" or "p"

## 9. Performance Testing

### Test with Multiple Concurrent Tasks

```python
# Save as: test_concurrent.py
import asyncio
from src.agent.task_executor import TaskExecutor
from src.tasks.web_tasks import WebScrapingTask

async def test_concurrent_execution():
    """Test concurrent task execution."""
    executor = TaskExecutor(max_concurrent_tasks=3)
    await executor.initialize()
    
    # Create multiple tasks
    tasks = []
    for i in range(5):
        task = WebScrapingTask(
            task_id=f"concurrent-{i}",
            url=f"https://quotes.toscrape.com/page/{i+1}/",
            selectors={"quotes": ".quote .text"}
        )
        tasks.append(task)
    
    # Add all tasks
    await executor.add_tasks(tasks)
    
    # Run executor
    executor_task = asyncio.create_task(executor.run())
    
    # Wait for completion
    while await executor.task_queue.size() > 0 or executor.active_tasks:
        await asyncio.sleep(1)
    
    await executor.stop()
    
    # Check results
    results = executor.get_task_results()
    print(f"Completed {len(results)} tasks")

if __name__ == "__main__":
    asyncio.run(test_concurrent_execution())
```

## 10. Next Steps

Once basic tests work:

1. **Customize Tasks**: Modify task parameters for your use case
2. **Add Error Handling**: Test with invalid URLs or selectors
3. **Monitor Performance**: Check execution times in logs
4. **Scale Up**: Try batch processing with more tasks
5. **Create Custom Tasks**: Extend the base classes for your needs

## Quick Reference

```bash
# Interactive mode
python main.py interactive

# Single scraping task
python main.py single --task scrape --url URL --selectors FILE.json

# AI extraction
python main.py single --task extract --url URL --prompt "What to extract"

# Batch processing
python main.py batch --tasks-file tasks.json

# With options
python main.py --headless --debug [mode] [options]
```