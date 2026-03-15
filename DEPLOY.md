# Deployment Guide

## Railway Deployment

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Select: `CyberRaccoonTeam/[api-name]`
4. Add environment variables:
   - `SECRET_KEY`: Generate with Python `import secrets; print(secrets.token_hex(32))`
   - `DATABASE_URL`: `sqlite:///app.db`
5. Deploy!

## Test Endpoints

- Health: `GET /api/health`
- Create Key: `POST /api/keys`
- Main Endpoint: `POST /api/...`

## Pricing

- Free: 100 requests/day
- Pro ($9/mo): 5,000 requests/day
- Business ($29/mo): Unlimited
