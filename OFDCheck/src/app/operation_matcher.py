from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Any
from decimal import Decimal
from src.audit.db_activity_log import DbActivityLog

class OperationMatcher:
    # Сопоставляет операции из БД и файла по:
    #   - точному совпадению суммы (с допуском float)
    #   - дате и времени  ±30 минут

    # Результат: список кортежей
    #   (dt_db, id_op_db, amount_db, dt_file, amount_file, kassa_file, result)


    def __init__(self, time_window_minutes: int = 30):
        self.time_window = timedelta(minutes=time_window_minutes)
        self.activity_log = DbActivityLog()

        # Индексы полей из БД
        self.idx_db_id_operation    = 0
        self.idx_db_dt              = 1
        self.idx_db_id_represent    = 2
        self.idx_db_type            = 3
        self.idx_db_amount          = 4
        self.idx_db_inv_number      = 5

        # Индексы полей из файла
        self.idx_file_dt = 0
        self.idx_file_amount = 1
        self.idx_file_type = 2
        self.idx_file_fd_num = 3

    @staticmethod
    def _parse_dt(dt_value: Any) -> Optional[datetime]:
        if isinstance(dt_value, datetime):
            return dt_value
        if not isinstance(dt_value, str):
            return None
        try:
            return datetime.strptime(dt_value.strip(), "%d.%m.%Y %H:%M")
        except ValueError:
            return None

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        # Преобразует значение в float.
        if value is None:
            return None

        if isinstance(value, Decimal):
            return float(value)

        s = str(value).replace(",", ".").strip()
        try:
            return float(s)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _amounts_match(a: Optional[float], b: Optional[float]) -> bool:
        if a is None or b is None:
            return False
        return abs(a - b) < 1e-6

    @staticmethod
    def _normalize_input(data: Optional[List[Tuple]]) -> List[Tuple]:
        # Если на вход пришёл None — возвращаем пустой список.
        if data is None:
            return []
        return data

    def match(
        self,
        db_rows: Optional[List[Tuple]],
        file_rows: Optional[List[Tuple]],
        id_represent,
        user
    ) -> List[Tuple]:
        # Основной метод: возвращает объединённый список кортежей с полем result.

        # Нормализуем входные данные: None -> пустой список
        db_rows = self._normalize_input(db_rows)
        file_rows = self._normalize_input(file_rows)

        # Нормализуем данные файла: парсим даты, суммы, сохраняем исходную строку
        file_parsed = []
        for row in file_rows:
            # Защита на случай, если в списке попадётся None вместо кортежа
            if not row:
                continue

            dt = self._parse_dt(row[self.idx_file_dt])
            amount = self._to_float(row[self.idx_file_amount])
            # kassa = row[self.idx_file_kassa]

            if dt is None or amount is None:
                # Пропускаем строки с невалидными датой/суммой
                continue

            file_parsed.append({
                "dt": dt,
                "amount": amount,
                "row": row,
                "matched": False
            })

        result = []

        # Проходим по каждой записи из БД
        for db_row in db_rows:
            if not db_row:
                # Если в списке БД попался None/пустой кортеж — считаем как «Ошибка»
                result.append((None, None, None, None, None, None, None, None, "Ошибка"))
                continue

            db_id_operation= db_row[self.idx_db_id_operation]
            db_dt = self._parse_dt(db_row[self.idx_db_dt])
            db_id_represent= db_row[self.idx_db_id_represent]
            db_type= db_row[self.idx_db_type]
            db_amount = self._to_float(db_row[self.idx_db_amount])
            db_inv_number= db_row[self.idx_db_inv_number]

            # Если в БД невалидные данные — всё равно добавляем как «Ошибка»
            if db_dt is None or db_amount is None:
                result.append((
                    db_id_operation,
                    db_dt,
                    db_amount,
                    db_type,
                    None,
                    None,
                    None,
                    None,
                    "Ошибка"
                ))
                continue

            lower = db_dt - self.time_window
            upper = db_dt + self.time_window

            matched_file = None
            for f in file_parsed:
                if f["matched"]:
                    continue
                if not self._amounts_match(db_amount, f["amount"]):
                    continue
                if lower <= f["dt"] <= upper:
                    matched_file = f
                    f["matched"] = True
                    break

            if matched_file:
                f_row = matched_file["row"]
                result.append((
                    db_id_operation,
                    db_dt,
                    db_amount,
                    db_type,
                    matched_file["dt"],
                    matched_file["amount"],
                    f_row[self.idx_file_type],
                    f_row[self.idx_file_fd_num],
                    "Успешно"
                ))
            else:
                # Пары нет — запись только из БД
                result.append((
                    db_id_operation,
                    db_dt,
                    db_amount,
                    db_type,
                    None,
                    None,
                    None,
                    None,
                    "Ошибка"
                ))

        # Добавляем записи из файла, которые так и не нашли пару (только файл)
        for f in file_parsed:
            if not f["matched"]:
                f_row = f["row"]
                result.append((
                    None,
                    None,
                    None,
                    None,
                    f["dt"],
                    f["amount"],
                    f_row[self.idx_file_type],
                    f_row[self.idx_file_fd_num],
                    "Ошибка"
                ))

        # запись лога
        self.activity_log.log(
                user_id=user["id"],
                action="Выполнена сверка",
                represent_id=id_represent
            )

        return result



