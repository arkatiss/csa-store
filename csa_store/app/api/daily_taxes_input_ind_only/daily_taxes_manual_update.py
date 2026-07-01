import logging
from datetime import timedelta

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.daily_taxes_input_ind_only.daily_taxes_manual_update_schema import (
    DailyTaxesManualUpdateRequest
)

logger = logging.getLogger(__name__)


def get_week_ending_date(sc_eow_last_run):
    """
    Equivalent of SQL:

    IF DATEPART(WEEKDAY,@SC_EOW_Last_Run)=1
        WeekEnding=@SC_EOW_Last_Run
    ELSE
        WeekEnding=@SC_EOW_Last_Run+(8-weekday)
    """

    if sc_eow_last_run.weekday() == 6:
        return sc_eow_last_run

    return sc_eow_last_run + timedelta(days=(6 - sc_eow_last_run.weekday()))


def get_existing_tax_values(
        cur,
        tenant_id,
        store,
        file_date):
    """
    Returns existing manual tax values
    keyed by tax rate.

    Equivalent of:

    Select @Old_DTM...
    """

    cur.execute("""
        SELECT
            dtm_tax_rate,
            dtm_net_sales,
            dtm_sales_tax_collected
        FROM retail_history.daily_taxes_manual
        WHERE tenant_id=%s
        AND dtm_store=%s
        AND dtm_file_date=%s
        ORDER BY dtm_tax_rate
    """,
    (
        str(tenant_id),
        store,
        file_date
    ))

    rows = cur.fetchall()

    old_values = {}

    for row in rows:

        old_values[row[0]] = {
            "net_sales": row[1],
            "sales_tax": row[2]
        }

    return old_values


def update_daily_taxes_manual(
        cur,
        tenant_id,
        store,
        file_date,
        tax_rate,
        net_sales,
        sales_tax):
    """
    Update retail_history.daily_taxes_manual
    """

    cur.execute("""
        UPDATE retail_history.daily_taxes_manual
        SET
            dtm_net_sales=%s,
            dtm_sales_tax_collected=%s
        WHERE tenant_id=%s
        AND dtm_store=%s
        AND dtm_file_date=%s
        AND dtm_tax_rate=%s
    """,
    (
        net_sales,
        sales_tax,
        str(tenant_id),
        store,
        file_date,
        tax_rate
    ))



def update_wtd_taxes_manual(
        cur,
        tenant_id,
        store,
        week_ending_date):
    """
    Equivalent of:

    Update WTD_Taxes_Manual
    """

    cur.execute("""
        UPDATE retail_accounting_original.wtd_taxes_manual wtm
        SET
            wtm_net_sales=q.net_sales,
            wtm_sales_tax_collected=q.sales_tax
        FROM
        (
            SELECT
                dtm_store,
                dtm_tax_rate,
                SUM(dtm_net_sales) net_sales,
                SUM(dtm_sales_tax_collected) sales_tax
            FROM retail_history.daily_taxes_manual
            WHERE tenant_id=%s
            GROUP BY
                dtm_store,
                dtm_tax_rate
            HAVING dtm_store=%s
        ) q
        WHERE
            wtm.tenant_id=%s
        AND wtm.wtm_store=q.dtm_store
        AND wtm.wtm_tax_rate=q.dtm_tax_rate
        AND wtm.wtm_store=%s
        AND wtm.wtm_week_ending_date=%s
    """,
    (
        str(tenant_id),
        store,
        str(tenant_id),
        store,
        week_ending_date
    ))



def update_daily_taxes(
        cur,
        tenant_id,
        store,
        file_date,
        tax_rate,
        net_sales,
        sales_tax):
    """
    Equivalent of SQL:

    Update DailyTaxes
    """

    cur.execute(f"""
        UPDATE retail_history.daily_taxes dt
        SET
            dt_net_sales =
                (%s + pos.pos_daily_net_sales_rate_{tax_rate}),
            dt_sales_tax_collected =
                (%s + pos.pos_daily_sales_tax_collected_rate_{tax_rate}),
            dt_sales_tax_liability =
                (
                    (%s + pos.pos_daily_net_sales_rate_{tax_rate})
                    *
                    sc.sc_tax_rate_{tax_rate}
                )
        FROM retail_history.pos pos
        INNER JOIN retail_accounting.store_configuration sc
            ON pos.pos_store = sc.sc_store
        WHERE dt.dt_store = pos.pos_store
        AND dt.dt_file_date = pos.pos_file_date
        AND dt.dt_store = %s
        AND dt.dt_file_date = %s
        AND dt.dt_tax_rate = %s
    """,
    (
        net_sales,
        sales_tax,
        net_sales,
        store,
        file_date,
        str(tax_rate)
    ))



