# Утилита для работы с bcrypt
import bcrypt

def hash_password(plain_password: str) -> str:
    # Создаёт хеш пароля с солью (bcrypt)
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, stored_hash: str) -> bool:
    # Проверяет, совпадает ли пароль с хешем
    return bcrypt.checkpw(plain_password.encode('utf-8'), stored_hash.encode('utf-8'))