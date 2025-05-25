# Browser Agent - AI-Powered Web Automation

A production-ready AI agent system built with the open-source `browser-use` library for intelligent web automation tasks.

## Features

- 🤖 **AI-Powered**: Uses LLMs (GPT-4, Claude) to understand and execute complex web tasks
- 🌐 **Web Automation**: Scraping, form filling, navigation, and data extraction
- ⚡ **Async First**: Built with asyncio for high performance
- 🔄 **Task Queue**: Priority-based task execution with retry mechanisms
- 📊 **Multiple Agents**: Support for concurrent browser instances
- 🛡️ **Production Ready**: Comprehensive error handling, logging, and monitoring
- 🧩 **Modular Design**: Extensible architecture for custom tasks

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/browser-agent-project.git
cd browser-agent-project
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Quick Start

### Single Task Execution

```bash
# Web scraping
python main.py single --task scrape --url https://example.com --selectors selectors.json

# Form filling
python main.py single --task fill_form --url https://example.com --form-data form_data.json

# Data extraction with AI
python main.py single --task extract --url https://example.com --prompt "Extract product prices and names"
```

### Batch Execution

```bash
# Run multiple tasks from a file
python main.py batch --tasks-file examples/example_tasks.json
```

### Interactive Mode

```bash
# Start interactive session
python main.py interactive
```

## Project Structure

```
browser-agent-project/
├── src/
│   ├── agent/          # Core agent implementations
│   ├── config/         # Configuration management
│   ├── tasks/          # Task definitions
│   └── utils/          # Helper utilities
├── tests/              # Test suite
├── examples/           # Example configurations
├── logs/               # Application logs
└── main.py            # Entry point
```

## Configuration

Key configuration options in `.env`:

- `OPENAI_API_KEY`: Your OpenAI API key
- `BROWSER_HEADLESS`: Run browser in headless mode (True/False)
- `AGENT_MAX_STEPS`: Maximum steps per task
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Creating Custom Tasks

```python
from src.tasks.base_task import BaseTask, TaskResult, TaskStatus

class CustomTask(BaseTask):
    def __init__(self, task_id: str, custom_param: str):
        super().__init__(task_id, "Custom task description")
        self.custom_param = custom_param
    
    async def execute(self, agent, **kwargs):
        # Your task logic here
        result = await agent.run(f"Do something with {self.custom_param}")
        
        return TaskResult(
            task_id=self.task_id,
            status=TaskStatus.COMPLETED,
            data=result
        )
```

## API Reference

### BrowserAgent

Main agent class for browser automation:

```python
async with BrowserAgent() as agent:
    result = await agent.execute("Navigate to example.com and extract prices")
```

### TaskExecutor

Manages multiple tasks with concurrent execution:

```python
executor = TaskExecutor(max_concurrent_tasks=5)
await executor.initialize()
await executor.add_tasks(tasks)
await executor.run()
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_agent.py
```

## Monitoring and Logging

- Logs are stored in `logs/` directory
- Structured logging with loguru
- Configurable log levels and formats
- Automatic log rotation and compression

## Security Considerations

- Never commit `.env` files with API keys
- Use `ALLOWED_DOMAINS` to restrict accessible domains
- Implement rate limiting for API calls
- Validate all user inputs
- Run in sandboxed environments for untrusted sites

## Performance Optimization

- Use headless mode in production
- Implement caching for repeated requests
- Batch similar tasks together
- Optimize CSS selectors
- Use appropriate timeouts

## Troubleshooting

### Common Issues

1. **Browser not found**: Install Chrome/Chromium
2. **Timeout errors**: Increase `BROWSER_TIMEOUT`
3. **Memory issues**: Reduce `max_concurrent_tasks`
4. **API rate limits**: Implement exponential backoff

### Debug Mode

Enable debug logging:
```bash
python main.py --debug single --task scrape --url https://example.com
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [browser-use](https://github.com/browser-use/browser-use)
- Powered by OpenAI and Anthropic LLMs
- Inspired by modern web automation needs