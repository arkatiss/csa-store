import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.pos_entry_form.form_pos_init_schema import FormPOSInitRequest, FormPOSInitResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/week_to_date/pos_entry_form",
    tags=["Week To Date POS Entry Form"]
)

@router.post("/form_pos_init", response_model=FormPOSInitResponse)
def csa_form_pos_init(request: FormPOSInitRequest):
    """
    Equivalent of:
    csa_FormPOS_Init
    """
    try:
        if request.pos_store is None:
            return FormPOSInitResponse(
                return_value=1,
                error_message="Invalid Store"
            )
            
        if request.pos_file_date is None:
            return FormPOSInitResponse(
                return_value=1,
                error_message="Invalid Date"
            )

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # Check if POS row exists
                cur.execute("""
                    SELECT count(*)
                    FROM retail_history.pos
                    WHERE pos_store = %s AND pos_file_date = %s
                """, (request.pos_store, request.pos_file_date))
                
                count_record = cur.fetchone()
                if count_record and count_record[0] != 0:
                    # Update audit
                    cur.execute("""
                        INSERT INTO retail_history.audit
                        (audit_store, audit_date, audit_form_type, audit_update_flag, audit_timestamp, audit_user, audit_description)
                        VALUES (%s, %s, 21, 'U', CURRENT_TIMESTAMP, %s, 'POS Figures changed by user')
                    """, (request.pos_store, request.pos_file_date, request.user))

                    # Check POS original
                    cur.execute("""
                        SELECT count(*)
                        FROM retail_history.pos_original
                        WHERE pos_store = %s AND pos_file_date = %s
                    """, (request.pos_store, request.pos_file_date))

                    orig_count = cur.fetchone()
                    if not orig_count or orig_count[0] == 0:
                        cur.execute("""
                            INSERT INTO retail_history.pos_original
                            SELECT * FROM retail_history.pos
                            WHERE pos_store = %s AND pos_file_date = %s
                        """, (request.pos_store, request.pos_file_date))

                else:
                    # Insert audit
                    cur.execute("""
                        INSERT INTO retail_history.audit
                        (audit_store, audit_date, audit_form_type, audit_update_flag, audit_timestamp, audit_user, audit_description)
                        VALUES (%s, %s, 21, 'I', CURRENT_TIMESTAMP, %s, 'POS Figures manually entered by user')
                    """, (request.pos_store, request.pos_file_date, request.user))

                    # 135 zero values after tenant_id, store, date, flag
                    zeros = [0] * 135
                    # Insert into pos
                    cur.execute(f"""
                        INSERT INTO retail_history.pos
                        (tenant_id, pos_store, pos_file_date, pos_process_flag,
                         pos_current_reading, pos_previous_reading_prior_day, pos_previous_reading_prior_week,
                         pos_wtd_net_sales_rate_1, pos_wtd_net_sales_rate_2, pos_wtd_net_sales_rate_3, pos_wtd_net_sales_rate_4,
                         pos_wtd_voids_rate_1, pos_wtd_voids_rate_2, pos_wtd_voids_rate_3, pos_wtd_voids_rate_4,
                         pos_wtd_nt_refunds_rate_1, pos_wtd_nt_refunds_rate_2, pos_wtd_nt_refunds_rate_3, pos_wtd_nt_refunds_rate_4,
                         pos_wtd_refunds_rate_1, pos_wtd_refunds_rate_2, pos_wtd_refunds_rate_3, pos_wtd_refunds_rate_4,
                         pos_wtd_credits_rate_1, pos_wtd_credits_rate_2, pos_wtd_credits_rate_3, pos_wtd_credits_rate_4,
                         pos_wtd_bottle_deposits, pos_wtd_bottle_refunds, pos_wtd_store_coupons,
                         pos_wtd_grocery_sales, pos_wtd_grocery_voids_refunds, pos_wtd_meat_sales, pos_wtd_meat_voids_refunds,
                         pos_wtd_produce_sales, pos_wtd_produce_voids_refunds, pos_wtd_deli_bakery_sales, pos_wtd_deli_bakery_voids_refunds,
                         pos_wtd_florist_sales, pos_wtd_florist_voids_refunds, pos_wtd_seafood_sales, pos_wtd_seafood_voids_refunds,
                         pos_wtd_pharmacy_sales, pos_wtd_pharmacy_voids_refunds, pos_wtd_ff_dairy_sales, pos_wtd_ff_dairy_voids_refunds,
                         pos_wtd_hba_sales, pos_wtd_hba_voids_refunds, pos_wtd_sales_tax_collected_rate_1, pos_wtd_sales_tax_collected_rate_2,
                         pos_wtd_sales_tax_collected_rate_3, pos_wtd_sales_tax_collected_rate_4, pos_wtd_total_customer_count,
                         pos_wtd_grocery_customer_count, pos_wtd_meat_customer_count, pos_wtd_produce_customer_count,
                         pos_wtd_deli_customer_count, pos_wtd_florist_customer_count, pos_wtd_seafood_customer_count,
                         pos_wtd_pharmacy_customer_count, pos_wtd_ff_dairy_customer_count, pos_wtd_hba_customer_count, pos_wtd_item_count,
                         pos_wtd_nt_sales_rate_1, pos_wtd_nt_sales_rate_2, pos_wtd_nt_sales_rate_3, pos_wtd_nt_sales_rate_4,
                         pos_daily_net_sales_rate_1, pos_daily_net_sales_rate_2, pos_daily_net_sales_rate_3, pos_daily_net_sales_rate_4,
                         pos_daily_voids_rate_1, pos_daily_voids_rate_2, pos_daily_voids_rate_3, pos_daily_voids_rate_4,
                         pos_daily_nt_refunds_rate_1, pos_daily_nt_refunds_rate_2, pos_daily_nt_refunds_rate_3, pos_daily_nt_refunds_rate_4,
                         pos_daily_refunds_rate_1, pos_daily_refunds_rate_2, pos_daily_refunds_rate_3, pos_daily_refunds_rate_4,
                         pos_daily_credits_rate_1, pos_daily_credits_rate_2, pos_daily_credits_rate_3, pos_daily_credits_rate_4,
                         pos_daily_bottle_deposits, pos_daily_bottle_returns, pos_daily_store_coupons,
                         pos_daily_grocery_sales, pos_daily_grocery_voids_refunds, pos_daily_meat_sales, pos_daily_meat_voids_refunds,
                         pos_daily_produce_sales, pos_daily_produce_voids_refunds, pos_daily_deli_bakery_sales, pos_daily_deli_bakery_voids_refunds,
                         pos_daily_florist_sales, pos_daily_florist_voids_refunds, pos_daily_seafood_sales, pos_daily_seafood_voids_refunds,
                         pos_daily_pharmacy_sales, pos_daily_pharmacy_voids_refunds, pos_daily_ff_dairy_sales, pos_daily_ff_dairy_voids_refunds,
                         pos_daily_hba_sales, pos_daily_hba_voids_refunds, pos_daily_sales_tax_collected_rate_1, pos_daily_sales_tax_collected_rate_2,
                         pos_daily_sales_tax_collected_rate_3, pos_daily_sales_tax_collected_rate_4, pos_daily_total_customer_count,
                         pos_daily_grocery_customer_count, pos_daily_meat_customer_count, pos_daily_produce_customer_count,
                         pos_daily_deli_customer_count, pos_daily_florist_customer_count, pos_daily_seafood_customer_count,
                         pos_daily_pharmacy_customer_count, pos_daily_ff_dairy_customer_count, pos_daily_hba_customer_count, pos_daily_item_count,
                         pos_wtd_sushi_sales, pos_wtd_sushi_voids_refunds, pos_wtd_sushi_customer_count,
                         pos_wtd_fuel_sales, pos_wtd_fuel_voids_refunds, pos_wtd_fuel_customer_count,
                         pos_wtd_starbucks_sales, pos_wtd_starbucks_voids_refunds, pos_wtd_starbucks_customer_count,
                         pos_wtd_kitchen_ware_sales, pos_wtd_kitchen_ware_voids_refunds, pos_wtd_kitchen_ware_customer_count,
                         pos_wtd_dream_dinners_sales, pos_wtd_dream_dinners_voids_refunds, pos_wtd_dream_dinners_customer_count,
                         pos_daily_sushi_sales, pos_daily_sushi_voids_refunds, pos_daily_sushi_customer_count,
                         pos_daily_fuel_sales, pos_daily_fuel_voids_refunds, pos_daily_fuel_customer_count,
                         pos_daily_starbucks_sales, pos_daily_starbucks_voids_refunds, pos_daily_starbucks_customer_count,
                         pos_daily_kitchen_ware_sales, pos_daily_kitchen_ware_voids_refunds, pos_daily_kitchen_ware_customer_count,
                         pos_daily_dream_dinners_sales, pos_daily_dream_dinners_voids_refunds, pos_daily_dream_dinners_customer_count,
                         pos_wtd_void_transaction, pos_daily_void_transaction)
                        VALUES (%s, %s, %s, '1', {','.join(['%s']*135)})
                    """, (request.tenant_id, request.pos_store, request.pos_file_date, *zeros))

                    # Insert into pos_original
                    cur.execute(f"""
                        INSERT INTO retail_history.pos_original
                        (tenant_id, pos_store, pos_file_date, pos_process_flag,
                         pos_current_reading, pos_previous_reading_prior_day, pos_previous_reading_prior_week,
                         pos_wtd_net_sales_rate_1, pos_wtd_net_sales_rate_2, pos_wtd_net_sales_rate_3, pos_wtd_net_sales_rate_4,
                         pos_wtd_voids_rate_1, pos_wtd_voids_rate_2, pos_wtd_voids_rate_3, pos_wtd_voids_rate_4,
                         pos_wtd_nt_refunds_rate_1, pos_wtd_nt_refunds_rate_2, pos_wtd_nt_refunds_rate_3, pos_wtd_nt_refunds_rate_4,
                         pos_wtd_refunds_rate_1, pos_wtd_refunds_rate_2, pos_wtd_refunds_rate_3, pos_wtd_refunds_rate_4,
                         pos_wtd_credits_rate_1, pos_wtd_credits_rate_2, pos_wtd_credits_rate_3, pos_wtd_credits_rate_4,
                         pos_wtd_bottle_deposits, pos_wtd_bottle_refunds, pos_wtd_store_coupons,
                         pos_wtd_grocery_sales, pos_wtd_grocery_voids_refunds, pos_wtd_meat_sales, pos_wtd_meat_voids_refunds,
                         pos_wtd_produce_sales, pos_wtd_produce_voids_refunds, pos_wtd_deli_bakery_sales, pos_wtd_deli_bakery_voids_refunds,
                         pos_wtd_florist_sales, pos_wtd_florist_voids_refunds, pos_wtd_seafood_sales, pos_wtd_seafood_voids_refunds,
                         pos_wtd_pharmacy_sales, pos_wtd_pharmacy_voids_refunds, pos_wtd_ff_dairy_sales, pos_wtd_ff_dairy_voids_refunds,
                         pos_wtd_hba_sales, pos_wtd_hba_voids_refunds, pos_wtd_sales_tax_collected_rate_1, pos_wtd_sales_tax_collected_rate_2,
                         pos_wtd_sales_tax_collected_rate_3, pos_wtd_sales_tax_collected_rate_4, pos_wtd_total_customer_count,
                         pos_wtd_grocery_customer_count, pos_wtd_meat_customer_count, pos_wtd_produce_customer_count,
                         pos_wtd_deli_customer_count, pos_wtd_florist_customer_count, pos_wtd_seafood_customer_count,
                         pos_wtd_pharmacy_customer_count, pos_wtd_ff_dairy_customer_count, pos_wtd_hba_customer_count, pos_wtd_item_count,
                         pos_wtd_nt_sales_rate_1, pos_wtd_nt_sales_rate_2, pos_wtd_nt_sales_rate_3, pos_wtd_nt_sales_rate_4,
                         pos_daily_net_sales_rate_1, pos_daily_net_sales_rate_2, pos_daily_net_sales_rate_3, pos_daily_net_sales_rate_4,
                         pos_daily_voids_rate_1, pos_daily_voids_rate_2, pos_daily_voids_rate_3, pos_daily_voids_rate_4,
                         pos_daily_nt_refunds_rate_1, pos_daily_nt_refunds_rate_2, pos_daily_nt_refunds_rate_3, pos_daily_nt_refunds_rate_4,
                         pos_daily_refunds_rate_1, pos_daily_refunds_rate_2, pos_daily_refunds_rate_3, pos_daily_refunds_rate_4,
                         pos_daily_credits_rate_1, pos_daily_credits_rate_2, pos_daily_credits_rate_3, pos_daily_credits_rate_4,
                         pos_daily_bottle_deposits, pos_daily_bottle_returns, pos_daily_store_coupons,
                         pos_daily_grocery_sales, pos_daily_grocery_voids_refunds, pos_daily_meat_sales, pos_daily_meat_voids_refunds,
                         pos_daily_produce_sales, pos_daily_produce_voids_refunds, pos_daily_deli_bakery_sales, pos_daily_deli_bakery_voids_refunds,
                         pos_daily_florist_sales, pos_daily_florist_voids_refunds, pos_daily_seafood_sales, pos_daily_seafood_voids_refunds,
                         pos_daily_pharmacy_sales, pos_daily_pharmacy_voids_refunds, pos_daily_ff_dairy_sales, pos_daily_ff_dairy_voids_refunds,
                         pos_daily_hba_sales, pos_daily_hba_voids_refunds, pos_daily_sales_tax_collected_rate_1, pos_daily_sales_tax_collected_rate_2,
                         pos_daily_sales_tax_collected_rate_3, pos_daily_sales_tax_collected_rate_4, pos_daily_total_customer_count,
                         pos_daily_grocery_customer_count, pos_daily_meat_customer_count, pos_daily_produce_customer_count,
                         pos_daily_deli_customer_count, pos_daily_florist_customer_count, pos_daily_seafood_customer_count,
                         pos_daily_pharmacy_customer_count, pos_daily_ff_dairy_customer_count, pos_daily_hba_customer_count, pos_daily_item_count,
                         pos_wtd_sushi_sales, pos_wtd_sushi_voids_refunds, pos_wtd_sushi_customer_count,
                         pos_wtd_fuel_sales, pos_wtd_fuel_voids_refunds, pos_wtd_fuel_customer_count,
                         pos_wtd_starbucks_sales, pos_wtd_starbucks_voids_refunds, pos_wtd_starbucks_customer_count,
                         pos_wtd_kitchen_ware_sales, pos_wtd_kitchen_ware_voids_refunds, pos_wtd_kitchen_ware_customer_count,
                         pos_wtd_dream_dinners_sales, pos_wtd_dream_dinners_voids_refunds, pos_wtd_dream_dinners_customer_count,
                         pos_daily_sushi_sales, pos_daily_sushi_voids_refunds, pos_daily_sushi_customer_count,
                         pos_daily_fuel_sales, pos_daily_fuel_voids_refunds, pos_daily_fuel_customer_count,
                         pos_daily_starbucks_sales, pos_daily_starbucks_voids_refunds, pos_daily_starbucks_customer_count,
                         pos_daily_kitchen_ware_sales, pos_daily_kitchen_ware_voids_refunds, pos_daily_kitchen_ware_customer_count,
                         pos_daily_dream_dinners_sales, pos_daily_dream_dinners_voids_refunds, pos_daily_dream_dinners_customer_count,
                         pos_wtd_void_transaction, pos_daily_void_transaction)
                        VALUES (%s, %s, %s, '1', {','.join(['%s']*135)})
                    """, (request.tenant_id, request.pos_store, request.pos_file_date, *zeros))

            conn.commit()

        return FormPOSInitResponse(
            return_value=0,
            error_message=""
        )

    except Exception as ex:
        logger.exception("Error in FormPOS_Init")
        return FormPOSInitResponse(
            return_value=1,
            error_message="Init Form POS Failed"
        )
