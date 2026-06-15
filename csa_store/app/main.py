from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.form98_retrieve import router as form98_router

app = FastAPI(title="CSA Store API")

app.include_router(health_router)

@app.get("/")
def root():
    return {"message": "CSA Store API is running"}


app.include_router(form98_router)
