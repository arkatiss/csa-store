import logging
from fastapi import APIRouter, HTTPException
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.form97_nondepositable_items.wtd_nondepositable_items_schema import (
    WTDNonDepositableItemsUpdateRequest, 
    WTDNonDepositableItemsUpdateResponse
)
from app.utils.week_to_date.form97_wtd_nondepositable_items_helper import (
    update_dsc_with_wndi,
    check_wndi_existence
)

# Configure Logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/week_to_date/wtd_non_depositable_items",
    tags=["WTD Non Depositable Items"]
)

@router.put("/update", response_model=WTDNonDepositableItemsUpdateResponse)
def csa_wtd_non_depositable_items_update(request: WTDNonDepositableItemsUpdateRequest):
    """
    Production-grade migration of the update procedure for WTD Non-Depositable Items.
    This API updates the non-depositable items for a specific store and week,
    recalculates related cash totals, and logs all changes to the audit table.
    """
    try:
        # 1. Initial Validations
        if not request.wndi_store:
            return WTDNonDepositableItemsUpdateResponse(return_value=1, error_message="Invalid Store")
        
        if not request.wndi_week_ending_date:
            return WTDNonDepositableItemsUpdateResponse(return_value=1, error_message="Invalid Week Ending Date")
            
        if not request.user or request.user.strip() == '':
            return WTDNonDepositableItemsUpdateResponse(return_value=1, error_message="Invalid User")
        
        if (
            request.wndi_cash_savers is None and
            request.wndi_gift_certificates is None and
            request.wndi_vendor_coupons is None and
            request.wndi_third_party_rx is None and
            request.wndi_miscellaneous is None and
            request.wndi_pfc_coupons is None and
            request.wndi_elec_gbax_coupons is None):
            return WTDNonDepositableItemsUpdateResponse(
                return_value=1,
                error_message="No Updateable Attributes Received"
            )

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # 2. Check if record exists
                if not check_wndi_existence(cur, request.tenant_id, request.wndi_store, request.wndi_week_ending_date):
                    return WTDNonDepositableItemsUpdateResponse(return_value=1, error_message="Record Not Found")

                # 3. Fetch Old Values for Auditing and Change Detection
                cur.execute("""
                    SELECT 
                        wndi_cash_savers, wndi_gift_certificates, wndi_vendor_coupons,
                        wndi_third_party_rx, wndi_miscellaneous, wndi_pfc_coupons,
                        wndi_elec_gbax_coupons
                    FROM retail_accounting.wtd_non_depositable_items
                    WHERE wndi_store = %s AND wndi_week_ending_date = %s
                """, (request.wndi_store, request.wndi_week_ending_date))
                
                old_row = cur.fetchone()
                old_vals = {
                    "wndi_cash_savers": old_row[0],
                    "wndi_gift_certificates": old_row[1],
                    "wndi_vendor_coupons": old_row[2],
                    "wndi_third_party_rx": old_row[3],
                    "wndi_miscellaneous": old_row[4],
                    "wndi_pfc_coupons": old_row[5],
                    "wndi_elec_gbax_coupons": old_row[6]
                }

# Check for No Updates Detected
# ----------------------------

                if (
                    old_vals["wndi_cash_savers"] == request.wndi_cash_savers and
                    old_vals["wndi_gift_certificates"] == request.wndi_gift_certificates and
                    old_vals["wndi_vendor_coupons"] == request.wndi_vendor_coupons and
                    old_vals["wndi_third_party_rx"] == request.wndi_third_party_rx and
                    old_vals["wndi_miscellaneous"] == request.wndi_miscellaneous and
                    old_vals["wndi_pfc_coupons"] == request.wndi_pfc_coupons and
                    old_vals["wndi_elec_gbax_coupons"] == request.wndi_elec_gbax_coupons
                ):
                    return WTDNonDepositableItemsUpdateResponse(
                        return_value=1,
                        error_message="No Updates Detected"
                    )

                # ----------------------------
                # Prepare Audit Messages
                # ----------------------------

                audit_logs = []

                field_names = {
                    "wndi_cash_savers": "Cash Savers",
                    "wndi_gift_certificates": "Gift Certificates",
                    "wndi_vendor_coupons": "Vendor Coupons",
                    "wndi_third_party_rx": "Third Party R/X",
                    "wndi_miscellaneous": "Miscellaneous",
                    "wndi_pfc_coupons": "PFC Coupons",
                    "wndi_elec_gbax_coupons": "Electronic GBAX Coupons"
                }

                fields_to_check = [
                    "wndi_cash_savers",
                    "wndi_gift_certificates",
                    "wndi_vendor_coupons",
                    "wndi_third_party_rx",
                    "wndi_miscellaneous",
                    "wndi_pfc_coupons",
                    "wndi_elec_gbax_coupons"
                ]

                for field in fields_to_check:
                    old_value = old_vals[field]
                    new_value = getattr(request, field)

                    if old_value != new_value:
                        audit_logs.append((
                            str(request.tenant_id),
                            request.wndi_store,
                            request.wndi_week_ending_date,
                            13,
                            "U",
                            request.user,
                            f"{field_names[field]} Changed From - {old_value} To - {new_value}"
                        ))

                # 5. Execute Update
                # 5. Execute Update
                cur.execute("""
                    UPDATE retail_accounting.wtd_non_depositable_items
                    SET
                        wndi_cash_savers = %s,
                        wndi_gift_certificates = %s,
                        wndi_vendor_coupons = %s,
                        wndi_third_party_rx = %s,
                        wndi_miscellaneous = %s,
                        wndi_pfc_coupons = %s,
                        wndi_elec_gbax_coupons = %s,
                        updated_at = NOW(),
                        updated_by = %s
                    WHERE
                        wndi_store = %s
                    AND
                        wndi_week_ending_date = %s
                """,
                (
                    request.wndi_cash_savers,
                    request.wndi_gift_certificates,
                    request.wndi_vendor_coupons,
                    request.wndi_third_party_rx,
                    request.wndi_miscellaneous,
                    request.wndi_pfc_coupons,
                    request.wndi_elec_gbax_coupons,
                    request.user,
                    request.wndi_store,
                    request.wndi_week_ending_date
                ))

                # 6. Call Helper to update Daily Sales Cash Total
                update_dsc_with_wndi(cur, request.tenant_id, request.wndi_store, request.wndi_week_ending_date)

                # 7. Insert Audit Records
                if audit_logs:
                    cur.executemany("""
                        INSERT INTO retail_history.audit
                        (tenant_id, a_store, a_date, a_form_type, a_action, a_creation_date, a_user, a_comment)
                        VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s)
                    """, audit_logs)

                conn.commit()
                logger.info(f"Successfully updated WTD Non-Depositable Items for store {request.wndi_store}")
                return WTDNonDepositableItemsUpdateResponse(return_value=0, error_message="")

    except Exception as ex:
        logger.exception(f"Error in csa_wtd_non_depositable_items_update: {str(ex)}")
        return WTDNonDepositableItemsUpdateResponse(
            return_value=1,
            error_message=f"Update Failed: {str(ex)}"
        )