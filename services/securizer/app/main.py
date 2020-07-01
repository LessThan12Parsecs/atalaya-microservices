from fastapi import FastAPI
from app.api.securizer import securizer

app = FastAPI(openapi_url="/api/v1/securizer/openapi.json", docs_url="/api/v1/securizer/docs")

app.include_router(securizer, prefix='/api/v1/securizer', tags=['securizer'])

