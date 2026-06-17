import os

from psycopg2.pool import ThreadedConnectionPool

from dotenv import load_dotenv

load_dotenv()

connection_pool = ThreadedConnectionPool(
    minconn=5,
    maxconn=20,
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
