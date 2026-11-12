import pyodbc
from src.db.connection import get_db_connection

class RepresentRepository:
    # Список представителей

    def __init__(self):
        self.conn = get_db_connection()

    def get_all(self):
        try:
            query = """
                SELECT id_represent, [name]
                FROM dbo.represents
                ORDER BY [name]
            """
            cursor = self.conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            self.conn.close()
            return rows
        except Exception as e:
            self.activity_log.log(
                action="Ошибка получения списка представителей! " + str(e),
            )


