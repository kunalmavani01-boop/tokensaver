# 🚀 Getting Started with TokenSaver

## What is TokenSaver?

TokenSaver is a self-hosted LLM cost governance stack that helps you:

- 💰 **Save Money** — Eliminate duplicate API calls through intelligent caching
- 🛡️ **Control Usage** — Set budgets and rate limits per user/API key
- 📊 **Monitor Costs** — Real-time analytics and spending alerts
- 🔌 **Easy Integration** — Drop-in replacement for OpenAI API

## 5-Minute Quick Start

### 1. Start TokenSaver

```bash
./start.sh  # Linux/macOS
# or
.\start_tokensaver.ps1  # Windows
```

### 2. Open Manager Dashboard

Visit: **http://localhost:3001/manager/**

### 3. Create an API Key

1. Go to **Settings** → **API Keys**
2. Click **Generate New Key**
3. Copy your API key

### 4. Connect Your App

Replace your OpenAI client:

```python
from openai import OpenAI

# Before (direct OpenAI)
# client = OpenAI(api_key="sk-...")

# After (via TokenSaver)
client = OpenAI(
    base_url="http://localhost:8788/v1",  # TokenSaver proxy
    api_key="sk-..."  # Your OpenAI key
)

# Use normally — TokenSaver handles caching & budgets
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### 5. Monitor in Dashboard

Refresh **http://localhost:3001/manager/** to see:
- API usage by user
- Cost savings from caching
- Budget status
- Anomalies detected

## Key Features

### 💾 Smart Caching

**Exact Match Cache**
```python
# First call: 10 tokens, hits API
response1 = client.chat.completions.create(...)

# Exact same prompt: 0 tokens, instant response from cache
response2 = client.chat.completions.create(...)
```

**Semantic Cache**
```python
# Saves responses for semantically similar prompts
# "What is Python?" and "Tell me about Python" return cached response
```

### 💳 Budget Management

1. Go to **Users** → **Add User**
2. Set monthly budget: $100
3. TokenSaver blocks requests when budget exceeded
4. Receive alerts at 50%, 80%, 100% thresholds

### 📈 Analytics

Dashboard shows:
- Per-model cost breakdown
- Cache hit rates
- Token savings
- User spending trends
- 7-day sparklines

### 🔔 Alerts

**Slack Alerts**
```
1. Settings → Integrations → Slack
2. Add webhook URL
3. Get notifications for budget thresholds
```

**Email Alerts**
```
1. Settings → Email Configuration
2. Configure SMTP
3. Receive budget alerts via email
```

## Common Use Cases

### Use Case 1: Development Team Cost Control

```
Team Budget: $500/month
├── Alice (ML Engineer): $150/month limit
├── Bob (Data Scientist): $200/month limit
└── Charlie (Product): $150/month limit
```

TokenSaver prevents overspend and alerts on anomalies.

### Use Case 2: Multi-Tenant SaaS

```
Customer A: $1000/month budget
Customer B: $500/month budget
Customer C: $250/month budget
```

Each customer gets isolated tracking and budget enforcement.

### Use Case 3: Cost Optimization

- Identify expensive API calls
- Find duplicate queries (caching opportunities)
- Detect usage anomalies
- Optimize prompts based on cost per request

## Next Steps

1. **[Installation Guide](./INSTALLATION.md)** — Detailed setup instructions
2. **[Configuration](./CONFIGURATION.md)** — Advanced settings
3. **[API Reference](./API.md)** — Integration guide
4. **[FAQ](./FAQ.md)** — Common questions

## Need Help?

- 📧 Email: kunalmavani@outlook.com
- 🐛 [Report Issues](https://github.com/kunalmavani01-boop/tokensaver/issues)
- 💬 [Discussions](https://github.com/kunalmavani01-boop/tokensaver/discussions)
