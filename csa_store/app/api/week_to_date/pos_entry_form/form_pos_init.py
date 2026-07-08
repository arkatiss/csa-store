import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.pos_entry_form.form_pos_init_schema import FormPOSInitRequest, FormPOSInitResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/week_to_date/pos_entry_form",
    tags=["Week To Date POS Entry Form"]
)



def get_pos_insert_columns(cursor):
    """
    Returns all POS columns that need to be initialized to zero.
    Excludes the columns supplied separately or with defaults.
    """
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'retail_history'
          AND table_name = 'pos'
          AND column_name NOT IN (
                'tenant_id',
                'pos_store',
                'pos_file_date',
                'pos_process_flag',
                'created_by',
                'creation_date',
                'last_updated_by',
                'last_update_date'
          )
        ORDER BY ordinal_position
    """)

    return [row[0] for row in cursor.fetchall()]

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
                        (tenant_id, a_store, a_date, a_form_type, a_action, a_creation_date, a_user, a_comment)
                        VALUES (%s, %s, %s, 21, 'U', CURRENT_TIMESTAMP, %s, 'POS Figures changed by user')
                    """, (str(request.tenant_id), request.pos_store, request.pos_file_date, request.user))

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
                        (tenant_id, a_store, a_date, a_form_type, a_action, a_creation_date, a_user, a_comment)
                        VALUES (%s, %s, %s, 21, 'I', CURRENT_TIMESTAMP, %s, 'POS Figures manually entered by user')
                    """, (str(request.tenant_id), request.pos_store, request.pos_file_date, request.user))

                    # 135 zero values after tenant_id, store, date, flag
                    zeros = [0] * 147
                    columns = get_pos_insert_columns(cur)
                    zeros = [0] * len(columns)
                    # Insert into pos
                    cur.execute(f"""
                        INSERT INTO retail_history.pos
                        (tenant_id, pos_store, pos_file_date, pos_process_flag, {",".join(columns)})
                        VALUES (%s, %s, %s, '1', {",".join(["%s"] * len(columns))})
                    """, (str(request.tenant_id), request.pos_store, request.pos_file_date, *zeros))

                    # Insert into pos_original
                    cur.execute(f"""
                        INSERT INTO retail_history.pos_original
                        (tenant_id, pos_store, pos_file_date, pos_process_flag, {",".join(columns)})
                        VALUES (%s, %s, %s, '1', {",".join(["%s"] * len(columns))})
                    """, (str(request.tenant_id), request.pos_store, request.pos_file_date, *zeros))

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