def update_wtd_taxes(
        cur,
        tenant_id,
        store,
        week_ending_date):
    """
    Equivalent of SQL:

    Update WTD Taxes
    """

    cur.execute("""
        UPDATE retail_accounting_original.wtd_taxes wt
        SET
            wt_net_sales=q.net_sales,
            wt_sales_tax_collected=q.sales_tax,
            wt_sales_tax_liability=q.sales_tax_liability
        FROM
        (
            SELECT
                dt_store,
                dt_tax_rate,
                SUM(dt_net_sales) net_sales,
                SUM(dt_sales_tax_collected) sales_tax,
                SUM(dt_sales_tax_liability) sales_tax_liability
            FROM retail_history.daily_taxes
            WHERE tenant_id=%s
            GROUP BY
                dt_store,
                dt_tax_rate
            HAVING dt_store=%s
        ) q
        WHERE
            wt.tenant_id=%s
        AND wt.wt_store=q.dt_store
        AND wt.wt_tax_rate=q.dt_tax_rate
        AND wt.wt_store=%s
        AND wt.wt_week_ending_date=%s
    """,
    (
        str(tenant_id),
        store,
        str(tenant_id),
        store,
        week_ending_date
    ))



def insert_daily_taxes_audit(
        cur,
        tenant_id,
        store,
        file_date,
        user,
        comment):
    """
    Insert audit record.
    """

    cur.execute("""
        INSERT INTO retail_history.audit
        (
            tenant_id,
            a_store,
            a_date,
            a_form_type,
            a_action,
            a_creation_date,
            a_user,
            a_comment
        )
        VALUES
        (
            %s,
            %s,
            %s,
            19,
            'U',
            CURRENT_TIMESTAMP,
            %s,
            %s
        )
    """,
    (
        str(tenant_id),
        store,
        file_date,
        user,
        comment
    ))


router = APIRouter(
    prefix="/daily_taxes_input_ind_only",
    tags=["Daily Taxes Input Ind Only"]
)


