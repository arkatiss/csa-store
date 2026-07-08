import logging
from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.week_to_date.form97_net_sales.wtd_net_sales_update_schema import (
    WTDNetSalesUpdateRequest,
    WTDNetSalesUpdateResponse,
)

from app.utils.week_to_date.form97_wtd_net_sales_update_helper import (
    check_wtd_net_sales_exists,
    update_daily_sales_cash_total,
    insert_audit_record,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/week_to_date/form97_net_sales",
    tags=["Week To Date Form 97 Net Sales"]
)


@router.put("/update", response_model=WTDNetSalesUpdateResponse)
def csa_wtd_net_sales_update(request: WTDNetSalesUpdateRequest):

    try:

        # -----------------------------
        # Validations
        # -----------------------------

        if request.wns_store is None:
            return WTDNetSalesUpdateResponse(
                return_value=1,
                error_message="Invalid Store"
            )

        if request.wns_week_ending_date is None:
            return WTDNetSalesUpdateResponse(
                return_value=1,
                error_message="Invalid Week Ending Date"
            )

        if not request.user or request.user.strip() == "":
            return WTDNetSalesUpdateResponse(
                return_value=1,
                error_message="Invalid User"
            )

        if (
            request.wns_deposit_cancels is None and
            request.wns_other_sales is None and
            (
                request.wns_other_sales_description is None or
                request.wns_other_sales_description.strip() == ""
            )
        ):
            return WTDNetSalesUpdateResponse(
                return_value=1,
                error_message="No Updateable Attributes Received"
            )

        with DBConnection() as conn:
            with conn.cursor() as cur:

                # -----------------------------
                # Row Exists
                # -----------------------------

                if not check_wtd_net_sales_exists(
                    cur,
                    request.wns_store,
                    request.wns_week_ending_date,
                ):
                    return WTDNetSalesUpdateResponse(
                        return_value=1,
                        error_message="Row Not Found"
                    )

                # -----------------------------
                # Fetch Old Values
                # -----------------------------

                cur.execute(
                    """
                    SELECT
                        wns_deposit_cancels,
                        wns_other_sales,
                        wns_other_sales_description
                    FROM retail_accounting.wtd_net_sales
                    WHERE
                        wns_store=%s
                    AND
                        wns_week_ending_date=%s
                    """,
                    (
                        request.wns_store,
                        request.wns_week_ending_date,
                    ),
                )

                row = cur.fetchone()

                old_deposit = row[0]
                old_other_sales = row[1]
                old_description = row[2]

                # -----------------------------
                # No Updates Detected
                # -----------------------------

                if (
                    old_deposit == request.wns_deposit_cancels and
                    old_other_sales == request.wns_other_sales and
                    old_description == request.wns_other_sales_description
                ):
                    return WTDNetSalesUpdateResponse(
                        return_value=1,
                        error_message="No Updates Detected"
                    )

                # -----------------------------
                # Update Net Sales
                # -----------------------------

                try:

                    cur.execute(
                        """
                        UPDATE retail_accounting.wtd_net_sales
                        SET
                            wns_deposit_cancels=%s,
                            wns_other_sales=%s,
                            wns_other_sales_description=%s,
                            updated_at=NOW(),
                            updated_by=%s
                        WHERE
                            wns_store=%s
                        AND
                            wns_week_ending_date=%s
                        """,
                        (
                            request.wns_deposit_cancels,
                            request.wns_other_sales,
                            request.wns_other_sales_description,
                            request.user,
                            request.wns_store,
                            request.wns_week_ending_date,
                        ),
                    )

                    # Update Daily Sales Cash Total
                    update_daily_sales_cash_total(
                        cur,
                        request.wns_store,
                        request.wns_week_ending_date,
                    )

                except Exception:

                    conn.rollback()

                    logger.exception("Update Failed")

                    return WTDNetSalesUpdateResponse(
                        return_value=1,
                        error_message="Update Failed"
                    )

                # -----------------------------
                # Audit
                # -----------------------------

                if old_deposit != request.wns_deposit_cancels:

                    insert_audit_record(
                        cur,
                        request.tenant_id,
                        request.wns_store,
                        request.wns_week_ending_date,
                        request.user,
                        f"Deposit Cancels Changed From - {old_deposit} To - {request.wns_deposit_cancels}"
                    )

                if old_other_sales != request.wns_other_sales:

                    insert_audit_record(
                        cur,
                        request.tenant_id,
                        request.wns_store,
                        request.wns_week_ending_date,
                        request.user,
                        f"Other Sales Changed From - {old_other_sales} To - {request.wns_other_sales}"
                    )

                if old_description != request.wns_other_sales_description:

                    if old_description is None:

                        comment = (
                            f"Other Sales Description Changed From - Blank To - "
                            f"{request.wns_other_sales_description}"
                        )

                    else:

                        comment = (
                            f"Other Sales Description Changed From - "
                            f"{old_description} To - "
                            f"{request.wns_other_sales_description}"
                        )

                    insert_audit_record(
                        cur,
                        request.tenant_id,
                        request.wns_store,
                        request.wns_week_ending_date,
                        request.user,
                        comment,
                    )

                conn.commit()

                return WTDNetSalesUpdateResponse(
                    return_value=0,
                    error_message=""
                )

    except Exception:

        logger.exception("Unexpected Error")

        return WTDNetSalesUpdateResponse(
            return_value=1,
            error_message="Update Failed"
        )