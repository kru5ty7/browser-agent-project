# Windows Installation Guide

## Troubleshooting Build Errors

If you encounter build errors with Visual Studio/Ninja, follow these steps:

### Method 1: Use Minimal Requirements (Recommended)

1. First, upgrade pip:
```bash
python -m pip install --upgrade pip
```

2. Install minimal requirements:
```bash
pip install -r requirements-minimal.txt
```

3. Install additional packages one by one:
```bash
# If you need pandas/numpy for data processing
pip install pandas --no-build-isolation
pip install numpy --no-build-isolation

# If you need lxml for better HTML parsing
pip install lxml --no-build-isolation
```

### Method 2: Install Pre-built Wheels

For packages that fail to build, install pre-built wheels from unofficial sources:

1. Visit https://www.lfd.uci.edu/~gohlke/pythonlibs/
2. Download the appropriate wheel for your Python version
3. Install with: `pip install path/to/downloaded.whl`

### Method 3: Use Conda Instead

If pip continues to have issues:

```bash
# Install Miniconda or Anaconda
# Then use conda to install packages
conda install -c conda-forge pandas numpy lxml
```

### Method 4: Install Visual Studio Build Tools

If you need to build from source:

1. Download Visual Studio Build Tools from https://visualstudio.microsoft.com/downloads/
2. Install with C++ build tools
3. Restart your terminal
4. Try pip install again

## Specific Package Solutions

### For `lxml` errors:
```bash
# Option 1: Use pre-built wheel
pip install lxml --prefer-binary

# Option 2: Use alternative parser in code
# Change: BeautifulSoup(html, 'lxml')
# To: BeautifulSoup(html, 'html.parser')
```

### For `pandas`/`numpy` errors:
```bash
# These are optional for basic functionality
# You can skip them initially
```

### For `playwright` errors:
```bash
# Playwright requires additional setup
# Use selenium instead for simpler installation
```

## Verifying Installation

Test your installation:

```python
# test_install.py
try:
    import browser_use
    print("✓ browser-use installed")
except ImportError:
    print("✗ browser-use not installed")

try:
    import langchain
    print("✓ langchain installed")
except ImportError:
    print("✗ langchain not installed")

try:
    import selenium
    print("✓ selenium installed")
except ImportError:
    print("✗ selenium not installed")

print("\nInstallation check complete!")
```

## Chrome/Chromium Setup

Browser-use requires Chrome or Chromium:

1. Download Chrome from https://www.google.com/chrome/
2. Or download Chromium from https://www.chromium.org/
3. Make sure it's in your system PATH

## Running the Agent

After successful installation:

```bash
# Set up environment
copy .env.example .env
# Edit .env with your API keys

# Test with a simple task
python main.py interactive
```

## Common Windows Issues

### Issue: "Microsoft Visual C++ 14.0 is required"
**Solution**: Install Visual Studio Build Tools or use pre-built wheels

### Issue: "ninja: build stopped"
**Solution**: Use requirements-minimal.txt instead of full requirements.txt

### Issue: "ImportError: DLL load failed"
**Solution**: Install Visual C++ Redistributable from Microsoft

### Issue: "No module named 'browser_use'"
**Solution**: Make sure to install browser-use with: `pip install browser-use`

## Getting Help

If you still have issues:
1. Check the exact error message
2. Try installing packages one by one
3. Use virtual environment to avoid conflicts
4. Consider using WSL (Windows Subsystem for Linux) for better compatibility