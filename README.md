# FinVise AI — Indian Stock Market Intelligence Platform

> **AI-powered stock intelligence with auto-generated 90-second video briefs for Indian (NSE/BSE) stocks.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-blue)](https://YOUR_FRONTEND_URL.vercel.app)
[![Backend API](https://img.shields.io/badge/Backend%20API-Render-green)](https://YOUR_BACKEND_URL.onrender.com/docs)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🚀 Live URLs

| Service | URL |
|---|---|
| **Frontend (React)** | `https://YOUR_FRONTEND_URL.vercel.app` |
| **Backend API (FastAPI)** | `https://YOUR_BACKEND_URL.onrender.com` |
| **API Docs (Swagger)** | `https://YOUR_BACKEND_URL.onrender.com/docs` |
| **Sample Video** | [Watch Demo](https://YOUR_DEMO_VIDEO_LINK) |

---

## 📋 What I Built

FinVise AI is a full-stack, production-grade stock market intelligence platform with four core layers:

1. **Real-Time Data Pipeline** — Fetches live stock prices (OHLCV, 52W range, market cap, P/E) from NSE/BSE via `yfinance`. Falls back to BSE if NSE data is unavailable.

2. **Multi-Source News Aggregation** — Scrapes financial RSS feeds (Moneycontrol, Economic Times, Business Standard, Livemint, Zee Business) in parallel. Optionally enriched with NewsAPI / GNews if keys are provided.

3. **AI Brief Generation** — Sends structured stock + news data to an LLM (Groq → Gemini → Anthropic → rule-based fallback) with a carefully engineered prompt that produces a structured, beginner-friendly 90-second video script in 5 timed sections.

4. **Programmatic Video Generation** — Converts the AI script to speech using `gTTS`, assembles timed slides with `MoviePy`, and exports a downloadable 720p MP4 — fully auto-generated, no manual steps.

---

## 🎬 Video Brief Format

| Section | Timestamp | Content |
|---|---|---|
| 🎣 Hook | 0–10s | Attention-grabbing opening tied to today's price/news |
| 📊 Stock Snapshot | 10–30s | Price, % change, 52-week context in plain English |
| 📰 What's Happening | 30–60s | 2–3 key news events explained simply |
| 💡 Beginner Takeaway | 60–80s | What it means for a first-time investor |
| 📣 Call to Action | 80–90s | Neutral educational closing line |

---

## 🛠 Tech Stack

### Backend (Python)
| Layer | Choice | Why |
|---|---|---|
| Framework | **FastAPI** | Async, fast, auto-generates Swagger docs |
| Stock Data | **yfinance** | Free, reliable, supports NSE `.NS` suffix |
| News | **feedparser** + RSS feeds | Fully free, no API key needed for base functionality |
| LLM (primary) | **Groq (llama-3.3-70b)** | Fastest free-tier inference, JSON mode support |
| LLM (fallback) | **Gemini 1.5 Flash** | High quality, generous free tier |
| LLM (tertiary) | **Anthropic Claude Haiku** | Reliable fallback |
| TTS | **gTTS** | Completely free, no API key, good quality |
| Video Assembly | **MoviePy** | Python-native, no paid services needed |
| Deployment | **Render** | Free tier web service, supports Python |

### Frontend (React)
| Layer | Choice | Why |
|---|---|---|
| Framework | **React 18** | Familiar, component-based, great ecosystem |
| Charts | **Recharts** | Lightweight, composable, works with financial data |
| HTTP | **fetch (native)** | No extra dependencies needed |
| Fonts | **Sora + Space Mono** | Modern display + monospace for financial data |
| Deployment | **Vercel** | Instant deploys, CDN, free tier |

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- At least one LLM API key (Groq recommended — fastest + free)

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/finvise-ai.git
cd finvise-ai
```

### 2. Backend setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and fill environment variables
cp .env.example .env
# Edit .env and add your API keys

# Run the backend
uvicorn main:app --reload --port 8000
```

### 3. Frontend setup
```bash
cd frontend

# Install dependencies
npm install

# Copy and configure environment
cp .env.example .env.local
# Edit .env.local: set REACT_APP_API_URL=http://localhost:8000

# Start the dev server
npm start
```

Visit `http://localhost:3000` in your browser.

---

## 🌍 Deployment Guide

### Backend → Render (Free Tier)
1. Push your code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo → select `backend/` as root directory
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables from `.env.example`
7. Deploy — you'll get a URL like `https://finvise-ai-backend.onrender.com`

### Frontend → Vercel (Free Tier)
1. Go to [vercel.com](https://vercel.com) → New Project
2. Import your GitHub repo → select `frontend/` as root directory
3. Set environment variable: `REACT_APP_API_URL=https://YOUR_RENDER_URL.onrender.com`
4. Deploy — you'll get a URL like `https://finvise-ai.vercel.app`

---

## 🔑 API Keys Needed

| Key | Where to Get | Required? |
|---|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | ✅ Recommended |
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) | Optional (fallback) |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | Optional (tertiary) |
| `NEWSAPI_KEY` | [newsapi.org](https://newsapi.org) | Optional (RSS works without it) |
| `GNEWS_KEY` | [gnews.io](https://gnews.io) | Optional |

**You can run the app with ONLY a Groq API key.** RSS news feeds work without any key.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/stock/{symbol}` | Full stock data (OHLCV, chart, metadata) |
| `GET` | `/api/stock/{symbol}/summary` | Compact summary for LLM input |
| `GET` | `/api/news/{symbol}` | Multi-source news articles |
| `POST` | `/api/brief/generate` | Generate AI video script |
| `POST` | `/api/video/generate` | Start async video generation |
| `GET` | `/api/video/status/{job_id}` | Poll video generation status |
| `GET` | `/api/video/download/{job_id}` | Download generated MP4 |

---

## 🧠 LLM Prompt Engineering

The brief generation prompt is carefully structured to:
- **Contextualise** the stock data (52-week position as %, not just numbers)
- **Mandate** 5 timed sections with specific word/sentence counts
- **Enforce** beginner-friendly language (no jargon instruction)
- **Use JSON mode** (Groq/Gemini) to guarantee parseable structured output
- **Include fallback** rule-based generation if all LLMs fail

The system prompt frames the model as "FinVise AI — a friendly financial educator", producing warmer, more accessible output than generic financial analyst prompts.

---

## 🔮 What I'd Improve With More Time

1. **WebSocket-based live price streaming** instead of polling — prices update in real-time without page refresh
2. **Remotion-based video generation** for React — richer visual slides with animations and branded graphics
3. **Portfolio tracking** — save multiple stocks, track overall portfolio sentiment over time
4. **Hindi/regional language support** — `gTTS` supports Hindi; adding language toggle would reach a far wider Indian audience
5. **Smarter news filtering** — NLP-based relevance scoring (currently keyword-based) to remove false positives
6. **Caching layer** — Redis cache for stock data (5-min TTL) to avoid yfinance rate limits under load
7. **Historical brief archive** — store generated briefs per stock per day for trend analysis

---

## ⚠️ Disclaimer

This platform is for **educational purposes only**. Nothing on FinVise AI constitutes financial advice. Always consult a SEBI-registered investment advisor before making investment decisions.

---

*Built with ❤️ for the FinVise AI Technical Assignment*