@router.put("/manual_update")
def csa_daily_taxes_manual_update(
        request: DailyTaxesManualUpdateRequest):
    """
    Equivalent of

    csa_DailyTaxes_Manual_Update

    Exact SQL Server procedure conversion.
    """

    try:

        #
        # VALIDATE STORE
        #

        if (
            request.dtm_store is None
            or
            request.dtm_store == ""
        ):
            return {
                "return_value": 1,
                "error_message": "Invalid Store"
            }

        #
        # VALIDATE FILE DATE
        #

        if (
            request.dtm_file_date is None
            or
            request.dtm_file_date == ""
        ):
            return {
                "return_value": 1,
                "error_message": "Invalid Date"
            }

        #
        # VALIDATE USER
        #

        if (
            request.user is None
            or
            request.user.strip() == ""
        ):
            return {
                "return_value": 1,
                "error_message": "Invalid User"
            }

        #
        # VALIDATE NET SALES
        #

        if request.dtm_net_sales1 is None:
            return {
                "return_value": 1,
                "error_message":
                    "Invalid Net Sales for tax Rate 1"
            }

        if request.dtm_net_sales2 is None:
            return {
                "return_value": 1,
                "error_message":
                    "Invalid Net Sales for tax Rate 2"
            }

        if request.dtm_net_sales3 is None:
            return {
                "return_value": 1,
                "error_message":
                    "Invalid Net Sales for tax Rate 3"
            }

        if request.dtm_net_sales4 is None:
            return {
                "return_value": 1,
                "error_message":
                    "Invalid Net Sales for tax Rate 4"
            }

        #
        # VALIDATE SALES TAX
        #

        if request.dtm_sales_tax_collected1 is None:
            return {
                "return_value": 1,
                "error_message":
                    "Invalid Sales Tax Collected for tax Rate 1"
            }

        if request.dtm_sales_tax_collected2 is None:
            return {
                "return_value": 1,
                "error_message":
                    "Invalid Sales Tax Collected for tax Rate 2"
            }

        if request.dtm_sales_tax_collected3 is None:
            return {
                "return_value": 1,
                "error_message":
                    "Invalid Sales Tax Collected for tax Rate 3"
            }

        if request.dtm_sales_tax_collected4 is None:
            return {
                "return_value": 1,
                "error_message":
                    "Invalid Sales Tax Collected for tax Rate 4"
            }

        with DBConnection() as conn:

            with conn.cursor() as cur:

                logger.info(
                    "Updating Daily Taxes Manual "
                    "Store=%s Date=%s",
                    request.dtm_store,
                    request.dtm_file_date
                )

                #
                # GET STORE CONFIGURATION
                #

                cur.execute("""
                    SELECT
                        sc_eow_last_run
                    FROM retail_accounting.store_configuration
                    WHERE sc_store=%s
                """,
                (request.dtm_store,))

                row = cur.fetchone()

                if row is None:

                    return {
                        "return_value": 1,
                        "error_message":
                            "Invalid Store"
                    }

                sc_eow_last_run = row[0]

                #
                # WEEK ENDING DATE
                #

                week_ending_date = get_week_ending_date(sc_eow_last_run.date())

                #
                # CHECK ROW EXISTS
                #

                cur.execute("""
                    SELECT COUNT(*)
                    FROM retail_history.daily_taxes_manual
                    WHERE dtm_store=%s
                    AND dtm_file_date=%s
                """,
                (request.dtm_store, request.dtm_file_date))

                count = cur.fetchone()[0]

                if count == 0:

                    return {
                        "return_value": 1,
                        "error_message":
                            "Row Not Found"
                    }

                #
                # FETCH OLD VALUES
                #

                old_values = get_existing_tax_values(
                    cur,
                    request.tenant_id,
                    request.dtm_store,
                    request.dtm_file_date
                )

                #
                # BEGIN TRANSACTION
                #
                logger.info("Transaction Started.")

                #
                # UPDATE DAILY TAXES MANUAL
                #

                update_daily_taxes_manual(
                    cur,
                    request.tenant_id,
                    request.dtm_store,
                    request.dtm_file_date,
                    "1",
                    request.dtm_net_sales1,
                    request.dtm_sales_tax_collected1
                )

                update_daily_taxes_manual(
                    cur,
                    request.tenant_id,
                    request.dtm_store,
                    request.dtm_file_date,
                    "2",
                    request.dtm_net_sales2,
                    request.dtm_sales_tax_collected2
                )

                update_daily_taxes_manual(
                    cur,
                    request.tenant_id,
                    request.dtm_store,
                    request.dtm_file_date,
                    "3",
                    request.dtm_net_sales3,
                    request.dtm_sales_tax_collected3
                )

                update_daily_taxes_manual(
                    cur,
                    request.tenant_id,
                    request.dtm_store,
                    request.dtm_file_date,
                    "4",
                    request.dtm_net_sales4,
                    request.dtm_sales_tax_collected4
                )

                logger.info("Daily Taxes Manual updated successfully.")

                #
                # UPDATE WTD TAXES MANUAL
                #

                update_wtd_taxes_manual(
                    cur,
                    request.tenant_id,
                    request.dtm_store,
                    week_ending_date
                )

                logger.info("WTD Taxes Manual updated.")

                #
                # UPDATE DAILY TAXES
                #

                update_daily_taxes(
                    cur,
                    request.tenant_id,
                    request.dtm_store,
                    request.dtm_file_date,
                    1,
                    request.dtm_net_sales1,
                    request.dtm_sales_tax_collected1
                )

                update_daily_taxes(
                    cur,
                    request.tenant_id,
                    request.dtm_store,
                    request.dtm_file_date,
                    2,
                    request.dtm_net_sales2,
                    request.dtm_sales_tax_collected2
                )

                update_daily_taxes(
                    cur,
                    request.tenant_id,
                    request.dtm_store,
                    request.dtm_file_date,
                    3,
                    request.dtm_net_sales3,
                    request.dtm_sales_tax_collected3
                )

                update_daily_taxes(
                    cur,
                    request.tenant_id,
                    request.dtm_store,
                    request.dtm_file_date,
                    4,
                    request.dtm_net_sales4,
                    request.dtm_sales_tax_collected4
                )

                logger.info("Daily Taxes updated.")

                #
                # UPDATE WTD TAXES
                #

                update_wtd_taxes(
                    cur,
                    request.tenant_id,
                    request.dtm_store,
                    week_ending_date
                )

                logger.info("WTD Taxes updated.")

                #
                # COMMIT
                #

                conn.commit()


                #
                # AUDIT - NET SALES RATE 1
                #

                if old_values["1"]["net_sales"] != request.dtm_net_sales1:
                    insert_daily_taxes_audit(
                        cur,
                        request.tenant_id,
                        request.dtm_store,
                        request.dtm_file_date,
                        request.user,
                        (
                            f"Net Sales for Tax Rate 1 Changed From - "
                            f"{old_values['1']['net_sales']} "
                            f"To - {request.dtm_net_sales1}"
                        )
                    )

                #
                # AUDIT - NET SALES RATE 2
                #

                if old_values["2"]["net_sales"] != request.dtm_net_sales2:
                    insert_daily_taxes_audit(
                        cur,
                        request.tenant_id,
                        request.dtm_store,
                        request.dtm_file_date,
                        request.user,
                        (
                            f"Net Sales for Tax Rate 2 Changed From - "
                            f"{old_values['2']['net_sales']} "
                            f"To - {request.dtm_net_sales2}"
                        )
                    )

                #
                # AUDIT - NET SALES RATE 3
                #

                if old_values["3"]["net_sales"] != request.dtm_net_sales3:
                    insert_daily_taxes_audit(
                        cur,
                        request.tenant_id,
                        request.dtm_store,
                        request.dtm_file_date,
                        request.user,
                        (
                            f"Net Sales for Tax Rate 3 Changed From - "
                            f"{old_values['3']['net_sales']} "
                            f"To - {request.dtm_net_sales3}"
                        )
                    )

                #
                # AUDIT - NET SALES RATE 4
                #

                if old_values["4"]["net_sales"] != request.dtm_net_sales4:
                    insert_daily_taxes_audit(
                        cur,
                        request.tenant_id,
                        request.dtm_store,
                        request.dtm_file_date,
                        request.user,
                        (
                            f"Net Sales for Tax Rate 4 Changed From - "
                            f"{old_values['4']['net_sales']} "
                            f"To - {request.dtm_net_sales4}"
                        )
                    )

                #
                # AUDIT - SALES TAX RATE 1
                #

                if  old_values["1"]["sales_tax"] != request.dtm_sales_tax_collected1:
                    insert_daily_taxes_audit(
                        cur,
                        request.tenant_id,
                        request.dtm_store,
                        request.dtm_file_date,
                        request.user,
                        (
                            f"Sales Tax Collected for Tax Rate 1 "
                            f"Changed From - "
                            f"{old_values['1']['sales_tax']} "
                            f"To - {request.dtm_sales_tax_collected1}"
                        )
                    )

                #
                # AUDIT - SALES TAX RATE 2
                #

                if  old_values["2"]["sales_tax"] != request.dtm_sales_tax_collected2:
                    insert_daily_taxes_audit(
                        cur,
                        request.tenant_id,
                        request.dtm_store,
                        request.dtm_file_date,
                        request.user,
                        (
                            f"Sales Tax Collected for Tax Rate 2 "
                            f"Changed From - "
                            f"{old_values['2']['sales_tax']} "
                            f"To - {request.dtm_sales_tax_collected2}"
                        )
                    )

                #
                # AUDIT - SALES TAX RATE 3
                #

                if old_values["3"]["sales_tax"] != request.dtm_sales_tax_collected3:
                    insert_daily_taxes_audit(
                        cur,
                        request.tenant_id,
                        request.dtm_store,
                        request.dtm_file_date,
                        request.user,
                        (
                            f"Sales Tax Collected for Tax Rate 3 "
                            f"Changed From - "
                            f"{old_values['3']['sales_tax']} "
                            f"To - {request.dtm_sales_tax_collected3}"
                        )
                    )

                #
                # AUDIT - SALES TAX RATE 4
                #

                if old_values["4"]["sales_tax"] != request.dtm_sales_tax_collected4:
                    insert_daily_taxes_audit(
                        cur,
                        request.tenant_id,
                        request.dtm_store,
                        request.dtm_file_date,
                        request.user,
                        (
                            f"Sales Tax Collected for Tax Rate 4 "
                            f"Changed From - "
                            f"{old_values['4']['sales_tax']} "
                            f"To - {request.dtm_sales_tax_collected4}"
                        )
                    )

                logger.info(
                    "Audit records inserted successfully."
                )

                return {
                    "return_value": 0,
                    "error_message": ""
                }
    except Exception as ex:

        logger.exception(
            "Error in DailyTaxes Manual Update"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }