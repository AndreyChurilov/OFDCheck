import pyodbc
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from src.db.connection import get_db_connection
from src.utils.auth_utils import hash_password, verify_password
from src.utils.icon_utils import set_icon
from src.audit.db_activity_log import DbActivityLog

# Авторизация
class LoginWindow:
    def __init__(self):
        # форма
        self.root = tk.Tk()
        self.activity_log = DbActivityLog()

        style = ttk.Style()
        try:
            style.theme_use('xpnative')
        except tk.TclError:
            style.theme_use('default')

        self.root.title("Авторизация")
        self.root.geometry("270x105")
        self.root.resizable(False, False)
        set_icon(self.root)
        # центрируем
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        self.root.geometry(f"+{(self.root.winfo_screenwidth()-w)//2}+{(self.root.winfo_screenheight()-h)//2}")

        # контролы
        tk.Label(self.root, text="Логин:").grid(row=0, column=0, sticky="e", padx=10, pady=(10,0))
        self.entry_login = tk.Entry(self.root, width=30)
        self.entry_login.grid(row=0, column=1, pady=(10,0))

        tk.Label(self.root, text="Пароль:").grid(row=1, column=0, sticky="e", padx=10, pady=5)
        self.entry_password = tk.Entry(self.root, show="*", width=30)
        self.entry_password.grid(row=1, column=1, pady=5)

        style.configure('Wide.TButton', font=('Segoe UI', 10))
        btn_login = ttk.Button(
            self.root,
            text="Войти",
            command=self.validate_login,
            style='Wide.TButton'
        )
        btn_login.grid(row=2, column=0, columnspan=2, pady=5, padx=(15,0), sticky="ew")

        self.user_data = None

    def validate_login(self):
        login = self.entry_login.get().strip()
        password = self.entry_password.get().strip()

        if not login or not password:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Получаем только хеш по логину
            cursor.execute(
                "SELECT id_user, full_name, login, psw_hash FROM dbo.users WHERE login = ?",
                (login,)
            )
            row = cursor.fetchone()
            conn.close()

            if not row:
                # Ошибка
                self.activity_log.log(
                    action="Ошибка: Неверный логин или пароль! Логин: " + login + " Пароль:" + password
                )
                messagebox.showerror("Ошибка", "Неверный логин или пароль")
                return

            user_id, full_name, login, stored_hash = row

            if verify_password(password, stored_hash):
                # Успех
                self.user_data = {
                    "id": user_id,
                    "name": full_name,
                    "login": login
                }
                self.activity_log.log(
                    action="Успешный вход"
                    ,user_id = user_id
                )
                self.root.destroy()
            else:
                # Ошибка
                self.activity_log.log(
                    action="Ошибка: Неверный логин или пароль! Логин: " + login + " Пароль:" + password
                )
                messagebox.showerror("Ошибка", "Неверный логин или пароль")

        except Exception as e:
            self.activity_log.log(
                action="Системная ошибка! " + str(e)
            )
            messagebox.showerror("Системная ошибка", str(e))

    def run(self):
        def on_close():
            # Выход по нажатию на "X"
            self.user_data = None
            self.root.destroy()
            import sys
            sys.exit(0)

        self.root.protocol("WM_DELETE_WINDOW", on_close)
        self.root.mainloop()
        return self.user_data