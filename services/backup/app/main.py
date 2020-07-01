# from fastapi import FastAPI
# from app.api.explorer import explorer

# app = FastAPI(openapi_url="/api/v1/explorer/openapi.json", docs_url="/api/v1/casts/docs")

# app.include_router(explorer, prefix='/api/v1/explorer', tags=['explorer'])

from fastapi import FastAPI

app = FastAPI()


@app.get('/')
async def index():
    return {"Real": "Python"}
