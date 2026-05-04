# System Architecture

## Overview
The Aether Protocol Gateway is a high-availability, multi-provider AI proxy. It unifies disparate free-tier AI APIs into a single OpenAI-compatible interface.

## Key Components

### 1. Provider Management
- **Registry**: Static definition of providers and their capabilities.
- **Dynamic Config**: Hot-reloadable settings from `providers.json` for provider chains, task-based routing, and weights.

### 2. Routing Engine
- **Modes**: Round-robin and Weighted.
- **Adaptive Routing**: Uses EWMA (Exponentially Weighted Moving Average) for latency and error-based weight adjustment.
- **Task Tiers**: specialized chains for 'general', 'code', 'vision', 'image', etc.

### 3. Failover & Resilience
- **Sequential Fallback**: Iterates through the provider chain until a successful response or exhaustion.
- **Retry Logic**: Per-provider retries for transient errors.
- **Cooldowns**: Temporarily disables failing providers.

### 4. Specialized Services
- **RAG Store**: In-memory lexical search with persistence.
- **Image Hub**: Multi-provider image generation with local SVG fallback.
- **Usage Tracking**: Token and cost estimation per provider with daily budget enforcement.

## Data Flow
1. Client sends request to `/v1/chat/completions` or `/v1/ai/chat`.
2. Router selects provider chain based on task/alias.
3. Failover engine attempts providers in order.
4. Response is enriched with routing metadata and returned.
