from fastapi import FastAPI
from app import models
from app.database import engine
from app.routers import agents

# Cria/atualiza as tabelas no banco de dados com base nos modelos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Agent for Gmail",
    description="Uma API para gerenciar agentes de IA que interagem com o Gmail."
)

app.include_router(agents.router)

@app.get("/", tags=["Root"])
def read_root():
    return {"status": "API está funcionando!"}