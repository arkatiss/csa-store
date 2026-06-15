from fastapi import APIRouter
from app.core.db_utils import DBConnection

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
def health_check():
    try:
        with DBConnection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
        return {"status": "UP", "db": result[0]}
    except Exception as ex:
        return {"status": "DOWN", "error": str(ex)}
