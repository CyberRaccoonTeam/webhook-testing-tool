# Webhook Testing Tool

> Test and debug webhooks in real-time. Get a unique URL, receive payloads, inspect everything.

![Status](https://img.shields.io/badge/Status-MVP-green)
![Stack](https://img.shields.io/badge/Stack-Python%2FFlask-blue)

---

## Features

- **Unique Endpoint URLs** - Each user gets a unique webhook endpoint
- **Real-time Payload Inspection** - See incoming webhooks instantly
- **Request Details** - Headers, body, method, timestamp
- **Signature Verification** - Validate webhook signatures (HMAC-SHA256)
- **Retry Simulation** - Test retry logic with configurable delays
- **Export History** - Download webhook history as JSON
- **Dark Mode UI** - Easy on the eyes

---

## Quick Start

```bash
# Install dependencies
pip install flask flask-socketio

# Run the server
python app.py

# Open http://localhost:5559
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/endpoints` | POST | Create a new webhook endpoint |
| `/api/endpoints/:id` | GET | Get endpoint details |
| `/api/endpoints/:id/webhooks` | GET | List received webhooks |
| `/webhook/:id` | ANY | Receive webhook payloads |
| `/api/endpoints/:id/export` | GET | Export webhook history |

---

## Usage Example

```bash
# Create an endpoint
curl -X POST http://localhost:5559/api/endpoints

# Response
{
  "id": "abc123",
  "url": "http://localhost:5559/webhook/abc123",
  "created_at": "2026-03-13T10:00:00Z"
}

# Send a test webhook
curl -X POST http://localhost:5559/webhook/abc123 \
  -H "Content-Type: application/json" \
  -d '{"event": "test", "data": "hello world"}'

# View received webhooks
curl http://localhost:5559/api/endpoints/abc123/webhooks
```

---

## Revenue Model

- **Free Tier:** 100 webhooks/day, 24h retention
- **Pro ($9/mo):** Unlimited webhooks, 30-day retention, signature verification
- **Team ($29/mo):** Multiple endpoints, team sharing, API access

---

## Tech Stack

- **Backend:** Python 3.11, Flask, Flask-SocketIO
- **Database:** SQLite (upgradeable to PostgreSQL)
- **Frontend:** Vanilla JS, CSS (dark theme)
- **Real-time:** WebSocket for instant updates

---

## Roadmap

- [x] MVP - Basic endpoint creation and payload capture
- [ ] Signature verification (HMAC-SHA256, SHA1)
- [ ] Custom response codes and delays
- [ ] Webhook forwarding
- [ ] Team collaboration
- [ ] API documentation (OpenAPI)

---

## License

MIT

---

Built by [CyberRaccoonTeam](https://github.com/CyberRaccoonTeam)