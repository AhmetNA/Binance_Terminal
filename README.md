# Binance Terminal

A professional trading application for Binance cryptocurrency exchange with real-time price monitoring and automated trading capabilities.

## Features

- Real-time price monitoring via WebSocket
- Favorite coins management
- Automated trading with risk management
- Interactive candlestick charts
- User preferences configuration
- Professional GUI built with PySide6

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/binance-terminal.git
cd binance-terminal
```

2. Install dependencies:

```bash
pip install -r requirements.txt
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
binance-terminal/
├── src/                    # Source code
│   ├── core/              # Core configuration and utilities
│   ├── api/               # API client implementations
│   ├── models/            # Data models
│   ├── services/          # Business logic services
│   ├── ui/                # User interface components
│   └── utils/             # Utility functions
├── tests/                 # Test files
├── config/                # Configuration files
├── docs/                  # Documentation
├── scripts/               # Build and utility scripts
└── logs/                  # Application logs
```

## Development

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for development guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is for educational purposes only. Use at your own risk. The authors are not responsible for any financial losses.
