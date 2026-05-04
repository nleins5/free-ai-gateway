# Project: Aether Gateway Backend Refactor

## Objective
Modularize the monolithic `simple_ai_gateway.py` into a production-grade FastAPI package, extract core services, and harden security/reliability.

## Strategy
Follow GSD principles to iteratively migrate logic while maintaining system uptime and verification at each step.

## Stack
- Backend: Python 3.12, FastAPI, httpx, OpenAI SDK
- State: Local memory + JSON persistence (future: Redis)
- Routing: Adaptive EWMA weight-based failover
- Frontend: React (Vite) - to be refactored into a modern landing page.

## Core Services
1. **Routing Service**: Multi-provider failover engine.
2. **RAG Service**: Lexical search and document management.
3. **Image Service**: Multi-provider image generation.
4. **State Store**: Centralized provider monitoring and usage tracking.
