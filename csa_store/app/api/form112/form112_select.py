import logging

from fastapi import APIRouter

from app.core.db_utils import DBConnection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form112",
    tags=["Form112"]
)


@router.get("/{dms_store}")
def form112_select(
        dms_store: int):
    """
    Equivalent of:

    csa_Form112_Select
    """

    try:

        #
        # VALIDATIONS
        #

        if dms_store is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Store"
            }

        with DBConnection() as conn:

            with conn.cursor() as cur:

                logger.info(
                    f"Fetching Form112 records "
                    f"for Store={dms_store}"
                )

                #
                # CHECK RECORD EXISTS
                #

                cur.execute("""
                    SELECT COUNT(*)
                    FROM retail_history.drink_machine_sales
                    WHERE dms_store=%s
                """,
                (
                    dms_store,
                ))

                count = cur.fetchone()[0]

                if count == 0:

                    return {
                        "return_value": 3,
                        "error_message": "No Rows Found"
                    }

                #
                # FETCH DATA
                #

                cur.execute("""
                    SELECT
                        dms.dms_date,
                        dms.dms_machine_nbr,
                        dm.dm_type,
                        dmt.dmt_description,
                        dm.dm_price_per_sale,
                        dm.dm_count_type,
                        dmct.dmct_description,
                        dms.dms_beginning_reading,
                        dms.dms_ending_reading,
                        dms.dms_nbr_of_sales,
                        dms.dms_actual_sales,
                        (
                            dm.dm_price_per_sale
                            * dms.dms_nbr_of_sales
                        ) AS calc_sales,
                        (
                            dms.dms_actual_sales
                            -
                            (
                                dm.dm_price_per_sale
                                * dms.dms_nbr_of_sales
                            )
                        ) AS over_short,
                        dms.dms_process_flag
                    FROM retail_history.drink_machine_sales dms
                    INNER JOIN retail_accounting.drink_machines dm
                        ON dms.dms_store = dm.dm_store
                        AND dms.dms_machine_nbr = dm.dm_machine_nbr
                    INNER JOIN retail_accounting.drink_machine_types dmt
                        ON dm.dm_type = dmt.dmt_id
                    INNER JOIN retail_accounting.drink_machine_count_types dmct
                        ON dm.dm_count_type = dmct.dmct_type
                    WHERE dms.dms_store=%s
                    ORDER BY dms.dms_date
                """,
                (
                    dms_store,
                ))

                rows = cur.fetchall()

                data = []

                for row in rows:

                    data.append({
                        "dms_date": row[0],
                        "dms_machine_nbr": row[1],
                        "dm_type": row[2],
                        "dmt_description": row[3],
                        "dm_price_per_sale": float(row[4])
                        if row[4] is not None
                        else 0,
                        "dm_count_type": row[5],
                        "dmct_description": row[6],
                        "dms_beginning_reading": row[7],
                        "dms_ending_reading": row[8],
                        "dms_nbr_of_sales": row[9],
                        "dms_actual_sales": float(row[10])
                        if row[10] is not None
                        else 0,
                        "calc_sales": float(row[11])
                        if row[11] is not None
                        else 0,
                        "over_short": float(row[12])
                        if row[12] is not None
                        else 0,
                        "dms_process_flag": row[13]
                    })

                return {
                    "return_value": 0,
                    "data": data
                }

    except Exception as ex:

        logger.exception(
            "Error in Form112 Select"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }