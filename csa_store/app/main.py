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
from app.api.form104.form104_retrieve_by_id import router as form104_retrieve_router
from app.api.form104.form104_insert import router as form104_insert_router
from app.api.form104.form104_update import router as form104_update_router
from app.api.form104.form104_delete import router as form104_delete_router

from app.api.form105a.form105a_select import router as form105a_select_router
from app.api.form105a.form105a_retrieve_by_id import router as form105a_retrieve_by_id_router
from app.api.form105a.ar_payment_types_select import router as ar_payment_types_router
from app.api.form105a.form105a_insert import router as form105a_insert_router
from app.api.form105a.form105a_update import router as form105a_update_router
from app.api.form105a.form105a_delete import router as form105a_delete_router

from app.api.form105b.form105b_select import router as form105b_select_router
from app.api.form105b.form105b_retrieve_by_id import router as form105b_retrieve_router
from app.api.form105b.form105b_insert import router as form105b_insert_router
from app.api.form105b.form105b_update import router as form105b_update_router
from app.api.form105b.form105b_delete import router as form105b_delete_router

from app.api.form122.form122_select import router as form122_select_router
from app.api.form122.form122_retrieve_by_id import router as form122_retrieve_by_id_router
from app.api.form122.form122_update import router as form122_update_router







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
app.include_router(form104_retrieve_router)
app.include_router(form104_insert_router)
app.include_router(form104_update_router)
app.include_router(form104_delete_router)

app.include_router(form105a_select_router)
app.include_router(form105a_retrieve_by_id_router)
app.include_router(ar_payment_types_router)
app.include_router(form105a_insert_router)
app.include_router(form105a_update_router)
app.include_router(form105a_delete_router)

app.include_router(form105b_select_router)
app.include_router(form105b_retrieve_router)
app.include_router(form105b_insert_router)
app.include_router(form105b_update_router)
app.include_router(form105b_delete_router)

app.include_router(form122_select_router)
app.include_router(form122_retrieve_by_id_router)
app.include_router(form122_update_router)