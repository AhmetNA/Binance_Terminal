# Binance Terminal

A professional trading application for Binance cryptocurrency exchange with real-time price monitoring and automated trading capabilities.

## Features

- Real-time price monitoring via WebSocket
- Favorite coins management
- Automated trading with risk management
- Interactive candlestick charts
- User preferences configuration
- Professional GUI built with PySide6

## ⚠️ Important Financial Disclaimer

**WARNING: This is a financial trading application that involves real money and cryptocurrency trading.**

- **USE AT YOUR OWN RISK**: Trading cryptocurrencies carries substantial risk of loss and is not suitable for all investors.
- **NO LIABILITY**: The developer(s) of this application are NOT responsible for any financial losses, damages, or consequences resulting from the use of this software.
- **NOT FINANCIAL ADVICE**: This application is a tool only and does not provide financial advice. All trading decisions are your own responsibility.
- **EDUCATIONAL PURPOSE**: This software is provided for educational and informational purposes only.
- **API RISKS**: Using exchange APIs with real accounts involves risks including but not limited to: technical failures, network issues, API changes, and security vulnerabilities.

By using this application, you acknowledge and accept full responsibility for all trading activities and potential losses.

## 🔒 Privacy & Data Security Disclaimer

**IMPORTANT: This application operates entirely on your local machine.**

- **LOCAL OPERATION**: This application runs completely locally on your computer and does NOT send any data to external servers owned or controlled by the developer.
- **NO DATA COLLECTION**: The developer does NOT collect, store, or have access to your API keys, trading data, or any personal information.
- **NO REMOTE SERVERS**: Your sensitive information (API credentials, trading history, portfolio data) remains solely on your local machine.
- **THIRD-PARTY CONNECTIONS**: This application only connects directly to official Binance APIs - no intermediary servers are used.
- **USER RESPONSIBILITY**: You are solely responsible for securing your local environment, API keys, and any data stored by this application.
- **NO LIABILITY FOR DATA BREACHES**: The developer is NOT responsible for any data theft, security breaches, or unauthorized access that may occur on your local system or through Binance's services.

**Security Best Practices:**

- Keep your API keys secure and never share them
- **CRITICAL**: When creating Binance API keys, NEVER enable "Enable Withdrawals" or "Enable Transfers" permissions
- **RECOMMENDED**: Only enable "Enable Spot & Margin Trading" and DISABLE "Enable Futures" for safety
- **USE SPOT TRADING ONLY**: Avoid margin and futures trading as they involve higher risks and potential for greater losses
- Use API keys with minimal required permissions only
- Ensure your local system is secure and up-to-date
- Regularly backup your configuration and trading data
- **TRADING RESPONSIBILITY**: All trading decisions and their consequences are entirely your responsibility

## Installation

1. Clone the repository:

```bash
git clone https://github.com/AhmetNA/binance-terminal.git
cd binance-terminal
```

2. Install dependencies:

```bash
# Install main dependencies
pip install -e .

# For development (includes testing, linting tools)
pip install -e .[dev]

# For building executable
pip install -e .[build]
```

3. Set up your API credentials:

```bash
cp config/.env.example config/.env
# Edit config/.env with your Binance API credentials
```

4. Run the application:

```bash
python src/main.py
```

## Configuration

Edit `config/preferences.txt` to customize:

- Risk percentages for trading
- Favorite coins list
- Chart intervals
- Price volatility settings

## Project Structure

```
binance_terminal_dev/
├── LICENSE                    # MIT License
├── README.md                  # Project documentation
├── pyproject.toml            # Python project configuration
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── run.sh                    # Linux/macOS run script
├── run_app.bat              # Windows run script
├── .gitignore               # Git ignore rules
├── .gitattributes           # Git attributes
├── venv/                    # Virtual environment (if created locally)
├── assets/                  # Application assets
│   └── btc.png             # Bitcoin icon
├── config/                  # Configuration files
│   ├── fav_coins.json      # User's favorite coins
│   ├── preferences.txt     # User preferences
│   └── *.example           # Example configuration files
├── data/                    # Application data storage
│   ├── analytics/          # Performance and analytics data
│   ├── portfolio/          # Portfolio tracking data
│   └── trades/             # Trading history data
├── docs/                    # Documentation
│   └── CONTRIBUTING.md     # Development guidelines
├── logs/                    # Application logs
│   └── binance_terminal_*.log  # Daily log files
├── scripts/                 # Build and utility scripts
│   ├── build_exe.py        # Executable builder
│   ├── run.py              # Application runner
│   ├── setup.py            # Setup utilities
│   └── test_*.py           # Test scripts
├── src/                     # Source code
│   ├── __init__.py         # Package initialization
│   ├── main.py             # Application entry point
│   ├── api/                # External API integrations
│   │   ├── __init__.py
│   │   └── http_client.py  # HTTP client for Binance API
│   ├── config/             # Configuration management
│   │   ├── __init__.py
│   │   ├── constants/      # Application constants
│   │   ├── preferences_manager.py  # Preferences handling
│   │   └── preferences_service.py  # Preferences service layer
│   ├── core/               # Core application logic
│   ├── data/               # Data management layer
│   ├── models/             # Data models and schemas
│   ├── services/           # Business logic services
│   ├── ui/                 # User interface components
│   └── utils/              # Utility functions and helpers
└── tests/                   # Test suite
    ├── __init__.py
    └── unit/               # Unit tests
```

## Development

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for development guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is for educational purposes only. Use at your own risk. The authors are not responsible for any financial losses.
