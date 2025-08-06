# Krona 📊

[![Release](https://img.shields.io/github/v/release/Sjoeborg/krona)](https://img.shields.io/github/v/release/Sjoeborg/krona)
[![Build status](https://img.shields.io/github/actions/workflow/status/Sjoeborg/krona/master.yml?branch=master)](https://github.com/Sjoeborg/krona/actions/workflows/master.yml?query=branch%3Amaster)
[![codecov](https://codecov.io/gh/Sjoeborg/krona/branch/main/graph/badge.svg)](https://codecov.io/gh/Sjoeborg/krona)
[![Commit activity](https://img.shields.io/github/commit-activity/m/Sjoeborg/krona)](https://img.shields.io/github/commit-activity/m/Sjoeborg/krona)
[![License](https://img.shields.io/github/license/Sjoeborg/krona)](https://img.shields.io/github/license/Sjoeborg/krona)
**KRONA Rapidly Organizes Nordic Assets** - A powerful transaction processing tool for Nordic brokers with multiple user interface options and advanced portfolio analytics.

## Features

### Core Functionality
- 📈 Process transactions from Nordic brokers (Avanza, Nordnet)
- 🎯 Smart symbol mapping with fuzzy matching
- 🖥️ Multiple UI modes: CLI, TUI, and Web UI
- 📊 Portfolio position tracking
- 💰 Dividend and fee calculation
- 🔄 Transaction history analysis

### Analytics Dashboard (Inspired by Dolphie)
- 📈 **Interactive Charts**: Portfolio value, transaction volume, asset allocation
- 📊 **Real-time Statistics**: Live portfolio metrics and performance indicators
- 🎨 **Modern TUI**: Professional terminal interface with sidebar navigation
- 🔄 **Dynamic Updates**: Real-time chart updates and data refresh
- 📋 **Drill-down Analysis**: Click positions to view detailed transaction history
- 🎛️ **Toggle Controls**: Interactive switches to customize chart displays

## Installation

```bash
# Clone the repository
git clone https://github.com/Sjoeborg/krona.git
cd krona

# Install dependencies
uv sync

# Or using pip
pip install -e .
```

## Usage

Krona offers three different user interface modes:

### 1. Command Line Interface (CLI) - Rich-based
Traditional command-line interface with Rich formatting:

```bash
uv run python -m krona.main --ui cli [path]
```

### 2. Terminal User Interface (TUI) - Textual-based ⭐ Default
Modern terminal interface with interactive features:

```bash
uv run python -m krona.main --ui tui [path]
# or simply
uv run python -m krona.main [path]
```

### 3. Web User Interface (Web) - Browser-based
Modern web interface accessible via browser (requires separate `textual-web` installation):

```bash
# First install textual-web (one-time setup)
pipx install textual-web

# Then run with web UI
uv run python -m krona.main --ui web [path] [--host localhost] [--port 8000]
```

### Command Line Arguments

```bash
uv run python -m krona.main --help

usage: main.py [-h] [--ui {cli,tui,web}] [--host HOST] [--port PORT] [path]

KRONA - Rapidly Organizes Nordic Assets

positional arguments:
  path               Path to directory containing transaction files (default: files)

options:
  -h, --help         show this help message and exit
  --ui {cli,tui,web} User interface mode: cli (Rich CLI), tui (Textual TUI), web (Web UI) (default: tui)
  --host HOST        Host address for web UI (default: localhost)
  --port PORT        Port for web UI (default: 8000)
```

## User Interface Comparison

| Feature | CLI | TUI | Web |
|---------|-----|-----|-----|
| Interactive mapping | ❌ | ✅ | ✅ |
| Analytics dashboard | ❌ | ✅ | ✅ |
| Interactive charts | ❌ | ✅ | ✅ |
| Real-time statistics | ❌ | ✅ | ✅ |
| Sidebar navigation | ❌ | ✅ | ✅ |
| Progress tracking | ❌ | ✅ | ✅ |
| Position drill-down | ❌ | ✅ | ✅ |
| Transaction history | ❌ | ✅ | ✅ |
| Bulk operations | ❌ | ✅ | ✅ |
| Portfolio analytics | ❌ | ✅ | ✅ |
| Remote access | ❌ | ❌ | ✅* |
| Mobile friendly | ❌ | ❌ | ✅* |

_* Requires separate `textual-web` installation via `pipx install textual-web`_

## TUI Features (Enhanced with Dolphie-inspired Analytics)

The Terminal User Interface (TUI) provides a comprehensive analytics dashboard:

### Navigation & Layout
- **📊 Sidebar Navigation**: Switch between Symbol Mappings, Portfolio, Analytics, and Settings
- **🎨 Modern Interface**: Professional color scheme with icons and visual indicators
- **🔄 Real-time Updates**: Dynamic data refresh and interactive elements

### Symbol Mapping Management
- **✅ Interactive Mapping**: Click rows to toggle suggestion acceptance
- **📊 Progress Tracking**: Visual progress bar for mapping completion
- **🔄 Bulk Operations**: Accept All, Decline All, Regenerate buttons
- **🎯 Smart Filtering**: Confidence-based suggestion sorting

### Portfolio Dashboard
- **📈 Dashboard Stats**: Live portfolio overview with key metrics
- **🔄 Filter Controls**: Show open/closed positions, refresh data
- **💎 Enhanced Display**: Color-coded P&L, status indicators, emojis
- **📋 Transaction Drill-down**: Click positions to view transaction details

### Analytics Charts
- **📊 Portfolio Value**: Track portfolio value over time with toggleable metrics
- **📈 Transaction Volume**: Analyze buy/sell/dividend transaction patterns
- **🥧 Asset Allocation**: Visual portfolio allocation with percentage breakdowns
- **💹 Performance Metrics**: Realized P&L analysis and performance tracking
- **🎛️ Interactive Controls**: Toggle chart elements, refresh data, customize views

## Web UI Features

The Web User Interface provides all TUI features plus:

- **Browser Access**: Access from any device with a web browser
- **Remote Operation**: Run on server, access from anywhere
- **Mobile Support**: Touch-friendly interface for mobile devices
- **Auto-open**: Automatically opens browser when started

## Examples

### Process Avanza transactions with TUI (default)
```bash
uv run python -m krona.main ~/Downloads/transactions/
```

### Use traditional CLI interface
```bash
uv run python -m krona.main --ui cli ~/Downloads/transactions/
```

### Start web interface on custom port
```bash
uv run python -m krona.main --ui web ~/Downloads/transactions/ --port 3000
```

### Start web server accessible from network
```bash
uv run python -m krona.main --ui web ~/Downloads/transactions/ --host 0.0.0.0 --port 8080
```

### Try the analytics demo
```bash
uv run python demo_analytics.py
```

## Technical Stack

Built with modern Python technologies:

- **🖥️ Textual**: Advanced terminal user interface framework
- **📊 PlotExt**: Terminal-based charting and data visualization
- **🎨 Rich**: Enhanced text rendering and formatting
- **⚡ Polars**: High-performance data processing
- **🔗 httpx**: Modern HTTP client for data fetching

## Architecture

The project follows a clean modular architecture:

- **@krona/parsers/**: Transaction file parsers for different brokers
- **@krona/processor/**: Core business logic for transaction processing
- **@krona/ui/**: User interface implementations (CLI, TUI, Web)
  - **charts.py**: Analytics dashboard with interactive charts
  - **tui.py**: Main terminal interface inspired by Dolphie
  - **cli.py**: Traditional command-line interface
- **@krona/models/**: Data models (Transaction, Position, Suggestion, etc.)
- **@krona/utils/**: Utility functions and helpers

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.