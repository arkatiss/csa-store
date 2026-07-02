from datetime import timedelta

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.daily.form98.form98_request import Form98InsertRequest

from app.utils.daily.form98_helper import (
    get_week_ending_date,
    update_dsc_with_form98,
    update_wcb_with_form98,
    insert_update_audit
)

router = APIRouter(
    prefix="/form98",
    tags=["Form98"]
)


@router.put("/update")
def form98_update(request: Form98InsertRequest):

    try:

        with DBConnection() as conn:

            with conn.cursor() as cur:

                tenant_id =str(request.tenant_id)

                # =====================================================
                # VALIDATIONS
                # =====================================================



                if not request.cb_store:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Store"
                    }

                week_ending_date = get_week_ending_date(
                    cur,
                    request.cb_store
                )

                last_week_ending_date = (
                    week_ending_date -
                    timedelta(days=7)
                )

                print(f"CB Date              : {request.cb_date}")
                print(f"Week Ending Date     : {week_ending_date}")
                print(f"Last Week Ending Date: {last_week_ending_date}")

                if (
                    request.cb_date is None
                    or
                    request.cb_date <= last_week_ending_date
                    or
                    request.cb_date > (
                        week_ending_date +
                        timedelta(days=1)
                    )
                ):
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Date"
                    }

                if not request.cb_employee_id:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Employee ID"
                    }

                if request.cb_till is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Till Number"
                    }

                if not request.cb_name:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Employee Name"
                    }

                if request.cb_sales is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Sales"
                    }

                if request.cb_voids is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Voids"
                    }

                if request.cb_returns is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Returns"
                    }

                if request.cb_checks is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Checks"
                    }

                if request.cb_gift_cards_tendered is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Gift Cards"
                    }

                if request.cb_ebt is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid EBT"
                    }

                if request.cb_credit_cards is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Credit Cards"
                    }

                if request.cb_wic is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid WIC"
                    }

                if request.cb_charges is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Charges"
                    }

                if request.cb_debit_cards is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Debit Cards"
                    }

                if request.cb_vendor_coupons is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Vendor Coupons"
                    }

                if request.cb_pfc_coupons is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid PFC_Coupons"
                    }

                if request.cb_cashier_over_short is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Cashier Over/Short"
                    }

                if request.cb_promo_coupons is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Promo Coupons"
                    }

                if request.cb_miscellaneous is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Miscellaneous"
                    }

                if request.cb_user is None or request.cb_user == "":
                    return {
                        "return_value": 1,
                        "error_message": "Invalid User"
                    }

                numeric_fields = [
                    ("Sales", request.cb_sales),
                    ("Voids", request.cb_voids),
                    ("Returns", request.cb_returns),
                    ("Checks", request.cb_checks),
                    ("Gift Cards", request.cb_gift_cards_tendered),
                    ("EBT", request.cb_ebt),
                    ("Credit Cards", request.cb_credit_cards),
                    ("WIC", request.cb_wic),
                    ("Charges", request.cb_charges),
                    ("Debit Cards", request.cb_debit_cards),
                    ("Vendor Coupons", request.cb_vendor_coupons),
                    ("PFC Coupons", request.cb_pfc_coupons),
                    ("Cashier Over/Short", request.cb_cashier_over_short),
                    ("Promo Coupons", request.cb_promo_coupons),
                    ("Miscellaneous", request.cb_miscellaneous),
                ]

                for field_name, value in numeric_fields:

                    if value is None:

                        return {
                            "return_value": 1,
                            "error_message": f"Invalid {field_name}"
                        }

                # =====================================================
                # RECORD EXISTS ?
                # =====================================================

                cur.execute("""
                    SELECT COUNT(*)
                    FROM retail_history.cashier_balance
                    WHERE cb_store=%s
                    AND cb_date=%s
                    AND cb_employee_id=%s
                    AND cb_till=%s
                """,
                (
                    request.cb_store,
                    request.cb_date,
                    request.cb_employee_id,
                    request.cb_till
                ))

                count = cur.fetchone()[0]

                if count == 0:

                    return {
                        "return_value": 1,
                        "error_message": "Cashier Balance Not Found"
                    }

                # =====================================================
                # OLD VALUES
                # =====================================================

                cur.execute("""
                    SELECT *
                    FROM retail_history.cashier_balance
                    WHERE cb_store=%s
                    AND cb_date=%s
                    AND cb_employee_id=%s
                    AND cb_till=%s
                """,
                (
                    request.cb_store,
                    request.cb_date,
                    request.cb_employee_id,
                    request.cb_till
                ))

                old_row = cur.fetchone()

                old_cb_store = old_row[1]
                old_cb_date = old_row[2]
                old_cb_employee_id = old_row[3]
                old_cb_till = old_row[4]
                old_cb_name = old_row[5]
                old_cb_sales = old_row[6]
                old_cb_voids = old_row[7]
                old_cb_returns = old_row[8]
                old_cb_checks = old_row[9]
                old_cb_gift_cards_tendered = old_row[10]
                old_cb_ebt = old_row[11]
                old_cb_credit_cards = old_row[12]
                old_cb_wic = old_row[13]
                old_cb_charges = old_row[14]
                old_cb_debit_cards = old_row[15]
                old_cb_vendor_coupons = old_row[16]
                old_cb_pfc_coupons = old_row[17]
                old_cb_cashier_over_short = old_row[18]
                old_cb_user = old_row[19]
                old_cb_promo_coupons = old_row[20]
                old_cb_miscellaneous = old_row[21]

                old_values = {
                    "cb_name": old_row[5],
                    "cb_sales": old_row[6],
                    "cb_voids": old_row[7],
                    "cb_returns": old_row[8],
                    "cb_checks": old_row[9],
                    "cb_gift_cards_tendered": old_row[10],
                    "cb_ebt": old_row[11],
                    "cb_credit_cards": old_row[12],
                    "cb_wic": old_row[13],
                    "cb_charges": old_row[14],
                    "cb_debit_cards": old_row[15],
                    "cb_vendor_coupons": old_row[16],
                    "cb_pfc_coupons": old_row[17],
                    "cb_cashier_over_short": old_row[18],
                    "cb_user": old_row[19],
                    "cb_promo_coupons": old_row[20],
                    "cb_miscellaneous": old_row[21]
                }

                # =====================================================
                # UPDATE
                # =====================================================

                cur.execute("""
                    UPDATE retail_history.cashier_balance
                    SET
                        cb_name=%s,
                        cb_sales=%s,
                        cb_voids=%s,
                        cb_returns=%s,
                        cb_checks=%s,
                        cb_gift_cards_tendered=%s,
                        cb_ebt=%s,
                        cb_credit_cards=%s,
                        cb_wic=%s,
                        cb_charges=%s,
                        cb_debit_cards=%s,
                        cb_vendor_coupons=%s,
                        cb_pfc_coupons=%s,
                        cb_cashier_over_short=%s,
                        cb_user=%s,
                        cb_promo_coupons=%s,
                        cb_miscellaneous=%s,
                        last_updated_by=%s,
                        last_update_date=CURRENT_TIMESTAMP
                    WHERE cb_store=%s
                    AND cb_date=%s
                    AND cb_employee_id=%s
                    AND cb_till=%s
                """,
                (
                    request.cb_name,
                    request.cb_sales,
                    request.cb_voids,
                    request.cb_returns,
                    request.cb_checks,
                    request.cb_gift_cards_tendered,
                    request.cb_ebt,
                    request.cb_credit_cards,
                    request.cb_wic,
                    request.cb_charges,
                    request.cb_debit_cards,
                    request.cb_vendor_coupons,
                    request.cb_pfc_coupons,
                    request.cb_cashier_over_short,
                    request.cb_user,
                    request.cb_promo_coupons,
                    request.cb_miscellaneous,
                    request.cb_user,
                    request.cb_store,
                    request.cb_date,
                    request.cb_employee_id,
                    request.cb_till
                ))

                if old_cb_name != request.cb_name:
                    insert_update_audit(
                        cur,
                        tenant_id,
                        request.cb_store,
                        request.cb_date,
                        request.cb_user,
                        f"Name Changed From: {old_cb_name} To: {request.cb_name}"
                    )

                if old_cb_sales != request.cb_sales:
                    insert_update_audit(
                        cur,
                        tenant_id,
                        request.cb_store,
                        request.cb_date,
                        request.cb_user,
                        f"Sales Changed From: {old_cb_sales} To: {request.cb_sales}"
                    )

                if old_cb_voids != request.cb_voids:
                    insert_update_audit(
                        cur,
                        tenant_id,
                        request.cb_store,
                        request.cb_date,
                        request.cb_user,
                        f"Voids Changed From: {old_cb_voids} To: {request.cb_voids}"
                    )

                if old_cb_returns != request.cb_returns:
                    insert_update_audit(
                        cur,
                        tenant_id,
                        request.cb_store,
                        request.cb_date,
                        request.cb_user,
                        f"Returns Changed From: {old_cb_returns} To: {request.cb_returns}"
                    )

                if old_cb_returns != request.cb_returns:
                    insert_update_audit(
                        cur,
                        tenant_id,
                        request.cb_store,
                        request.cb_date,
                        request.cb_user,
                        f"Returns Changed From: {old_cb_returns} To: {request.cb_returns}"
                    )

                if old_cb_gift_cards_tendered != request.cb_gift_cards_tendered:
                    insert_update_audit(
                        cur,
                        tenant_id,
                        request.cb_store,
                        request.cb_date,
                        request.cb_user,
                        f"Gift Cards Tendered Changed From: "
                        f"{old_cb_gift_cards_tendered} "
                        f"To: "
                        f"{request.cb_gift_cards_tendered}"
                    )

                if old_cb_ebt != request.cb_ebt:
                    insert_update_audit(
                        cur,
                        tenant_id,
                        request.cb_store,
                        request.cb_date,
                        request.cb_user,
                        f"EBT Changed From: {old_cb_ebt} To: {request.cb_ebt}"
                    )

                if old_cb_credit_cards != request.cb_credit_cards:
                    insert_update_audit(
                        cur,
                        tenant_id,
                        request.cb_store,
                        request.cb_date,
                        request.cb_user,
                        f"Credit Cards Changed From: "
                        f"{old_cb_credit_cards} "
                        f"To: "
                        f"{request.cb_credit_cards}"
                    )

                if old_cb_wic != request.cb_wic:
                    insert_update_audit(
                        cur,
                        tenant_id,
                        request.cb_store,
                        request.cb_date,
                        request.cb_user,
                        f"WIC Changed From: {old_cb_wic} To: {request.cb_wic}"
                    )

                if old_cb_charges != request.cb_charges:
                    insert_update_audit(
                        cur,
                        tenant_id,
                        request.cb_store,
                        request.cb_date,
                        request.cb_user,
                        f"Charges Changed From: {old_cb_charges} To: {request.cb_charges}"
                    )

                if old_cb_debit_cards != request.cb_debit_cards:
                    insert_update_audit(
                        cur,
                        tenant_id,
                        request.cb_store,
                        request.cb_date,
                        request.cb_user,
                        f"Debit Cards Changed From: "
                        f"{old_cb_debit_cards} "
                        f"To: "
                        f"{request.cb_debit_cards}"
                    )

                if old_cb_vendor_coupons != request.cb_vendor_coupons:
                    insert_update_audit(
                        cur,
                        tenant_id,
                        request.cb_store,
                        request.cb_date,
                        request.cb_user,
                        f"Vendor Coupons Changed From: "
                        f"{old_cb_vendor_coupons} "
                        f"To: "
                        f"{request.cb_vendor_coupons}"
                    )

                if old_cb_pfc_coupons != request.cb_pfc_coupons:
                    insert_update_audit(
                        cur,
                        tenant_id,
                        request.cb_store,
                        request.cb_date,
                        request.cb_user,
                        f"PFC Coupons Changed From: "
                        f"{old_cb_pfc_coupons} "
                        f"To: "
                        f"{request.cb_pfc_coupons}"
                    )

                if old_cb_cashier_over_short != request.cb_cashier_over_short:
                    insert_update_audit(
                        cur,
                        tenant_id,
                        request.cb_store,
                        request.cb_date,
                        request.cb_user,
                        f"Cashier Over Short Changed From: "
                        f"{old_cb_cashier_over_short} "
                        f"To: "
                        f"{request.cb_cashier_over_short}"
                    )

                if old_cb_user != request.cb_user:
                    insert_update_audit(
                        cur,
                        tenant_id,
                        request.cb_store,
                        request.cb_date,
                        request.cb_user,
                        f"User Changed From: "
                        f"{old_cb_user} "
                        f"To: "
                        f"{request.cb_user}"
                    )

                if old_cb_promo_coupons != request.cb_promo_coupons:
                    insert_update_audit(
                        cur,
                        tenant_id,
                        request.cb_store,
                        request.cb_date,
                        request.cb_user,
                        f"Promo Coupons Changed From: "
                        f"{old_cb_promo_coupons} "
                        f"To: "
                        f"{request.cb_promo_coupons}"
                    )

                if old_cb_miscellaneous != request.cb_miscellaneous:
                    insert_update_audit(
                        cur,
                        tenant_id,
                        request.cb_store,
                        request.cb_date,
                        request.cb_user,
                        f"Miscellaneous Changed From: "
                        f"{old_cb_miscellaneous} "
                        f"To: "
                        f"{request.cb_miscellaneous}"
                    )



                # =====================================================
                # OFFICE BALANCE UPDATE
                # =====================================================

                try:

                    cur.execute("""
                        SELECT COALESCE(
                            SUM(cb_cashier_over_short),
                            0
                        )
                        FROM retail_history.cashier_balance
                        WHERE cb_store=%s
                        AND cb_date > %s
                        AND cb_date <= %s
                    """,
                    (
                        request.cb_store,
                        last_week_ending_date,
                        week_ending_date
                    ))
                except Exception:

                    return {
                        "return_value": 1,
                        "error_message": "Update Office Balance Failed"
                    }

                ob_cashier_over_short = cur.fetchone()[0]

                cur.execute("""
                    UPDATE retail.office_balance
                    SET
                        ob_cashier_over_short=%s,
                        ob_net_accountability=
                            ob_petty_cash_fund +
                            ob_petty_cash_advances +
                            %s
                    WHERE ob_store=%s
                """,
                (
                    ob_cashier_over_short,
                    ob_cashier_over_short,
                    request.cb_store
                ))

                try:

                    update_dsc_with_form98(
                        cur,
                        request.cb_store,
                        week_ending_date
                    )

                except Exception:

                    return {
                        "return_value": 1,
                        "error_message": "Update Failed"
                    }

                try:

                    update_wcb_with_form98(
                        cur,
                        request.cb_store
                    )

                except Exception:

                    return {
                        "return_value": 1,
                        "error_message": "Update WTD Cashier Balance Failed"
                    }

                # =====================================================
                # AUDIT CHANGES
                # =====================================================

                audit_fields = {
                    "Name": (
                        old_values["cb_name"],
                        request.cb_name
                    ),
                    "Sales": (
                        old_values["cb_sales"],
                        request.cb_sales
                    ),
                    "Voids": (
                        old_values["cb_voids"],
                        request.cb_voids
                    ),
                    "Returns": (
                        old_values["cb_returns"],
                        request.cb_returns
                    ),
                    "Checks": (
                        old_values["cb_checks"],
                        request.cb_checks
                    ),
                    "Gift Cards": (
                        old_values["cb_gift_cards_tendered"],
                        request.cb_gift_cards_tendered
                    ),
                    "EBT": (
                        old_values["cb_ebt"],
                        request.cb_ebt
                    ),
                    "Credit Cards": (
                        old_values["cb_credit_cards"],
                        request.cb_credit_cards
                    ),
                    "WIC": (
                        old_values["cb_wic"],
                        request.cb_wic
                    ),
                    "Charges": (
                        old_values["cb_charges"],
                        request.cb_charges
                    ),
                    "Debit Cards": (
                        old_values["cb_debit_cards"],
                        request.cb_debit_cards
                    ),
                    "Vendor Coupons": (
                        old_values["cb_vendor_coupons"],
                        request.cb_vendor_coupons
                    ),
                    "PFC Coupons": (
                        old_values["cb_pfc_coupons"],
                        request.cb_pfc_coupons
                    ),
                    "Cashier Over Short": (
                        old_values["cb_cashier_over_short"],
                        request.cb_cashier_over_short
                    ),
                    "Promo Coupons": (
                        old_values["cb_promo_coupons"],
                        request.cb_promo_coupons
                    ),
                    "Miscellaneous": (
                        old_values["cb_miscellaneous"],
                        request.cb_miscellaneous
                    )
                }

                for field_name, values in audit_fields.items():

                    old_value, new_value = values

                    if old_value != new_value:

                        insert_update_audit(
                            cur,
                            tenant_id,
                            request.cb_store,
                            request.cb_date,
                            request.cb_user,
                            f"{field_name} Changed From: {old_value} To: {new_value}"
                        )

                try:

                    conn.commit()

                except Exception:

                    return {
                        "return_value": 1,
                        "error_message": "Commit Failed"
                    }

                return {
                    "return_value": 0,
                    "message": "Cashier Balance Updated Successfully"
                }

    except Exception as e:

        return {
            "return_value": 1,
            "error_message": str(e)
        }