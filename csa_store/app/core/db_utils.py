import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class DBConnection:
    '''
    PostgreSQL connection wrapper.
    Usage:
        with DBConnection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    '''

    def __init__(self):
        self.conn = None

    def __enter__(self):
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type:
                self.conn.rollback()
            else:
                self.conn.commit()
            self.conn.close()
