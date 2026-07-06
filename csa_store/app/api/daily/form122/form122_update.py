import logging

from datetime import datetime

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.daily.form122.form122_update_schema import (
    Form122UpdateRequest
)

from app.utils.daily.form98_helper import (
    get_week_ending_date
)

from app.utils.daily.form122_helper import (
    update_form111_with_postage_stamps,
    update_dsc_with_form111,
    insert_form122_audit
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily/form122",
    tags=["Form122"]
)


@router.put("/update")
def form122_update(
        request: Form122UpdateRequest):
    """
    Equivalent of:

    csa_Form122_Update
    """

    try:

        #
        # VALIDATIONS
        #

        if request.psi_store is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Store"
            }

        if request.psi_books_received is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Books Received"
            }

        if request.psi_money_collected is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Money Collected"
            }

        if request.psi_books_sold is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Books Sold"
            }

        if request.psi_books_in_till is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Books In Till"
            }

        if request.psi_books_in_safe is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Books In Safe"
            }

        if request.psi_books_in_office is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Books In Office"
            }

        if (
            request.user is None
            or
            request.user.strip() == ""
        ):

            return {
                "return_value": 1,
                "error_message": "Invalid User"
            }

        with DBConnection() as conn:

            with conn.cursor() as cur:

                #
                # STORE CONFIGURATION
                #

                cur.execute("""
                    SELECT
                        sc_eow_last_run,
                        sc_eod_last_run
                    FROM retail_accounting.store_configuration
                    WHERE sc_store=%s
                """,
                (
                    request.psi_store,
                ))

                config_row = cur.fetchone()

                if not config_row:

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Store"
                    }

                sc_eow_last_run = config_row[0]
                sc_eod_last_run = config_row[1]

                #
                # WEEK ENDING DATE
                #

                week_ending_date = get_week_ending_date(
                    cur,
                    request.psi_store
                )

                #
                # VALIDATE DATE
                #
                # SQL:
                # PSI_Date must equal SC_EOD_Last_Run
                #

                if (
                    request.psi_date is None
                    or
                    request.psi_date != sc_eod_last_run.date()
                ):

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Date"
                    }

                #
                # CHECK RECORD EXISTS
                #

                cur.execute("""
                    SELECT COUNT(*)
                    FROM retail_history.postage_stamp_inventory
                    WHERE psi_store=%s
                    AND psi_date=%s
                    AND psi_process_flag='0'
                """,
                (
                    request.psi_store,
                    request.psi_date
                ))

                count = cur.fetchone()[0]

                if count == 0:

                    return {
                        "return_value": 1,
                        "error_message": "Row Not Found for Updateing"
                    }

                #
                # GET OLD VALUES
                #

                cur.execute("""
                    SELECT
                        psi_books_received,
                        psi_money_collected,
                        psi_books_sold,
                        psi_books_in_till,
                        psi_books_in_safe,
                        psi_books_in_office
                    FROM retail_history.postage_stamp_inventory
                    WHERE psi_store=%s
                    AND psi_date=%s
                    AND psi_process_flag='0'
                """,
                (
                    request.psi_store,
                    request.psi_date
                ))

                old_row = cur.fetchone()

                old_books_received = old_row[0]
                old_money_collected = old_row[1]
                old_books_sold = old_row[2]
                old_books_in_till = old_row[3]
                old_books_in_safe = old_row[4]
                old_books_in_office = old_row[5]

                #
                # UPDATE INVENTORY
                #

                cur.execute("""
                    UPDATE retail_history.postage_stamp_inventory
                    SET
                        psi_books_received=%s,
                        psi_money_collected=%s,
                        psi_books_sold=%s,
                        psi_books_in_till=%s,
                        psi_books_in_safe=%s,
                        psi_books_in_office=%s
                    WHERE psi_store=%s
                    AND psi_date=%s
                    AND psi_process_flag='0'
                """,
                (
                    request.psi_books_received,
                    request.psi_money_collected,
                    request.psi_books_sold,
                    request.psi_books_in_till,
                    request.psi_books_in_safe,
                    request.psi_books_in_office,
                    request.psi_store,
                    request.psi_date
                ))

                #
                # UPDATE FORM111
                #

                update_form111_with_postage_stamps(
                    cur,
                    request.psi_store,
                    request.psi_date,
                    week_ending_date
                )

                #
                # UPDATE DSC
                #

                update_dsc_with_form111(
                    cur,
                    request.psi_store,
                    week_ending_date
                )

                #
                # AUDIT LOGS
                #

                if old_books_received != request.psi_books_received:

                    insert_form122_audit(
                        cur,
                        request.tenant_id,
                        request.psi_store,
                        request.psi_date,
                        request.user,
                        (
                            f"Books Received Changed From: "
                            f"{old_books_received} "
                            f"To: "
                            f"{request.psi_books_received}"
                        )
                    )

                if old_money_collected != request.psi_money_collected:

                    insert_form122_audit(
                        cur,
                        request.tenant_id,
                        request.psi_store,
                        request.psi_date,
                        request.user,
                        (
                            f"Money Collected Changed From: "
                            f"{old_money_collected} "
                            f"To: "
                            f"{request.psi_money_collected}"
                        )
                    )

                if old_books_sold != request.psi_books_sold:

                    insert_form122_audit(
                        cur,
                        request.tenant_id,
                        request.psi_store,
                        request.psi_date,
                        request.user,
                        (
                            f"Books Sold Changed From: "
                            f"{old_books_sold} "
                            f"To: "
                            f"{request.psi_books_sold}"
                        )
                    )

                if old_books_in_till != request.psi_books_in_till:

                    insert_form122_audit(
                        cur,
                        request.tenant_id,
                        request.psi_store,
                        request.psi_date,
                        request.user,
                        (
                            f"Books In Till Changed From: "
                            f"{old_books_in_till} "
                            f"To: "
                            f"{request.psi_books_in_till}"
                        )
                    )

                if old_books_in_safe != request.psi_books_in_safe:

                    insert_form122_audit(
                        cur,
                        request.tenant_id,
                        request.psi_store,
                        request.psi_date,
                        request.user,
                        (
                            f"Books In Safe Changed From: "
                            f"{old_books_in_safe} "
                            f"To: "
                            f"{request.psi_books_in_safe}"
                        )
                    )

                if old_books_in_office != request.psi_books_in_office:

                    insert_form122_audit(
                        cur,
                        request.tenant_id,
                        request.psi_store,
                        request.psi_date,
                        request.user,
                        (
                            f"Books In Office Changed From: "
                            f"{old_books_in_office} "
                            f"To: "
                            f"{request.psi_books_in_office}"
                        )
                    )

                logger.info(
                    f"Form122 updated successfully "
                    f"Store={request.psi_store} "
                    f"Date={request.psi_date}"
                )

                return {
                    "return_value": 0,
                    "message": "Record Updated Successfully"
                }

    except Exception as ex:

        logger.exception(
            "Error in Form122 Update"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }