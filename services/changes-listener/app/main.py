from fastapi import FastAPI
from app.api.listener import listener

app = FastAPI(openapi_url="/api/v1/listener/openapi.json", docs_url="/api/v1/listener/docs")

app.include_router(listener, prefix='/api/v1/listener', tags=['listener'])

