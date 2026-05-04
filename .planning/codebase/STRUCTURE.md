# Project Structure

```text
/
├── .env                # API keys and environment config
├── providers.json      # Dynamic provider settings
├── requirements.txt    # Python dependencies
├── simple_ai_gateway.py # MONOLITHIC BACKEND (Primary Logic)
├── .rag_store.json     # RAG database (JSON)
├── ui/                 # Frontend source
│   ├── src/            # React components
│   └── dist/           # Built frontend assets (served by backend)
└── .planning/          # GSD Planning & Codebase Map
```

## Critical Files
- **simple_ai_gateway.py**: Contains all logic for routing, failover, RAG, and API endpoints.
- **providers.json**: Allows updating the behavior of the gateway without restarting the server.
