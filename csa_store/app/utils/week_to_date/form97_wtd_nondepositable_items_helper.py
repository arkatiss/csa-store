
### File 2: helper.py
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

def update_dsc_with_wndi(cur, tenant_id, store, week_ending_date):
    """
    Equivalent of a helper procedure to update Daily Sales Cash Total 
    based on changes in Non-Depositable Items.
    
    Logic: Recalculates the actual daily deposits by subtracting non-depositable 
    items from net receipts.
    """
    try:
        # Calculate the total of all non-depositable items for the given store and week
        cur.execute("""
            SELECT 
                (wndi_cash_savers + wndi_gift_certificates + wndi_vendor_coupons + 
                 wndi_third_party_rx + wndi_miscellaneous + wndi_pfc_coupons + 
                 wndi_elec_gbax_coupons) as total_non_depositable
            FROM retail_accounting.wtd_non_depositable_items
            WHERE wndi_store = %s AND wndi_week_ending_date = %s
        """, (store, week_ending_date))
        
        result = cur.fetchone()
        total_non_depositable = result[0] if result and result[0] is not None else Decimal('0.0000')

        # Update the daily_sales_cash_total table
        # dsct_actual_daily_deposits is typically derived from net receipts minus non-depositable items
        cur.execute("""
            UPDATE retail_accounting.daily_sales_cash_total
            SET dsct_key_entered =
            (
                SELECT
                    wndi_cash_savers +
                    wndi_gift_certificates +
                    wndi_vendor_coupons +
                    wndi_third_party_rx +
                    wndi_miscellaneous +
                    wndi_pfc_coupons +
                    wndi_elec_gbax_coupons
                FROM retail_accounting.wtd_non_depositable_items
                WHERE wndi_store=%s
                AND wndi_week_ending_date=%s
            )
            WHERE dsct_store=%s
            AND dsct_week_ending_date=%s
            """,
            (
                store,
                week_ending_date,
                store,
                week_ending_date
            ))

        logger.info(f"Successfully updated daily_sales_cash_total for store {store}")
        
    except Exception as e:
        logger.exception("Error in update_dsc_with_wndi helper function")
        raise e

def check_wndi_existence(cur, tenant_id, store, week_ending_date):
    """
    Helper to verify if a record exists in wtd_non_depositable_items.
    """
    cur.execute("""
        SELECT COUNT(*) 
        FROM retail_accounting.wtd_non_depositable_items 
        WHERE wndi_store = %s AND wndi_week_ending_date = %s
    """, (store, week_ending_date))
    count = cur.fetchone()[0]
    return count > 0

