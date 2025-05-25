# Google Gemini Integration Guide

## Current Support

The current implementation supports:
- ✅ OpenAI (GPT-3.5, GPT-4)
- ✅ Anthropic (Claude)
- ❌ Google Gemini (needs modification)

## Adding Gemini Support

### Step 1: Install Required Package

```bash
pip install google-generativeai langchain-google-genai
```

### Step 2: Update requirements.txt

Add to requirements.txt:
```
google-generativeai>=0.3.0
langchain-google-genai>=0.0.5
```

### Step 3: Update .env file

Add your Gemini API key:
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

### Step 4: Update config/settings.py

Add Gemini configuration:
```python
# Add to Settings class
google_api_key: Optional[str] = Field(None, env="GOOGLE_API_KEY")
```

### Step 5: Update agent/browser_agent_v1.py

Replace the `_create_llm` method with this updated version:

```python
def _create_llm(self) -> Union[ChatOpenAI, ChatAnthropic, ChatGoogleGenerativeAI]:
    """Create LLM instance based on configuration."""
    # OpenAI
    if settings.openai_api_key and "gpt" in settings.llm_model:
        from langchain.chat_models import ChatOpenAI
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model_name=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
    
    # Anthropic
    elif settings.anthropic_api_key and "claude" in settings.llm_model:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            api_key=settings.anthropic_api_key,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
    
    # Google Gemini
    elif settings.google_api_key and "gemini" in settings.llm_model:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            google_api_key=settings.google_api_key,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_output_tokens=settings.llm_max_tokens
        )
    
    else:
        raise ValueError("No valid LLM API key provided")
```

### Step 6: Update .env.example

Add Gemini configuration:
```
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_gemini_api_key_here

# LLM Configuration (options: gpt-4, gpt-3.5-turbo, claude-3-opus, gemini-pro)
LLM_MODEL=gemini-pro
```

## Available Gemini Models

- `gemini-pro` - Best for most tasks
- `gemini-pro-vision` - For multimodal tasks (if needed)
- `gemini-1.5-pro` - Latest model with better performance

## Complete Updated Files

### Updated browser_agent_v1.py imports:
```python
from typing import Any, Dict, Optional, Union
from langchain.chat_models import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
```

### Test with Gemini

```bash
# Set environment variable
set LLM_MODEL=gemini-pro

# Or update .env file
LLM_MODEL=gemini-pro
GOOGLE_API_KEY=your_key_here

# Run test
python main.py interactive
```

## Cost Comparison

| Model | Cost per 1K tokens (Input/Output) | Best For |
|-------|-----------------------------------|----------|
| GPT-3.5 | $0.0005 / $0.0015 | Fast, cheap tasks |
| GPT-4 | $0.03 / $0.06 | Complex reasoning |
| Gemini-Pro | Free (with limits) | General use |
| Claude-3 | $0.015 / $0.075 | Long contexts |

## Limitations

- Gemini has different rate limits
- Some prompting styles may need adjustment
- Vision capabilities require different setup

## Alternative: Direct Gemini Implementation

If you prefer to use Gemini directly without LangChain:

```python
import google.generativeai as genai

class GeminiAgent:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def generate(self, prompt: str) -> str:
        response = await self.model.generate_content_async(prompt)
        return response.text
```

## Quick Test Script for Gemini

```python
# test_gemini.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

# Test
response = model.generate_content("Hello! Can you see this?")
print(response.text)
```

## Troubleshooting Gemini

1. **API Key Issues**: Get key from https://makersuite.google.com/app/apikey
2. **Rate Limits**: Free tier has 60 requests per minute
3. **Region Restrictions**: Some regions may not have access
4. **Model Availability**: Check if model name is correct