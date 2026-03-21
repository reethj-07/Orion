# Orion — free / zero-cost stack

Orion is designed so you can run **without paid cloud APIs**. Use **local open-source services** (Docker + Ollama) and **free search** (DuckDuckGo).

## What costs money vs what does not

| Capability | Free option (recommended) | Paid / API alternative |
|------------|---------------------------|-------------------------|
| **Database, cache, vectors** | PostgreSQL, MongoDB, Redis, Qdrant via Docker Compose (local) | Managed cloud DBs |
| **Chat LLM** | **[Ollama](https://ollama.com)** — run `llama3.2`, `mistral`, etc. locally | OpenAI, Anthropic |
| **Embeddings** | **Ollama** — e.g. `nomic-embed-text` | OpenAI `text-embedding-3-small` |
| **Web search** | **DuckDuckGo** (built-in, no key) | Tavily (has a limited free tier; optional) |
| **CI** | **GitHub Actions** free tier for public repos | Larger runners / private minutes |
| **Frontend / API hosting** | Local dev; deploy to free tiers (e.g. **Render**, **Fly.io**, **Vercel** hobby) as you prefer | Paid PaaS |

## Quick setup (100% local inference)

1. Install **[Ollama](https://ollama.com)** and pull models:

   ```bash
   ollama pull llama3.2
   ollama pull nomic-embed-text
   ```

2. Copy env and use **free defaults** (see `.env.example`):

   ```env
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   OLLAMA_MODEL=llama3.2
   EMBEDDING_PROVIDER=ollama
   OLLAMA_EMBED_MODEL=nomic-embed-text
   WEB_SEARCH_PROVIDER=duckduckgo
   ```

   **Docker note:** from *inside* containers, `localhost` is not your host. On Docker Desktop use `http://host.docker.internal:11434` for `OLLAMA_BASE_URL`. On Linux you may need `http://172.17.0.1:11434` or run Ollama in Compose.

3. Start the stack: `make dev`

**Important:** Do not mix embedding providers for the same Qdrant collections. If you ingested documents with OpenAI (e.g. 1536-dim) and later switch to Ollama (e.g. 768-dim for `nomic-embed-text`), reset Qdrant volumes or use a fresh org/collection strategy.

## Optional: OpenAI / Anthropic free credits

If you have **free trial or promotional credits** (not a “premium subscription”), you can set:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
```

Use **small / mini** models to stretch free credits. Orion does **not** require Tavily, SerpAPI, or Cohere.

## Optional: Tavily

`WEB_SEARCH_PROVIDER=tavily` uses [Tavily](https://tavily.com) when `TAVILY_API_KEY` is set. The project defaults to **DuckDuckGo** so web research works with **no API key**.
