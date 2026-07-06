import logging

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.daily.form112.form112_update_schema import (
    Form112UpdateRequest
)

from app.utils.daily.form98_helper import (
    get_week_ending_date
)

from app.utils.daily.form112_helper import (
    update_form111_with_drink_machine_sales,
    update_dsc_with_form111
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily/form112",
    tags=["Form112"]
)


@router.put("/update")
def form112_update(
        request: Form112UpdateRequest):
    """
    Equivalent of:

    csa_Form112_Update
    """

    conn = None

    try:

        with DBConnection() as conn:

            with conn.cursor() as cur:

                #
                # VALIDATIONS
                #

                if request.dms_store is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Store"
                    }

                if request.dms_machine_nbr is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Drink Machine Nbr"
                    }

                if request.dms_actual_sales is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Actual Sales"
                    }

                if (
                        request.created_by is None
                        or
                        request.created_by.strip() == ""
                ):
                    return {
                        "return_value": 1,
                        "error_message": "Invalid User"
                    }

                cur.execute("""
                    SELECT
                        sc_eow_last_run,
                        sc_eod_last_run
                    FROM retail_accounting.store_configuration
                    WHERE tenant_id=%s
                    AND sc_store=%s
                """,
                            (
                                str(request.tenant_id),
                                request.dms_store
                            ))

                config_row = cur.fetchone()

                if not config_row:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Store"
                    }

                sc_eow_last_run = config_row[0]
                sc_eod_last_run = config_row[1]

                week_ending_date = get_week_ending_date(
                    cur,
                    request.dms_store
                )

                if (
                        request.dms_date is None
                        or
                        request.dms_date != sc_eod_last_run.date()
                ):
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Date"
                    }

                cur.execute("""
                    SELECT
                        dm_count_type,
                        dm_price_per_sale
                    FROM retail_accounting.drink_machines
                    WHERE tenant_id=%s
                    AND dm_store=%s
                    AND dm_machine_nbr=%s
                """,
                            (
                                str(request.tenant_id),
                                request.dms_store,
                                request.dms_machine_nbr
                            ))

                machine_row = cur.fetchone()

                if not machine_row:
                    return {
                        "return_value": 1,
                        "error_message": "Drink Machine Not Found"
                    }

                dm_count_type = machine_row[0]
                dm_price_per_sale = machine_row[1]

                cur.execute("""
                    SELECT
                        dms_beginning_reading,
                        dms_ending_reading,
                        dms_nbr_of_sales,
                        dms_actual_sales
                    FROM retail_history.drink_machine_sales
                    WHERE tenant_id=%s
                    AND dms_store=%s
                    AND dms_date=%s
                    AND dms_machine_nbr=%s
                    AND dms_process_flag='0'
                """,
                            (
                                str(request.tenant_id),
                                request.dms_store,
                                request.dms_date,
                                request.dms_machine_nbr
                            ))

                existing_row = cur.fetchone()

                if not existing_row:
                    return {
                        "return_value": 1,
                        "error_message": "Row Not Found for Updating"
                    }

                (
                    old_beginning_reading,
                    old_ending_reading,
                    old_nbr_of_sales,
                    old_actual_sales
                ) = existing_row

                if dm_count_type == "R":

                    if request.dms_ending_reading is None:
                        return {
                            "return_value": 1,
                            "error_message": "Invalid Ending Reading"
                        }

                    calculated_sales = (
                            request.dms_ending_reading -
                            old_beginning_reading
                    )

                    if calculated_sales < 0:
                        return {
                            "return_value": 1,
                            "error_message": "Ending Reading Less Than Beginning Reading"
                        }

                    dms_nbr_of_sales = calculated_sales

                else:

                    if request.dms_nbr_of_sales is None:
                        return {
                            "return_value": 1,
                            "error_message": "Invalid Number Of Sales"
                        }

                    dms_nbr_of_sales = request.dms_nbr_of_sales

                cur.execute("""
                    UPDATE retail_history.drink_machine_sales
                    SET
                        dms_ending_reading=%s,
                        dms_nbr_of_sales=%s,
                        dms_actual_sales=%s,
                        last_updated_by=%s,
                        last_update_date=CURRENT_TIMESTAMP
                    WHERE tenant_id=%s
                    AND dms_store=%s
                    AND dms_date=%s
                    AND dms_machine_nbr=%s
                    AND dms_process_flag='0'
                """,
                            (
                                request.dms_ending_reading,
                                dms_nbr_of_sales,
                                request.dms_actual_sales,
                                request.created_by,
                                str(request.tenant_id),
                                request.dms_store,
                                request.dms_date,
                                request.dms_machine_nbr
                            ))

                update_form111_with_drink_machine_sales(
                    cur,
                    request.tenant_id,
                    request.dms_store,
                    request.dms_date,
                    request.dms_machine_nbr,
                    week_ending_date
                )

                update_dsc_with_form111(
                    cur,
                    request.tenant_id,
                    request.dms_store,
                    week_ending_date
                )

                audit_messages = []

                if old_ending_reading != request.dms_ending_reading:
                    audit_messages.append(
                        f"Ending Reading Changed From: "
                        f"{old_ending_reading} To: "
                        f"{request.dms_ending_reading}"
                    )

                if old_nbr_of_sales != dms_nbr_of_sales:
                    audit_messages.append(
                        f"Number Of Sales Changed From: "
                        f"{old_nbr_of_sales} To: "
                        f"{dms_nbr_of_sales}"
                    )

                if float(old_actual_sales) != float(request.dms_actual_sales):
                    audit_messages.append(
                        f"Actual Sales Changed From: "
                        f"{old_actual_sales} To: "
                        f"{request.dms_actual_sales}"
                    )

                for message in audit_messages:
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
                            112,
                            'U',
                            CURRENT_TIMESTAMP,
                            %s,
                            %s
                        )
                    """,
                                (
                                    str(request.tenant_id),
                                    request.dms_store,
                                    request.dms_date,
                                    request.created_by,
                                    message
                                ))
                conn.commit()

                return {
                    "return_value": 0,
                    "message": "Drink Machine Sales Updated Successfully"
                }

    except Exception as ex:

        if conn:
            conn.rollback()

        logger.exception(
            "Error in Form112 Update"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }