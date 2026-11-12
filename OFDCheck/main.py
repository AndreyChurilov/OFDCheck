import pyodbc
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk, filedialog
from datetime import datetime
from pathlib import Path
import json
from src.db.connection import get_db_connection
from src.app.login_window import LoginWindow
from src.utils.icon_utils import set_icon
from src.app.operation_repository import OperationRepository
from src.app.represent_repository import RepresentRepository
from src.app.load_csv import LoadCsvOFD
from src.app.operation_matcher import OperationMatcher
from src.utils.export_csv import CsvExporter


app = LoginWindow()
user = app.run()

# константы
CNT_COL_TOTAL = 10
CNT_COL_CONTROL = 5
NUM_ROW_GRID = 3
CNT_GRID_COL = 9
# начальные значения
file_name = ''
matcher = OperationMatcher(time_window_minutes=30)
db_data = None
file_data = None
id_represent = 0

# Получить данные из БД
def load_operations(repr_dic):
    global db_data
    global id_represent
    # Получить дату
    date_str = entry_dt.get().strip()
    try:
        dt = datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ДД.ММ.ГГГГ")
        return 
    # Получить представителя
    selected_name = combo.get()
    id_represent = repr_dic.get(selected_name)
    if id_represent == None: 
        messagebox.showerror("Ошибка", "Выберите представителя")
        return
    # Получение данных
    oper_repo = OperationRepository()
    db_data = oper_repo.load_data(dt, id_represent, user)
    refresh()

# Выбор файла
def get_file():
    global file_name
    filepath = filedialog.askopenfilename(
        title="Выберите файл",
        filetypes=[
            ("CSV", "*.csv"),
            ("Excel", "*.xlsx"),
            ("Все файлы", "*.*"),
        ]
    )
    if not filepath:
        return  # пользователь нажал «Отмена»
    file_name = filepath
    lbl_path.config(text=f"Выбран: {Path(filepath).name}")

# загрузка файла
def load_file(filepath: str):
    global file_data
    global id_represent

    if not filepath: #файл не выбран
        messagebox.showerror("Ошибка", "Файл не выбран")
        return

    file_data = LoadCsvOFD().load(filepath, user, id_represent)
    refresh()

# обновить
def refresh():
    global db_data
    global file_data
    global id_represent
    # фильтр
    selected = report_type.get()
    # сопоставление
    combined = matcher.match(db_data, file_data, id_represent, user)
    # вывод с предочисткой старых данных
    clear()
    display_rows = prepare_rows_for_treeview(combined)
    error_count = 0
    total_count = 0
    for i, row in enumerate(display_rows):
        is_status_ok = row[8] == "Успешно"
        tag = "success" if is_status_ok else "error"
        # обработка фильтра
        if (selected == "report_diff") and is_status_ok:
            continue
        # счетчик строк 
        total_count += 1
        if (not is_status_ok): error_count += 1 
        # вывод в таблицу
        tree.insert("", "end", values=row, tags=(tag,))   
    # статистика   
    lbl_status.config(text=f"Всего строк: {total_count} | С ошибками: {error_count}")

def prepare_rows_for_treeview(raw_rows):
    # Обработка строк для вывода в Treeview.
    prepared = []
    for row in raw_rows:
        new_row = []
        for value in row:
            if value is None:
                new_row.append("")
            elif isinstance(value, datetime):
                new_row.append(value.strftime("%d.%m.%Y %H:%M"))
            elif isinstance(value, (int, float)):
                # Форматируем числа: 2 знака после запятой
                new_row.append(f"{value:.2f}".rstrip('0').rstrip('.'))
            else:
                new_row.append(str(value))
        prepared.append(tuple(new_row))
    return prepared

# Очистить
def clear():
    for item in tree.get_children():
        tree.delete(item)
    lbl_status.config(text="Всего строк: 0 | С ошибками: 0") 

# Экспорт в Excel
def export_excel():
    print("Экспорт в Excel")

# Создание главного окна
root = tk.Tk()
root.title("Программа сверки онлайн-платежей: " + user['name'])
root.geometry("900x600")
set_icon(root)
root.resizable(True, True)  # Разрешаем менять размер окна

# центрируем
root.update_idletasks()
w, h = root.winfo_width(), root.winfo_height()
root.geometry(f"+{(root.winfo_screenwidth()-w)//2}+{(root.winfo_screenheight()-h)//2}")

style = ttk.Style()
try:
    style.theme_use('xpnative')
except tk.TclError:
    style.theme_use('default')


# Веса для колонок
for c in range(0,CNT_COL_CONTROL + 1):
    root.columnconfigure(c, weight=0)
for c in range(CNT_COL_CONTROL,CNT_COL_TOTAL):
    root.columnconfigure(c, weight=1) 

# +++++++++++++++++++++ КОНТРОЛЫ +++++++++++++++++++++
# Дата, представитель + Загрузить
tk.Label(root, text="Дата:").grid(row=0, column=0, sticky="e", padx=10, pady=(10,0))
entry_dt = tk.Entry(root, width=20)
entry_dt.grid(row=0, column=1, pady=(10,0))

# today_str = datetime.now().strftime("%d.%m.%Y")
entry_dt.insert(0, "02.11.2026")

# Список представителей
tk.Label(root, text="Представитель:").grid(row=0, column=2, sticky="e", padx=10, pady=(10,0))
repr_list = RepresentRepository().get_all()
combo = ttk.Combobox(root, values=[row[1] for row in repr_list], state="readonly", width=30)  
repr_dic = {name: rid for rid, name in repr_list} # сохраняем соответствие id и name в словаре
combo.set("Выберите представителя")  # значение по умолчанию
combo.grid(row=0, column=3, pady=(10,0))

