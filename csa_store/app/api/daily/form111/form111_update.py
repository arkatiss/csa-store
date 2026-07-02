import logging

from datetime import timedelta

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.daily.form111.form111_update_schema import (
    Form111UpdateRequest
)

from app.utils.daily.form98_helper import (
    get_week_ending_date
)

from app.utils.daily.form111_helper import (
    update_dsc_with_form111,
    insert_form111_update_audit
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form111",
    tags=["Form111"]
)


@router.put("/update")
def form111_update(
        request: Form111UpdateRequest):
    """
    Equivalent of:

    csa_Form111_Update
    """

    try:

        #
        # VALIDATIONS
        #

        if not request.def_id:
            return {
                "return_value": 1,
                "error_message": "Invalid ID"
            }

        if not request.def_store:
            return {
                "return_value": 1,
                "error_message": "Invalid Store"
            }

        if request.def_form_type != 7:
            return {
                "return_value": 1,
                "error_message": "Invalid Form Type"
            }

        if (
            request.def_user is None
            or
            request.def_user.strip() == ""
        ):
            return {
                "return_value": 1,
                "error_message": "Invalid User"
            }

        if (
            request.def_descriptor_1 is None
            or
            request.def_descriptor_1.strip() == ""
        ):
            return {
                "return_value": 1,
                "error_message": "Invalid Description"
            }

        if request.def_amount_1 is None:
            return {
                "return_value": 1,
                "error_message": "Invalid Retail"
            }

        if request.def_amount_2 is None:
            return {
                "return_value": 1,
                "error_message": "Invalid Cost"
            }

        with DBConnection() as conn:

            with conn.cursor() as cur:

                #
                # WEEK ENDING DATE
                #

                week_ending_date = get_week_ending_date(
                    cur,
                    request.def_store
                )

                if (
                    request.def_date <
                    (week_ending_date - timedelta(days=7))
                    or
                    request.def_date >
                    (week_ending_date + timedelta(days=1))
                ):
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Date"
                    }

                #
                # RECORD EXISTS
                #

                cur.execute("""
                    SELECT COUNT(*)
                    FROM retail_accounting.data_entry_forms
                    WHERE tenant_id=%s
                    AND def_id=%s
                """,
                (
                    str(request.tenant_id),
                    request.def_id
                ))

                count = cur.fetchone()[0]

                if count == 0:
                    return {
                        "return_value": 1,
                        "error_message": "Identity Not Found"
                    }

                #
                # OLD VALUES
                #

                cur.execute("""
                    SELECT
                        def_store,
                        def_date,
                        def_form_type,
                        def_user,
                        def_descriptor_1,
                        def_descriptor_2,
                        def_amount_1,
                        def_amount_2
                    FROM retail_accounting.data_entry_forms
                    WHERE tenant_id=%s
                    AND def_id=%s
                """,
                (
                    str(request.tenant_id),
                    request.def_id
                ))

                old_row = cur.fetchone()

                old_store = old_row[0]
                old_date = old_row[1]
                old_form_type = old_row[2]
                old_user = old_row[3]
                old_desc1 = old_row[4]
                old_desc2 = old_row[5]
                old_amount1 = old_row[6]
                old_amount2 = old_row[7]

                #
                # STORE VALIDATION
                #

                if old_store != request.def_store:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Store"
                    }

                #
                # FORM TYPE VALIDATION
                #

                if old_form_type != request.def_form_type:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Form Type"
                    }

                #
                # NON UPDATEABLE USERS
                #

                non_updateable = [
                    "DrinkMachineSales",
                    "TaxOnDrinkSales",
                    "PostageStampInventory",
                    "MoneyOrderFees",
                    "MoneyOrderReceipts"
                ]

                if old_user in non_updateable:
                    return {
                        "return_value": 1,
                        "error_message":
                            "Invalid Update - Non-Updateable Row"
                    }

                #
                # UPDATE
                #

                cur.execute("""
                    UPDATE retail_accounting.data_entry_forms
                    SET
                        def_date=%s,
                        def_user=%s,
                        def_descriptor_1=%s,
                        def_descriptor_2=%s,
                        def_amount_1=%s,
                        def_amount_2=%s,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE tenant_id=%s
                    AND def_id=%s
                """,
                (
                    request.def_date,
                    request.def_user,
                    request.def_descriptor_1,
                    request.def_descriptor_2,
                    request.def_amount_1,
                    request.def_amount_2,
                    str(request.tenant_id),
                    request.def_id
                ))

                #
                # UPDATE DSC
                #

                update_dsc_with_form111(
                    cur,
                    request.tenant_id,
                    request.def_store,
                    week_ending_date
                )

                conn.commit()

                #
                # AUDITS
                #

                if old_date.date() != request.def_date:

                    insert_form111_update_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"Date Changed From: "
                        f"{old_date.strftime('%m/%d/%y')} "
                        f"To: {request.def_date}"
                    )

                if old_user != request.def_user:

                    insert_form111_update_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"User Changed From: "
                        f"{old_user} To: {request.def_user}"
                    )

                if old_desc1 != request.def_descriptor_1:

                    insert_form111_update_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"Descriptor 1 Changed From: "
                        f"{old_desc1} To: "
                        f"{request.def_descriptor_1}"
                    )

                if old_desc2 != request.def_descriptor_2:

                    old_value = (
                        "Blank"
                        if old_desc2 is None
                        else old_desc2
                    )

                    insert_form111_update_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"Descriptor 2 Changed From: "
                        f"{old_value} To: "
                        f"{request.def_descriptor_2}"
                    )

                if old_amount1 != request.def_amount_1:

                    insert_form111_update_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"Amount 1 Changed From: "
                        f"{old_amount1} To: "
                        f"{request.def_amount_1}"
                    )

                if old_amount2 != request.def_amount_2:

                    insert_form111_update_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"Amount 2 Changed From: "
                        f"{old_amount2} To: "
                        f"{request.def_amount_2}"
                    )

                conn.commit()

                return {
                    "return_value": 0,
                    "message":
                        "Form111 Updated Successfully"
                }

    except Exception as ex:

        logger.exception(
            "Error in Form111 Update"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }