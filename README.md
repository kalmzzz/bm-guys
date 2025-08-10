# X Superfan Agent Platform

A multi-tenant FastAPI service to run X (Twitter) agents as brand superfans with configurable actions, targeting, style adaptation, and CTA cadence.

## Features
- Brand data input with CTA links and frequencies
- Style adaptation from existing tweets (upload CSV or fetch via X API)
- Targeted users: auto-engage when they post
- Content rewriting from other accounts before posting
- Custom actions per agent: tweets, replies, likes, retweets
- Per-action scheduling (e.g., post every 4h, reply every 2m, etc.)
- Keyword-based auto-replies
- CTA cadence rules (e.g., include site link every 3 tweets)
- Multi-agent under a single deployment
- Railway-ready with Dockerfile and `railway.toml`

## Quickstart

### Local
1. Create a virtualenv and install deps:
   ```bash
   pip install -r requirements.txt
   ```
2. Set environment variables (see `.env.example` in README below):
   - `DATABASE_URL` (defaults to SQLite if not set)
   - `OPENAI_API_KEY` (optional but recommended)
3. Run:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Visit `http://localhost:8000/admin` for a minimal admin UI.

### Railway Deployment
- Fork this repo and click: [Deploy on Railway](https://railway.app/new)
- Add a Postgres plugin to provision `DATABASE_URL`
- Set optional `OPENAI_API_KEY`
- Deploy. The app listens on `${PORT}`.

## Environment Variables
- `DATABASE_URL` (e.g., `postgresql+psycopg2://user:pass@host:port/db`)
- `OPENAI_API_KEY` (for LLM features)
- The X (Twitter) tokens are stored per Agent via the Admin UI and DB. Ensure each agent has valid keys with the necessary permissions.

## Compliance
Use official X APIs and respect rate limits and platform policies. Avoid scraping in violation of Terms. Ensure the account has permissions for write, like, and retweet actions.

## Notes
- This is a reference implementation. Review, harden, and add auth to the admin UI before production use.