# Contributing to Binance Terminal

Thank you for your interest in contributing to Binance Terminal! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork the repository
2. Clone your fork:

   ```bash
   git clone https://github.com/yourusername/binance-terminal.git
   ```

3. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

## Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions small and focused

## Testing

Run tests before submitting:

```bash
python -m pytest tests/
```

## Submitting Changes

1. Create a feature branch:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit:

   ```bash
   git add .
   git commit -m "Add your descriptive commit message"
   ```

3. Push to your fork and submit a pull request

## Reporting Issues

Please use the GitHub issue tracker to report bugs or request features. Include:

- Python version
- Operating system
- Steps to reproduce the issue
- Expected vs actual behavior
