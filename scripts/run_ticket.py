#!/usr/bin/env python3
"""Run ticket service in microservices mode."""
import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Force microservices mode
os.environ["DEPLOYMENT_MODE"] = "microservices"

import uvicorn
from common.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    print(f"🚀 Starting Ticket Service in MICROSERVICES mode")
    print(f"🔗 Connects to Vacancy at: {settings.vacancy_url}")
    print(f"🌐 Server: http://{settings.host}:{settings.ticket_port}")
    print(f"📚 Docs: http://{settings.host}:{settings.ticket_port}/docs")
    print()
    uvicorn.run(
        "ticket.main:app",
        host=settings.host,
        port=settings.ticket_port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        # Configurações para alta concorrência
        workers=1,                    # Workers (1 para dev, 4+ para prod)
        backlog=2048,                 # Fila de conexões pendentes
        limit_concurrency=500,        # Limite de requisições simultâneas
        timeout_keep_alive=5,         # Keep-alive timeout
    )
