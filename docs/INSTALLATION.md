# 📦 Installation Guide

## Prerequisites

- Python >= 3.10
- pip or conda
- Docker (optional, for containerized deployment)

## Native Installation

### Linux / macOS

```bash
# Clone the repository
git clone https://github.com/kunalmavani01-boop/tokensaver.git
cd tokensaver

# Install dependencies
pip install -r requirements.txt

# Start TokenSaver
./start.sh
```

The application will be available at:
- **Manager UI**: http://127.0.0.1:3001/manager/
- **Caching Proxy**: http://127.0.0.1:8788/v1

### Windows (PowerShell)

```powershell
# Clone the repository
git clone https://github.com/kunalmavani01-boop/tokensaver.git
cd tokensaver

# Install dependencies
pip install -r requirements.txt

# Start TokenSaver
.\start_tokensaver.ps1
```

## Docker Installation

### Using Docker Compose

```bash
# Clone the repository
git clone https://github.com/kunalmavani01-boop/tokensaver.git
cd tokensaver

# Start with Docker
docker-compose up
```

Services will be available at:
- **Manager**: http://localhost:3001/manager/
- **Proxy**: http://localhost:8788/v1
- **Database**: SQLite at `./data/savings.db`

### Building Custom Image

```bash
docker build -t tokensaver:latest .
docker run -p 3001:3001 -p 8788:8788 tokensaver:latest
```

## Environment Configuration

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Manager Settings
TOKENSAVER_MANAGER_PORT=3001
TOKENSAVER_DB_PATH=./data/savings.db

# Proxy Settings
TOKENSAVER_PROXY_PORT=8788
TOKENSAVER_PROXY_UPSTREAM=https://api.openai.com

# API Keys
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=your-key-here

# Alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Email (SMTP)
TOKENSAVER_SMTP_HOST=smtp.gmail.com
TOKENSAVER_SMTP_PORT=587
TOKENSAVER_SMTP_USER=your-email@gmail.com
TOKENSAVER_SMTP_PASSWORD=your-app-password
TOKENSAVER_SMTP_FROM=tokensaver@yourdomain.com

# License
TOKENSAVER_LICENSE_KEY=dev-mode
```

## Verify Installation

```bash
# Check if services are running
curl http://127.0.0.1:3001/health
curl http://127.0.0.1:8788/health
```

## Troubleshooting

### Port Already in Use

```bash
# Change ports in .env
TOKENSAVER_MANAGER_PORT=3002
TOKENSAVER_PROXY_PORT=8789
```

### Python Version Issues

```bash
# Verify Python version
python --version

# Use virtual environment
python3.10 -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate  # Windows
```

## Next Steps

- [Getting Started](./GETTING_STARTED.md)
- [Configuration](./CONFIGURATION.md)
- [API Reference](./API.md)
