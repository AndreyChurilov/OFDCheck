import pyodbc
from typing import Optional
from src.db.connection import get_db_connection
import socket

class DbActivityLog:
    # Логирование действий пользователя

    def log(
        self,
        user_id: Optional[int] = None,
        action: str = "",
        represent_id: Optional[int] = None,
    ) -> bool:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            host_name = socket.gethostname()

            cursor.execute(
                "insert into dbo.activity_log (host_name, id_user, action, id_represent) values(?,?,?,?)",
                (host_name,user_id,action,represent_id)
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"[AUDIT ERROR] Не удалось записать лог: {e}")
            return False