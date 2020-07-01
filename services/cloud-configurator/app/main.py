from fastapi import FastAPI
from app.api.cloud_configurator import cloud_configurator

app = FastAPI(openapi_url="/api/v1/cloud_configurator/openapi.json", docs_url="/api/v1/cloud_configurator/docs")

app.include_router(cloud_configurator, prefix='/api/v1/cloud_configurator', tags=['cloud_configurator'])

