# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UV Alert Vitoria-Gasteiz is a UV radiation monitoring system that sends Telegram alerts when UV levels become dangerous. The system is specifically designed for people with photosensitivity or taking photosensitizing medication in Vitoria-Gasteiz, Spain.

## Architecture

### Core Components

- **uv_monitor.py**: Main monitoring service that runs continuously, checking UV levels and sending alerts
- **openweather_api.py**: API client for OpenWeatherMap UV Index service with fallback time-based estimation
- **test_telegram.py**: Configuration test script for Telegram bot setup

### Key Features

- OpenWeatherMap UV Index API integration for real-time UV data
- Fallback UV estimation based on time of day and season when API is unavailable
- Telegram bot integration for real-time alerts
- Bidirectional alerts: dangerous UV levels AND when UV drops to safe levels
- Skin type-based safe exposure time calculations
- 50% exposure time reduction for photosensitizing medication
- Docker containerization with health monitoring

## Development Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Test Telegram configuration
python3 test_telegram.py

# Run the monitor locally (requires .env file)
python3 uv_monitor.py
```

### Docker Operations
```bash
# Build local image
docker build -t uv-alert-vitoria .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Pull and update
docker-compose pull && docker-compose up -d
```

### Testing and Debugging
```bash
# Check current UV estimate
python3 estimate_uv_now.py

# Get current UV from API
python3 check_uv_now.py

# Test Telegram bot
python3 test_telegram.py
```

## Configuration

### Required Environment Variables
- `TELEGRAM_BOT_TOKEN`: Bot token from @BotFather
- `TELEGRAM_CHAT_ID`: User ID from @userinfobot

### Optional Configuration
- `UV_THRESHOLD`: UV index threshold for alerts (default: 6)
- `SKIN_TYPE`: Skin type 1-6 for exposure calculations (default: 2)
- `CHECK_INTERVAL_MINUTES`: Minutes between checks (default: 30)
- `OPENWEATHER_API_KEY`: OpenWeatherMap API key for real-time UV data

## Code Architecture Notes

### UV Calculation Logic
- Base exposure times per skin type are hardcoded in `calculate_safe_exposure_time()`
- Times are automatically reduced by 50% for photosensitizing medication
- UV level descriptions and emojis are mapped in `get_uv_level_description()`

### API Integration
- Primary: OpenWeatherMap UV Index API (free tier: 1000 calls/day)
- Fallback: Time-based UV estimation when API fails or is unavailable
- Simple REST API with API key authentication

### Alert System
- Bidirectional state-based alerting (dangerous ↔ safe transitions)
- Different message templates for dangerous vs safe conditions
- Includes calculated safe exposure times in alerts
- Alerts when UV rises above threshold AND when it drops below threshold

### Error Handling
- Comprehensive logging to both console and file
- Graceful degradation when APIs fail
- Required environment variable validation on startup

## Deployment

The application is containerized and available on Docker Hub as `alexdiazdecerio/uv-alert-vitoria`. It's designed to run continuously as a daemon service, particularly suited for Raspberry Pi deployments.