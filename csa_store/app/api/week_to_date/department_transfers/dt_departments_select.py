import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.department_transfers.dt_departments_select_schema import DTDepartmentsSelectRequest, DTDepartmentsSelectResponse, DepartmentItem

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/week_to_date/departments_transfers",
    tags=["Week To Date Department Transfers"]
)

@router.post("/dt_departments_select", response_model=DTDepartmentsSelectResponse)
def csa_dt_departments_select(request: DTDepartmentsSelectRequest):
    """
    Equivalent of:
    csa_DTDepartments_Select
    """
    try:
        if request.store is None:
            return DTDepartmentsSelectResponse(
                return_value=1,
                error_message="Invalid Store",
                departments=[]
            )

        with DBConnection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT d_id, d_description
                    FROM retail_accounting.departments
                    WHERE d_id IN (1, 2, 3, 5, 7)

                    UNION

                    SELECT d.d_id, d.d_description
                    FROM retail_accounting.departments d
                    INNER JOIN retail_accounting.store_department_account sda
                        ON d.d_id = sda.sda_department
                    WHERE sda.sda_po_mf_account_nbr IS NOT NULL
                      AND sda.sda_po_mf_account_nbr <> ''
                      AND sda.sda_po_mf_account_nbr <> '0'
                      AND sda.sda_store = %s

                    UNION

                    SELECT d_id, d_description
                    FROM retail_accounting.departments
                    WHERE d_department_transfers_flag = 'Y'

                    UNION

                    SELECT d.d_id, d.d_description
                    FROM retail_accounting.departments d
                    INNER JOIN retail_accounting.store_department_account sda
                        ON d.d_supply_main_department_id = sda.sda_department
                    WHERE d.d_supply_department_flag = 'Y'
                      AND sda.sda_po_mf_account_nbr IS NOT NULL
                      AND sda.sda_po_mf_account_nbr <> ''
                      AND sda.sda_po_mf_account_nbr <> '0'
                      AND sda.sda_store = %s

                    ORDER BY d_description
                """
                
                cur.execute(query, (request.store, request.store))
                rows = cur.fetchall()
                
                departments = []
                for row in rows:
                    departments.append(DepartmentItem(
                        d_id=row[0],
                        d_description=row[1]
                    ))
                
                return DTDepartmentsSelectResponse(
                    return_value=0,
                    error_message="",
                    departments=departments
                )

    except Exception as ex:
        logger.exception("Error in DTDepartments_Select")
        return DTDepartmentsSelectResponse(
            return_value=1,
            error_message="Select DT Departments Failed",
            departments=[]
        )
