import csv
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional
from src.audit.db_activity_log import DbActivityLog
from pathlib import Path

class CsvExporter:
    @staticmethod
    def export(tree: tk.ttk.Treeview, user, filename: Optional[str] = None) -> bool:
        columns = list(tree["columns"])
        headings = [tree.heading(col)["text"] for col in columns]

        if filename is None:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")],
                title="Сохранить отчёт в CSV (ANSI/cp1251)"
            )
            if not filename:
                return False

        try:
            # encoding='cp1251' ANSI для русской локали Windows
            with open(filename, "w", newline="", encoding="cp1251") as f:
                f.write("sep=;\n")

                writer = csv.writer(f, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(headings)

                for item_id in tree.get_children():
                    values = tree.item(item_id)["values"]
                    writer.writerow(values)

            messagebox.showinfo("Успех", f"Данные успешно сохранены (кодировка cp1251):\n{filename}")
            # логирование
            activity_log = DbActivityLog()
            activity_log.log(
                user_id=user["id"],
                action=f"Данные сверки выгружены в файл: {Path(filename).name}",
            )

            return True

        except PermissionError:
            messagebox.showerror("Ошибка доступа", "Файл открыт в другой программе. Закройте его и попробуйте снова.")
            return False
        except UnicodeEncodeError as e:
            # Если в данных есть символы, которых нет в cp1251 (например, «ё», тире, эмодзи)
            messagebox.showerror(
                "Ошибка кодировки",
                f"В данных найдены символы, которые нельзя сохранить в кодировке cp1251.\n"
                f"Рекомендуется использовать UTF‑8.\nОшибка: {e}"
            )
            return False
        except Exception as e:
            messagebox.showerror("Ошибка экспорта", str(e))
            return False
