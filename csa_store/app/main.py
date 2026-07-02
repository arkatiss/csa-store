from fastapi import FastAPI
from app.core.db_pool import connection_pool
from app.api.health import router as health_router

from app.api.stores_list import router as stores_list_router


from app.api.daily.form98.form98_retrieve import router as form98_retrieve_router
from app.api.daily.form98.form98_insert import router as form98_insert_router
from app.api.daily.form98.form98_retrieve_by_key import router as form98_retrieve_by_key_router
from app.api.daily.form98.form98_delete import router as form98_delete_router
from app.api.daily.form98.form98_update import router as form98_update_router

from app.api.daily.form103.form103_select import router as form103_select_router
from app.api.daily.form103.form103_paidouts_departments_retrieve import router as form103_paidout_departments_retrieve_router
from app.api.daily.form103.form103_retrieve_by_id import router as form103_retrieve_by_id_router
from app.api.daily.form103.form103_insert import router as form103_insert_router
from app.api.daily.form103.form103_update import router as form103_update_router
from app.api.daily.form103.form103_delete import router as form103_delete_router

from app.api.daily.form104.form104_select import router as form104_select_router
from app.api.daily.form104.form104_retrieve_by_id import router as form104_retrieve_router
from app.api.daily.form104.form104_account_descriptions_select import router as form104_account_descriptions_router
from app.api.daily.form104.form104_insert import router as form104_insert_router
from app.api.daily.form104.form104_update import router as form104_update_router
from app.api.daily.form104.form104_delete import router as form104_delete_router

from app.api.daily.form105a.form105a_select import router as form105a_select_router
from app.api.daily.form105a.form105a_retrieve_by_id import router as form105a_retrieve_by_id_router
from app.api.daily.form105a.form105a_ar_payment_types_select import router as form105a_ar_payment_types_router
from app.api.daily.form105a.form105a_insert import router as form105a_insert_router
from app.api.daily.form105a.form105a_update import router as form105a_update_router
from app.api.daily.form105a.form105a_delete import router as form105a_delete_router

from app.api.daily.form105b.form105b_select import router as form105b_select_router
from app.api.daily.form105b.form105b_retrieve_by_id import router as form105b_retrieve_router
from app.api.daily.form105b.form105b_insert import router as form105b_insert_router
from app.api.daily.form105b.form105b_update import router as form105b_update_router
from app.api.daily.form105b.form105b_delete import router as form105b_delete_router

from app.api.daily.form122.form122_select import router as form122_select_router
from app.api.daily.form122.form122_retrieve_by_id import router as form122_retrieve_by_id_router
from app.api.daily.form122.form122_update import router as form122_update_router

from app.api.daily.form112.form112_select import router as form112_select_router
from app.api.daily.form112.form112_retrievebyid import router as form112_retrievebyid_router
from app.api.daily.form112.form112_update import router as form112_update_router

from app.api.daily.form97.form97_select import router as form97_select_router
from app.api.daily.form97.form97_update import router as form97_update_router

from app.api.daily.form111.form111_select import router as form111_select_router
from app.api.daily.form111.form111_retrieve_by_id import router as form111_retrieve_by_id_router
from app.api.daily.form111.form111_account_descriptions_select import router as form111_account_descriptions_router
from app.api.daily.form111.form111_insert import router as form111_insert_router
from app.api.daily.form111.form111_update import router as form111_update_router
from app.api.daily.form111.form111_delete import router as form111_delete_router

from app.api.daily.form102.form102_select import router as form102_select_router
from app.api.daily.form102.form102_retrieve_by_id import router as form102_retrieve_by_id_router
from app.api.daily.form102.form102_deposit_types_select import router as form102_deposit_types_select_router
from app.api.daily.form102.form102_insert import router as form102_insert_router
from app.api.daily.form102.form102_update import router as form102_update_router
from app.api.daily.form102.form102_delete import router as form102_delete_router

from app.api.daily.daily_department_input_ind_only.dept_input_select import router as dept_input_select_router
from app.api.daily.daily_department_input_ind_only.dept_sales_manual_update import router as dept_sales_manual_update_router
from app.api.daily.daily_department_input_ind_only.dept_voids_refunds_manual_update import router as dept_voids_refunds_manual_update_router
from app.api.daily.daily_department_input_ind_only.dept_customer_count_manual_update import router as dept_customer_count_manual_update_router

from app.api.daily.form106.form106_select import router as form106_select_router
from app.api.daily.form106.form106_retrieve_by_id import router as form106_retrieve_by_id_router
from app.api.daily.form106.form106_departments_select import router as departments_select_router
from app.api.daily.form106.form106_insert import router as form106_insert_router
from app.api.daily.form106.form106_update import router as form106_update_router
from app.api.daily.form106.form106_delete import router as form106_delete_router

from app.api.daily.daily_taxes_input_ind_only.daily_taxes_manual_select import router as daily_taxes_manual_select_router
from app.api.daily.daily_taxes_input_ind_only.daily_taxes_manual_update import router as daily_taxes_manual_update_router





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

app.include_router(stores_list_router)

app.include_router(form98_retrieve_router)
app.include_router(form98_insert_router)
app.include_router(form98_retrieve_by_key_router)
app.include_router(form98_delete_router)
app.include_router(form98_update_router)

app.include_router(form103_select_router)
app.include_router(form103_paidout_departments_retrieve_router)
app.include_router(form103_retrieve_by_id_router)
app.include_router(form103_insert_router)
app.include_router(form103_update_router)
app.include_router(form103_delete_router)

app.include_router(form104_select_router)
app.include_router(form104_retrieve_router)
app.include_router(form104_account_descriptions_router)
app.include_router(form104_insert_router)
app.include_router(form104_update_router)
app.include_router(form104_delete_router)

app.include_router(form105a_select_router)
app.include_router(form105a_retrieve_by_id_router)
app.include_router(form105a_ar_payment_types_router)
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

app.include_router(form112_select_router)
app.include_router(form112_retrievebyid_router)
app.include_router(form112_update_router)

app.include_router(form97_select_router)
app.include_router(form97_update_router)

app.include_router(form111_select_router)
app.include_router(form111_retrieve_by_id_router)
app.include_router(form111_account_descriptions_router)
app.include_router(form111_insert_router)
app.include_router(form111_update_router)
app.include_router(form111_delete_router)

app.include_router(form102_select_router)
app.include_router(form102_retrieve_by_id_router)
app.include_router(form102_deposit_types_select_router)
app.include_router(form102_insert_router)
app.include_router(form102_update_router)
app.include_router(form102_delete_router)

app.include_router(dept_input_select_router)
app.include_router(dept_sales_manual_update_router)
app.include_router(dept_voids_refunds_manual_update_router)
app.include_router(dept_customer_count_manual_update_router)

app.include_router(form106_insert_router)
app.include_router(form106_select_router)
app.include_router(form106_delete_router)
app.include_router(form106_update_router)
app.include_router(form106_retrieve_by_id_router)
app.include_router(departments_select_router)

app.include_router(daily_taxes_manual_select_router)
app.include_router(daily_taxes_manual_update_router)
