import pyodbc
from src.db.connection import get_db_connection
from src.audit.db_activity_log import DbActivityLog

class OperationRepository:
    # Данные об операциях из MS SQL 

    COLUMNS = [
        "id_operation", 
        "dt", 
        "id_represent",
        "type", 
        "amount", 
        "inv_number"
    ]

    def __init__(self):
        self.conn = get_db_connection()
        self.activity_log = DbActivityLog()

    def load_data(self, dt, id_represent, user) -> list:
        # :param dt: datetime — дата операции 
        # :param id_represent: int — идентификатор представителя
        # :return: список кортежей строк таблицы
        try:
            query = """
                SELECT 
                     id_operation
                    ,dt
                    ,id_represent
                    ,[type]
                    ,amount
                    ,inv_number
                FROM dbo.operations
                WHERE cast(dt as date) = ?
                AND id_represent = ?
                ORDER BY dt
            """
            cursor = self.conn.cursor()
            cursor.execute(query, (dt, id_represent))
            rows = cursor.fetchall()
            self.conn.close()
            # логируем
            self.activity_log.log(
                user_id=user["id"],
                action="Запрошены данные об операциях за " + dt.strftime("%d.%m.%Y"),
                represent_id=id_represent
            )

            return rows
        except Exception as e:
            self.activity_log.log(
                user_id=user["id"],
                action="Системная ошибка! " + str(e),
                represent_id=id_represent
            )

