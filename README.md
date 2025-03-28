# Sentry Profile Hours Testing Tool

A tool for testing Sentry profile hours billing with different profile types, platforms, and generation methods.

## Overview

This tool allows you to quickly generate profile data to test how Sentry bills for profile hours. It supports:

- Both transaction-based and continuous profiling
- UI and backend platform profiles
- Both AM2 and AM3 billing plans
- Direct profile generation to create large volumes of data quickly

## Quick Start

```bash
# Install dependencies with uv
uv pip install -r requirements.txt

# Run with a preset to generate profile hours
uv run hello.py
```

## Setup with uv

This project uses [uv](https://github.com/astral-sh/uv), a modern Python package installer and resolver written in Rust.

### Installing uv

```bash
# Install with curl (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

### Project Setup

```bash
# Create a virtual environment
uv venv

# Install dependencies
uv pip install -r requirements.txt

# Alternatively, use the pyproject.toml
uv pip install -e .
```

### Running the Script

```bash
# Run the script directly (automatically activates virtual environment)
uv run hello.py

# Or run with specific parameters
uv run -- python hello.py
```

### Adding Dependencies

```bash
# Add new dependencies
uv add sentry-sdk

# Or with a specific version
uv add 'sentry-sdk==1.35.0'

# Create/update requirements.txt
uv pip compile pyproject.toml -o requirements.txt
```

## Configuration

The script is highly configurable through presets or manual configuration. Edit the configuration variables at the top of `hello.py`:

### Using Presets

Set the `PRESET` variable to quickly switch between common testing configurations:

```python
# Use a preset for quick configuration
PRESET = "DIRECT_AM3_CONTINUOUS_UI"  # Fast UI profile hours for AM3
MOCK_DURATION_HOURS = 5.0  # Generate 5 hours of profile data
```

Available presets include:

- **AM2 Plan Presets**: `AM2_TRANSACTION_BACKEND`, `AM2_TRANSACTION_UI`, `AM2_CONTINUOUS_BACKEND`, `AM2_CONTINUOUS_UI`
- **AM3 Plan Presets**: `AM3_TRANSACTION_BACKEND`, `AM3_TRANSACTION_UI`, `AM3_CONTINUOUS_BACKEND`, `AM3_CONTINUOUS_UI`
- **Fast Generation (AM2)**: `DIRECT_AM2_TRANSACTION_BACKEND`, `DIRECT_AM2_TRANSACTION_UI`, `DIRECT_AM2_CONTINUOUS_BACKEND`, `DIRECT_AM2_CONTINUOUS_UI`
- **Fast Generation (AM3)**: `DIRECT_AM3_TRANSACTION_BACKEND`, `DIRECT_AM3_TRANSACTION_UI`, `DIRECT_AM3_CONTINUOUS_BACKEND`, `DIRECT_AM3_CONTINUOUS_UI`
- **Special Modes**: `CUSTOM` (use settings below), `DISABLED` (use manual configuration)

### Manual Configuration

When not using presets (`PRESET = "DISABLED"`), configure the script manually:

```python
# Profile type: "transaction" or "continuous"
PROFILE_TYPE = "continuous"

# Platform: "python" (backend) or "javascript", "android", "cocoa" (UI platforms)
PLATFORM = "javascript"

# Fast generation mode
DIRECT_CHUNK_GENERATION = True

# Hours to simulate
MOCK_DURATION_HOURS = 10.0

# DSN to use
SELECTED_DSN = "profile-hours-am3-business"
```

## Understanding Profile Hours Billing

Sentry offers different billing models for profiling:

- **AM2 Plans**:
  - Have separate billing for transaction-based profiling
  - Have continuous profiling (UI and non-UI) billing

- **AM3 Plans**:
  - Transaction-based profiling is automatically converted to profile hours
  - All profiling is billed as profile hours (UI or non-UI depending on platform)

## Key Features

- **Preset System**: Easy switching between common configurations
- **DSN Selection**: Test against different plan types
- **Direct Generation**: Generate hours of profile data in seconds
- **Platform Spoofing**: Test both UI and backend profile hours
- **Detailed Reporting**: Console output shows exactly what's being tested

## Project Structure

- **hello.py**: Main script for generating profile data
- **pyproject.toml**: Project dependencies and metadata
- **CLAUDE.md**: Contains detailed documentation about Sentry profiling architecture

## Advanced Usage

See `CLAUDE.md` for detailed technical information about Sentry profiling internals, how Relay processes profiles, and the specific strategies used for profile generation.