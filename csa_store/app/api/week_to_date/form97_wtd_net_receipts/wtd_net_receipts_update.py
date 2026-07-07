import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.form97_wtd_net_receipts.wtd_net_receipts_update_schema import WTDNetReceiptsUpdateRequest, WTDNetReceiptsUpdateResponse
from app.utils.week_to_date.form97_wtd_net_receipts_helper import update_dsc_with_form111, update_form111_with_mo_fees, update_form111_with_mo_receipts

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/week_to_date/form97_wtd_net_receipts",
    tags=["Week To Date Form 97 WTD Net Receipts"]
)

@router.put("/update", response_model=WTDNetReceiptsUpdateResponse)
def csa_wtd_net_receipts_update(request: WTDNetReceiptsUpdateRequest):
    """
    Equivalent of:
    csa_WTDNetReceipts_Update
    """
    try:
        # Initial Validations
        if request.wnr_store is None:
            return WTDNetReceiptsUpdateResponse(return_value=1, error_message="Invalid Store")
        
        if request.wnr_week_ending_date is None:
            return WTDNetReceiptsUpdateResponse(return_value=1, error_message="Invalid Week Ending Date")
            
        if not request.user or str(request.user).strip() == '':
            return WTDNetReceiptsUpdateResponse(return_value=1, error_message="Invalid User")

        if request.wnr_mo_receipts is None and request.wnr_nbr_of_mo is None:
            return WTDNetReceiptsUpdateResponse(return_value=1, error_message="No Updateable Attributes Received")
            
        if request.wnr_mo_receipts is None:
            return WTDNetReceiptsUpdateResponse(return_value=1, error_message="Invalid MO Receipts")
            
        if request.wnr_nbr_of_mo is None:
            return WTDNetReceiptsUpdateResponse(return_value=1, error_message="Invalid Nbr Of MOs")

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # Check if rows exist
                cur.execute("""
                    SELECT count(*)
                    FROM retail_accounting.wtd_net_receipts
                    WHERE wnr_store = %s AND wnr_week_ending_date = %s
                """, (request.wnr_store, request.wnr_week_ending_date))
                count_record = cur.fetchone()
                
                if not count_record or count_record[0] == 0:
                    return WTDNetReceiptsUpdateResponse(return_value=1, error_message="Row Not Found")

                # Fetch Old Values
                cur.execute("""
                    SELECT wnr_mo_receipts, wnr_nbr_of_mo
                    FROM retail_accounting.wtd_net_receipts
                    WHERE wnr_store = %s AND wnr_week_ending_date = %s
                """, (request.wnr_store, request.wnr_week_ending_date))
                
                old_row = cur.fetchone()
                old_mo_receipts = float(old_row[0]) if old_row[0] is not None else 0.0
                old_nbr_of_mo = int(old_row[1]) if old_row[1] is not None else 0
                
                if old_mo_receipts == request.wnr_mo_receipts and old_nbr_of_mo == request.wnr_nbr_of_mo:
                    return WTDNetReceiptsUpdateResponse(return_value=1, error_message="No Updates Detected")

                try:
                    # Update WTDNetReceipts
                    cur.execute("""
                        UPDATE retail_accounting.wtd_net_receipts
                        SET wnr_mo_receipts = %s,
                            wnr_nbr_of_mo = %s
                        WHERE wnr_store = %s AND wnr_week_ending_date = %s
                    """, (request.wnr_mo_receipts, request.wnr_nbr_of_mo, request.wnr_store, request.wnr_week_ending_date))
                    
                    # Update Form 111 with Money Order Fees
                    if old_nbr_of_mo != request.wnr_nbr_of_mo:
                        update_form111_with_mo_fees(cur, request.wnr_store, request.wnr_week_ending_date)
                        
                    # Update Form 111 with Money Order Receipts
                    if old_mo_receipts != request.wnr_mo_receipts:
                        update_form111_with_mo_receipts(cur, request.wnr_store, request.wnr_week_ending_date)
                        
                    # Update DailySalesCashTotal with Net Receipts Amount
                    update_dsc_with_form111(cur, request.wnr_store, request.wnr_week_ending_date)
                    
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    logger.exception("Transaction Failed in WTDNetReceipts_Update")
                    return WTDNetReceiptsUpdateResponse(return_value=1, error_message="Update Failed")

                # Insert Audit Logs
                audit_records = []
                if old_mo_receipts != request.wnr_mo_receipts:
                    audit_records.append((
                        str(request.tenant_id), request.wnr_store, request.wnr_week_ending_date, 12, 'U', request.user,
                        f"MO Receipts Changed From - {old_mo_receipts} To - {request.wnr_mo_receipts}"
                    ))
                    
                if old_nbr_of_mo != request.wnr_nbr_of_mo:
                    audit_records.append((
                        str(request.tenant_id), request.wnr_store, request.wnr_week_ending_date, 12, 'U', request.user,
                        f"Nbr Of MOs Changed From - {old_nbr_of_mo} To - {request.wnr_nbr_of_mo}"
                    ))

                if audit_records:
                    cur.executemany("""
                        INSERT INTO retail_history.audit
                        (tenant_id, a_store, a_date, a_form_type, a_action, a_creation_date, a_user, a_comment)
                        VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s)
                    """, audit_records)
                    conn.commit()

                return WTDNetReceiptsUpdateResponse(return_value=0, error_message="")

    except Exception as ex:
        logger.exception("Error in WTDNetReceipts_Update")
        return WTDNetReceiptsUpdateResponse(
            return_value=1,
            error_message="Update Failed"
        )
