# Astraventa WhatsApp Gemini AI Engine & Next.js 15 Admin Portal

Production-grade WhatsApp AI Automation Engine built with FastAPI, Meta Cloud API v25.0, Supabase PostgreSQL, pgvector RAG Search, and a high-density Next.js 15 Admin Portal.

---

## 🌟 Key Features

### 1. FastAPI Meta WhatsApp Cloud API Engine (`/app`)
- **Meta Cloud API v25.0**: Handles incoming webhooks (`/webhook`) and async message processing.
- **Interactive Messages**: Outbound support for Meta quick reply buttons and list menus.
- **Gemini 2.5 & OpenRouter AI Engine**: RAG vector search integration with multi-model fallback.
- **Supabase Memory & Logs**: Stateful conversation history per WhatsApp phone number (`wa_id`).

### 2. Next.js 15 App Router Admin Portal (`/dashboard`)
- **Ultra-Dark Charcoal Developer UI**: Inspired by OpenRouter.ai and Vercel.
- **Realtime Chat Stream (`/admin/chats`)**: Supabase Realtime WebSocket listener for live user-bot conversations.
- **Engine Telemetry (`/admin/overview`)**: KPI metrics and Recharts 24-hour message volume graphs.
- **Vector Knowledge Base Editor (`/admin/knowledge-base`)**: RAG document editor with vector embedding generation.

---

## 🚀 Quick Start (Local Development)

### 1. Backend FastAPI Server
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Next.js Admin Portal
```bash
cd dashboard
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000).

---

## 🛠️ Tech Stack
- **FastAPI / Python 3.10+**
- **Next.js 15 / TypeScript / Tailwind CSS / Framer Motion**
- **Supabase PostgreSQL & pgvector**
- **Meta WhatsApp Cloud API v25.0**
- **Google Gemini 2.5 Flash / OpenRouter API**
