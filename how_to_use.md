# How to Use the Browser Agent System

Now that you have Gemini working, here's how to use the complete browser automation system we built.

## 🚀 Quick Start

### 1. Set Up Your Environment

First, make sure your `.env` file has your Gemini API key:

```env
GOOGLE_API_KEY=your_actual_gemini_api_key
LLM_MODEL=gemini-1.5-flash
BROWSER_HEADLESS=False  # Set to True to hide browser window
LOG_LEVEL=INFO
```

### 2. Three Ways to Use the System

## 📝 Method 1: Interactive Mode (Easiest)

This is the best way to start - just type what you want the browser to do:

```bash
python main.py interactive
```

Then type commands like:
- `Go to amazon.com and search for "laptop"`
- `Navigate to https://news.ycombinator.com and tell me the top 3 stories`
- `Visit wikipedia.org and find information about Python programming`
- `Go to quotes.toscrape.com and extract all quotes about life`
- Type `exit` to quit

## 🔧 Method 2: Single Task Mode

Run specific pre-defined tasks:

### A. Web Scraping Task

First create a `selectors.json` file:
```json
{
  "titles": "h3.title",
  "prices": ".price",
  "descriptions": ".description"
}
```

Then run:
```bash
python main.py single --task scrape --url https://example.com --selectors selectors.json
```

### B. AI Extraction Task (Easier - No Selectors Needed!)

```bash
# Extract specific information using natural language
python main.py single --task extract --url https://www.python.org --prompt "Find the latest Python version and release date"

# More examples
python main.py single --task extract --url https://en.wikipedia.org/wiki/Artificial_intelligence --prompt "What are the main types of AI mentioned?"

python main.py single --task extract --url https://news.ycombinator.com --prompt "List the top 5 stories with their points"
```

### C. Form Filling Task

Create `form_data.json`:
```json
{
  "input[name='search']": "Python tutorials",
  "select[name='category']": "Programming"
}
```

Run:
```bash
python main.py single --task fill_form --url https://example.com/search --form-data form_data.json --submit-selector "button[type='submit']"
```

### D. Navigation Task

```bash
# Visit multiple pages
python main.py single --task navigate --urls https://example.com https://example.com/about https://example.com/contact
```

## 📦 Method 3: Batch Mode (Multiple Tasks)

Create a `tasks.json` file with multiple tasks:

```json
[
  {
    "type": "extract",
    "task_id": "get-python-info",
    "url": "https://www.python.org",
    "extraction_prompt": "What is the latest Python version?",
    "description": "Extract Python version"
  },
  {
    "type": "extract",
    "task_id": "get-news",
    "url": "https://news.ycombinator.com",
    "extraction_prompt": "What are the top 3 stories?",
    "description": "Get top HN stories"
  },
  {
    "type": "scrape",
    "task_id": "get-quotes",
    "url": "https://quotes.toscrape.com",
    "selectors": {
      "quotes": ".quote .text",
      "authors": ".quote .author"
    },
    "description": "Scrape quotes"
  }
]
```

Run all tasks:
```bash
python main.py batch --tasks-file tasks.json
```

## 💡 Practical Examples

### Example 1: Research Task
```bash
# Interactive mode
python main.py interactive

# Then type:
> Go to Google Scholar and search for "machine learning trends 2024"
> Extract the titles and authors of the first 5 papers
> Navigate to the first paper and summarize its abstract
```

### Example 2: Price Monitoring
```bash
python main.py single --task extract --url https://www.amazon.com/dp/B08N5WRWNW --prompt "What is the current price and availability?"
```

### Example 3: News Aggregation
```bash
# Create news_tasks.json
[
  {
    "type": "extract",
    "task_id": "tech-news",
    "url": "https://techcrunch.com",
    "extraction_prompt": "What are the top 5 headlines?",
    "description": "Get TechCrunch headlines"
  },
  {
    "type": "extract", 
    "task_id": "hn-news",
    "url": "https://news.ycombinator.com",
    "extraction_prompt": "What are the top 5 stories with most points?",
    "description": "Get HackerNews top stories"
  }
]

# Run
python main.py batch --tasks-file news_tasks.json
```

### Example 4: Website Monitoring
```bash
# Check if a product is in stock
python main.py single --task extract --url https://store.example.com/product --prompt "Is this item in stock? What's the price?"

# Monitor for changes
python main.py single --task extract --url https://example.com/status --prompt "What is the current system status?"
```

## 🛠️ Advanced Usage

### Use Custom Python Scripts

Create your own scripts using the browser agent:

```python
# my_automation.py
import asyncio
from src.agent.browser_agent import BrowserAgent

async def my_custom_task():
    async with BrowserAgent() as agent:
        # Task 1: Get news
        result = await agent.execute(
            "Go to BBC News and tell me the main headline"
        )
        print(f"BBC Headline: {result.data}")
        
        # Task 2: Search for something
        result = await agent.execute(
            "Go to Google and search for 'Python tutorials 2024'"
        )
        print(f"Search completed: {result.success}")
        
        # Task 3: Extract data
        result = await agent.execute(
            "Extract the first 3 search results with their titles and URLs"
        )
        print(f"Results: {result.data}")

# Run it
asyncio.run(my_custom_task())
```

### Command Line Options

```bash
# Run in headless mode (no browser window)
python main.py --headless single --task extract --url https://example.com --prompt "Get page title"

# Enable debug logging
python main.py --debug interactive

# Specify output file
python main.py single --task scrape --url https://example.com --selectors selectors.json --output results.json
```

## 📊 Viewing Results

### Check Output Files
```bash
# View JSON output
type output\*.json

# View logs
type logs\agent.log
```

### Results Location
- **JSON outputs**: `output/` directory
- **Logs**: `logs/agent.log`
- **Screenshots**: `screenshots/` directory

## 🎯 Best Practices

1. **Start with Interactive Mode** to understand what the agent can do
2. **Use Extract Tasks** for most scraping - they're easier than writing selectors
3. **Be Specific** in your prompts for better results
4. **Check Logs** if something doesn't work: `type logs\agent.log`
5. **Run Headless** for faster execution: `--headless` flag

## 🔍 Troubleshooting

### If the browser doesn't open:
```bash
python main.py --headless interactive
```

### If tasks fail:
1. Check logs: `type logs\agent.log`
2. Try a simpler version of the task
3. Make sure the website is accessible
4. Try with a different URL

### To see what's happening:
```bash
# Run with debug mode and visible browser
python main.py --debug interactive
# Don't use --headless so you can see the browser
```

## 🚀 Quick Reference

```bash
# Interactive mode (easiest)
python main.py interactive

# Extract data with AI
python main.py single --task extract --url URL --prompt "What to extract"

# Scrape with selectors
python main.py single --task scrape --url URL --selectors file.json

# Run multiple tasks
python main.py batch --tasks-file tasks.json

# Common flags
--headless    # Hide browser window
--debug       # Show debug logs
--output      # Specify output file
```

## Next Steps

1. Try interactive mode first
2. Create some extract tasks for websites you're interested in
3. Set up a batch file for regular monitoring
4. Build custom scripts for complex workflows

The system is now ready to automate your web tasks with Gemini!