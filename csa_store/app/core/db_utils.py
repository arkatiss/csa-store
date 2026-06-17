from app.core.db_pool import connection_pool


class DBConnection:
    '''
    PostgreSQL connection wrapper.
    Usage:
        with DBConnection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    '''

    def __enter__(self):

        self.conn = connection_pool.getconn()

        print("Connection acquired")

        return self.conn

    def __exit__(
            self,
            exc_type,
            exc_val,
            exc_tb):

        try:

            if exc_type:

                self.conn.rollback()

            else:

                self.conn.commit()

        finally:

            connection_pool.putconn(self.conn)

            print("Connection returned")