style.configure('Wide.TButton', font=('Segoe UI', 10))
btn_load_db = ttk.Button(
    root,
    text="Загрузить",
    command = lambda: load_operations(repr_dic=repr_dic),
    style='Wide.TButton'
)
btn_load_db.grid(row=0, column=4, pady=(10,0), padx=10, sticky="ew")

# Выбор файла + Загрузить
lbl_path = ttk.Label(root, text="Файл не выбран")
lbl_path.grid(row=1, column=0, columnspan=3, sticky="w", padx=10, pady=(10,0))

btn_path = ttk.Button(
    root,
    text="Выбрать файл...",
    command=get_file,
    style='Wide.TButton'
)
btn_path.grid(row=1, column=3, pady=(10,0), padx=0, sticky="e")

btn_load_file = ttk.Button(
    root,
    text="Загрузить",
    command = lambda: load_file(filepath= file_name),
    style='Wide.TButton'
)
btn_load_file.grid(row=1, column=4, pady=(10,0), padx=10, sticky="ew")

# Фильтр + Обновить
report_type = tk.StringVar(value="report_all")

rb_all = tk.Radiobutton(
    root,
    text="Все данные",
    variable=report_type,
    value="report_all",
    indicatoron=True,         
    anchor="w"              
)
rb_all.grid(row=2, column=0, pady=(10,0), padx=10)

rb_diff = tk.Radiobutton(
    root,
    text="Только различия",
    variable=report_type,
    value="report_diff",
    anchor="w"
)
rb_diff.grid(row=2, column=1, pady=(10,0), padx=10)

btn_refresh = ttk.Button(
    root,
    text="Обновить",
    command=refresh,
    style='Wide.TButton'
)
btn_refresh.grid(row=2, column=2, pady=(10,0), padx=10, sticky="ew")

btn_clear = ttk.Button(
    root,
    text="Очистить",
    command=clear,
    style='Wide.TButton'
)
btn_clear.grid(row=2, column=3, pady=(10,0), padx=0, sticky="w")

btn_export_excel = ttk.Button(
    root,
    text="Экспорт  в  CSV",
    command=lambda: CsvExporter.export(tree, user),
    style='Wide.TButton'
)
btn_export_excel.grid(row=2, column=3, pady=(10,0), padx=0, sticky="e")
# статистика
lbl_status = tk.Label(root, text="Всего строк: 0 | С ошибками: 0", anchor="e")
lbl_status.grid(row=2, column=CNT_COL_TOTAL - 1, sticky="e", padx=20, pady=(10,0))

# +++++++++++++++++++++ ТАБЛИЦА +++++++++++++++++++++
frm = ttk.Frame(root, padding=10)
frm.grid(row=NUM_ROW_GRID, column=0, columnspan=CNT_COL_TOTAL, sticky="nsew")
root.rowconfigure(NUM_ROW_GRID, weight=1)

# Колонки таблицы
columns = ["id", "date1", "sum1", "type1", "date2", "sum2", "type2", "fd", "status"]

sub_headers = ["ID операции", "Дата и время", "Сумма", "Тип",
               "Дата и время", "Сумма", "Тип", "ФД №", "Статус сверки"]

widths = {
    "id": 90, "date1": 140, "sum1": 80, "type1": 80,
    "date2": 140, "sum2": 80, "type2": 80, "fd": 70,
    "status": 120,
}

# Верхний уровень шапки
frm_head = ttk.Frame(frm)
frm_head.columnconfigure(0, weight=0,
                         minsize=widths["id"] + widths["date1"] + widths["sum1"] + widths["type1"])
frm_head.columnconfigure(1, weight=0,
                         minsize=widths["date2"] + widths["sum2"] + widths["type2"] + widths["fd"])
frm_head.columnconfigure(2, weight=0, minsize=widths["status"])

style.configure("Header.TLabel", font=("Segoe UI", 10, "bold"), anchor="center")

ttk.Label(frm_head, text="Данные из программы", style="Header.TLabel",
          relief="solid", borderwidth=1).grid(row=0, column=0, sticky="nsew")
ttk.Label(frm_head, text="Данные из ОФД", style="Header.TLabel",
          relief="solid", borderwidth=1).grid(row=0, column=1, sticky="nsew")
ttk.Label(frm_head, text="Результат", style="Header.TLabel",
          relief="solid", borderwidth=1).grid(row=0, column=2, sticky="nsew")

# Treeview
tree = ttk.Treeview(frm, columns=columns, show="headings", height=15)

for col, header in zip(columns, sub_headers):
    tree.column(col, width=widths[col], anchor="center", stretch=False)
    tree.heading(col, text=header)

# Шаблоны цветов строк
tree.tag_configure("success", background="#DCF4D3")
tree.tag_configure("error", background="#F4D8D3")

style.map("Treeview",
          background=[("selected", "#cfe3f5")],
          foreground=[("selected", "#1a2a3a")])

# Прокрутка Y
v_scroll = ttk.Scrollbar(frm, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=v_scroll.set)

# Размещение: шапка сверху, таблица, полоса прокрутки ниже
frm_head.grid(row=0, column=0, sticky="ew")
tree.grid(row=1, column=0, sticky="nsew")
v_scroll.grid(row=1, column=1, sticky="ns")

frm.columnconfigure(0, weight=1)  
frm.columnconfigure(1, weight=0)  
frm.rowconfigure(1, weight=1)   

# Запуск главного цикла событий
root.mainloop()
