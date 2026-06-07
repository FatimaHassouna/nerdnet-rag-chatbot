import sqlite3
import hashlib
from typing import Optional, Tuple


def verify_user(username: str, password: str) -> bool:
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect('nerdnet_auth.db')
    c = conn.cursor()
    c.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == password_hash

def get_user(username: str) -> Optional[Tuple]:
    conn = sqlite3.connect('nerdnet_auth.db')
    c = conn.cursor()
    c.execute('SELECT id, username, email, created_at FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    return result