import csv
import tkinter as tk
from tkinter import messagebox
from src.audit.db_activity_log import DbActivityLog
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Импорт из файла CSV в формате OFD.ru
class LoadCsvOFD:
    @staticmethod
    def detect_encoding(file_path: str):
        # Пытается угадать кодировку: сначала utf-8, потом cp1251.
        encodings_to_try = ["utf-8", "cp1251"]
        for enc in encodings_to_try:
            try:
                with open(file_path, "r", encoding=enc, newline="") as f:
                    f.read(1024)  
                return enc
            except UnicodeDecodeError:
                continue
        return None

    @staticmethod
    def detect_delimiter(file_path: str, encoding: str):
        # Определяет разделитель
        with open(file_path, "r", encoding=encoding, newline="") as f:
            sample = f.read(4096)

        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(sample)
            return dialect.delimiter
        except csv.Error:
            if ";" in sample and "\n" in sample:
                return ";"
            return ","

    @classmethod
    def load(cls, file_path: str, user, id_represent):
        # Определяем кодировку и разделитель
        encoding = cls.detect_encoding(file_path)
        if encoding is None:
            messagebox.showerror("Ошибка", "Не удалось определить кодировку файла. Попробуйте сохранить CSV в UTF-8.")
            return None

        delimiter = cls.detect_delimiter(file_path, encoding)

        try:
            with open(file_path, "r", encoding=encoding, newline="") as f:
                reader = csv.reader(f, delimiter=delimiter)
                rows = list(reader)
                
            if not rows:
                messagebox.showwarning("Внимание", "Файл пустой.")
                return None

            # Пропускаем заголовок
            data_rows = rows[1:]
            if not data_rows:
                messagebox.showwarning("Внимание", "В файле есть только заголовок, данных нет.")
                return None

            # Преобразуем и фильтруем данные под требования ВКР
            transformed = cls._transform_cash_receipts(data_rows)

            activity_log = DbActivityLog()
            activity_log.log(
                user_id=user["id"],
                action=f"Загружен файл: {Path(file_path).name}, строк данных (кассовые чеки): {len(transformed)}",
                represent_id=id_represent
            )

            return transformed
        except Exception as e:
            messagebox.showerror("Ошибка чтения файла", str(e))
            return None

    @staticmethod
    def _transform_cash_receipts(raw_rows: list) -> list:
        
        # Преобразует сырые строки CSV в формат для OperationMatcher:
        #   - Фильтрует по колонке 13 == 'Кассовый чек'
        #   - Объединяет колонку 10 (дата) и 11 (время) в datetime
        #   - Берёт: 9 (номер ФД), 15 (номер чека), 16 (тип операции), 17 (сумма)
        #   - Возвращает список кортежей: (dt, amount, kassa_number)
        #     где kassa_number = номер ФД (колонка 9) — под твой matcher
        
        result = []

        for i, row in enumerate(raw_rows):
            # Защита от слишком коротких строк
            if len(row) < 18:
                continue

            # Фильтр: колонка 13 должна быть 'Кассовый чек'
            if row[13] != "Кассовый чек":
                continue

            fd_number = row[9]              # номер ФД
            date_str = row[10].strip()      # дата (10)
            time_str = row[11].strip()      # время (11)
            check_number = row[15]          # номер чека (15)
            op_type = row[16]               # тип операции (16)
            amount_str = row[17].strip()    # сумма (17)

            # Объединение даты и времени
            dt_str = f"{date_str} {time_str}"
            try:
                dt = datetime.strptime(dt_str, "%d.%m.%Y %H:%M:%S")
            except ValueError:
                # Если формат не совпадает — пробуем без секунд (если время без секунд)
                try:
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    # Строка не парсится — пропускаем
                    continue

            # Парсинг суммы: убираем пробелы, заменяем запятую на точку
            clean_amount = amount_str.replace(" ", "").replace(",", ".")
            try:
                amount = float(Decimal(clean_amount))
            except (ValueError, InvalidOperation):
                continue

            # Для твоего OperationMatcher нужен формат (dt, amount, kassa)
            # В качестве kassa передаём номер ФД — это уникальный идентификатор кассы/чека
            result.append((dt, amount, op_type, fd_number))

        return result            