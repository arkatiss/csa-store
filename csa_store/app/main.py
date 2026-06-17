from fastapi import FastAPI
from app.core.db_pool import connection_pool
from app.api.health import router as health_router

from app.api.form98.form98_retrieve import router as form98_retrieve_router
from app.api.form98.form98_insert import router as form98_insert_router
from app.api.form98.form98_retrieve_by_key import router as form98_retrieve_by_key_router
from app.api.form98.form98_delete import router as form98_delete_router
from app.api.form98.form98_update import router as form98_update_router

from app.api.form103.form103_paidouts_departments_retrieve import router as form103_paidout_departments_retrieve_router
from app.api.form103.form103_insert import router as form103_insert_router
from app.api.form103.form103_update import router as form103_update_router
from app.api.form103.form103_update import router as form103_update_router
from app.api.form103.form103_delete import router as form103_delete_router

from app.api.form104.form104_select import router as form104_select_router






app = FastAPI(title="CSA Store API")

app.include_router(health_router)

@app.on_event("startup")
def startup():

    conn = connection_pool.getconn()

    try:

        with conn.cursor() as cur:

            cur.execute("SELECT 1")

            print("Database pool initialized successfully")

    finally:

        connection_pool.putconn(conn)

@app.on_event("shutdown")
def shutdown():

    connection_pool.closeall()

    print("Database pool closed")


@app.get("/")
def root():
    return {"message": "CSA Store API is running"}


app.include_router(form98_retrieve_router)
app.include_router(form98_insert_router)
app.include_router(form98_retrieve_by_key_router)
app.include_router(form98_delete_router)
app.include_router(form98_update_router)

app.include_router(form103_paidout_departments_retrieve_router)
app.include_router(form103_insert_router)
app.include_router(form103_update_router)
app.include_router(form103_delete_router)

app.include_router(form104_select_router)