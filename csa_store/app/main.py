from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.form98_retrieve import router as form98_retrieve_router
from app.api.form98_insert import router as form98_insert_router
from app.api.form98_retrieve_by_key import router as form98_retrieve_by_key_router

app = FastAPI(title="CSA Store API")

app.include_router(health_router)

@app.get("/")
def root():
    return {"message": "CSA Store API is running"}


app.include_router(form98_retrieve_router)
app.include_router(form98_insert_router)
app.include_router(form98_retrieve_by_key_router)

