from pymysql import connect as conn, cursors, OperationalError
from time import time as timestamp
from typing import List
from json import dumps, loads

from config import host, port, user, password, db
from tupes import Json


class Session:
    def __init__(self, version, system, architecture, release):
        self.version = version
        self.system = system
        self.architecture = architecture
        self.release = release
    
    def __str__(self) -> str:
        version = self.version
        system = self.system
        architecture = self.architecture
        release = self.release

        return f"""
        Session info:
        {version = !r}
        {system = !r}
        {architecture = !r}
        {release = !r}
        """

__all__ = ["Database"]


class Database:
    connection = None

    def __init__(self):
        try:
            self.connection = conn(
                host=host,
                port=port,
                user=user,
                password=password,
                db=db,
                cursorclass=cursors.DictCursor
            )
        except OperationalError as e:
            raise(Exception("Error connecting to database: {e}"))
 
        if self.connection is None:
            raise ValueError("Database connection is not established.")
        else:
            print("Database connection established successfully.")
    def __enter__(self) -> "Database":
        return self
    
    def __exit__(self, *exc_info) -> None:
        if self.connection:
            pass

    #region GET USER
    def get_all_users(self, limit: int = 50) -> Json:
        limit = int(limit)
        with self.connection.cursor() as sql:
            sql.execute("SELECT id, name, sessions FROM users ORDER BY id DESC LIMIT %s", (limit,))
            rows = sql.fetchall()

        return {
            "users": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "sessions": loads(row["sessions"])
                }
                for row in rows
            ]
        }

    def get_user_by_id(self, id: int) -> Json:
        with self.connection.cursor() as sql:
            sql.execute("SELECT id, name, sessions FROM users WHERE id = %s", (id,))
            row = sql.fetchone()

        return {
            "user": {
                "id": row["id"],
                "name": row["name"],
                "sessions": row["sessions"]
            }
        }
    
    def get_user_by_name(self, name: str) -> Json:
        with self.connection.cursor() as sql:
            sql.execute("SELECT id, name, sessions FROM users WHERE name = %s", (name,))
            row = sql.fetchone()

        return {
            "user": {
                "id": row["id"],
                "name": row["name"],
                "sessions": loads(row["sessions"])
            }
        }

    def get_id_by_name(self, name: str) -> int:
        with self.connection.cursor() as sql:
            sql.execute("SELECT id FROM users WHERE name = %s", (name,))
            row = sql.fetchone()
        return row["id"]

    def check_id(self, id: int):
        with self.connection.cursor() as sql:
            sql.execute("SELECT * FROM users WHERE id = %s", (id,))
            return sql.fetchone() is None
    
    def check_name(self, name: str):
        with self.connection.cursor() as sql:
            sql.execute("SELECT * FROM users WHERE name = %s", (name,))
            return sql.fetchone() is None

    #endregion
    #region SEND USER
    def add_user(self, id: int, name: str, password: str, token: str, sessions: Json):
        with self.connection.cursor() as sql:
            sql.execute(
                "INSERT INTO users (id, name, password, token, sessions) VALUES (%s, %s, %s, %s, %s)",
                (id, name, password, token, dumps(sessions))
            )
            self.connection.commit()

    def update_sessions(self, id: int, new_session: Json):
        with self.connection.cursor() as sql:
            sessions: List[Json] = sql.execute("SELECT id, name, sessions FROM users WHERE id = %s", (id,))
            sessions.append(new_session)
            sql.execute(
                "UPDATE users SET sessions = %s WHERE id = %s",
                (sessions, id)
            )
            self.connection.commit()

    def change_password(self, id: int, new_password: str):
        with self.connection.cursor() as sql:
            sql.execute("UPDATE users SET password = %s WHERE id = %s", (new_password, id))
            self.connection.commit()

    #endregion
    #region GET MESSAGE
    def get_messages(self, limit: int = 50):
        limit = int(limit)
        with self.connection.cursor() as sql:
            sql.execute("SELECT * FROM messages ORDER BY time DESC LIMIT %s", (limit,))
            rows = sql.fetchall()

        return {
            'messages': [
                    {
                        "id": row["id"],
                        "chat": row["chat"],
                        "user": row["user"],
                        "text": row["text"],
                        "time": row["time"]
                    } for row in rows
                ]
            }
    #endregion
    #region SEND MESSAGE
    def send_message(self, chat: Json, user: Json, text: str):
        with self.connection.cursor() as sql:       
            sql.execute("INSERT INTO messages (chat, user, text, time) VALUES (%s, %s, %s, %s)", (chat, user, text, timestamp()))
            self.connection.commit()

    #endregion
    #region GET CHATS
    def get_chats(self, limit: int = 50) -> Json:
        limit = int(limit)
        with self.connection.cursor() as sql:
            sql.execute('SELECT chat_id, title FROM chats ORDER BY chat_id DESC LIMIT %s', (limit,))
            rows = sql.fetchall()

        return {
            "chats": [
                {
                    "id": row["chat_id"],
                    "title": row["title"]
                } for row in rows
            ]
        }

    #endregion


if __name__ == "__main__":
    try:
        base = Database()
    except OperationalError as e:
        print("Error connecting to database.")
        print("Reconnect...") 
        base = Database()
