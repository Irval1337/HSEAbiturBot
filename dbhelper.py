import sqlite3
import json

import excelhelper
import settings.config

connect = sqlite3.connect(settings.config.db_path, check_same_thread=False)
cursor = connect.cursor()


class WatchingUser:
    def __init__(self, user_data: str, watching_courses: dict = []):
        self.user_data = excelhelper.CourseTable.parse_snils(user_data)
        self.watching_courses = dict()


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, WatchingUser):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)

class User:
    def __init__(self, id: int = -1, watching: list[WatchingUser] = None, state: int = -1):
        self.id = id
        if watching:
            self.watching = watching
            self.state = state
        else:
            self.get()

    def update(self) -> None:
        cursor.execute(f'UPDATE USERS SET Watching=?, State=? WHERE Id=?',
                       [json.dumps(self.watching, cls=JSONEncoder), self.state, self.id])
        connect.commit()

    def get(self) -> None:
        if not self.exists():
            self.create()
            return
        info = cursor.execute('SELECT * FROM USERS WHERE Id=? LIMIT 1', [self.id]).fetchone()
        self.watching = json.loads(info[1])
        self.state = info[2]

    def exists(self) -> bool:
        return cursor.execute('SELECT Id FROM USERS WHERE Id=? LIMIT 1', [self.id]).fetchone() is not None

    def create(self) -> None:
        cursor.execute('INSERT INTO USERS (Id, Watching, State) VALUES (?, ?, ?)', [self.id, "[]", 0])
        connect.commit()
        self.watching = []

    @staticmethod
    def get_all():
        info = cursor.execute('SELECT * FROM USERS').fetchall()
        return [User(user[0], json.loads(user[1]), user[2]) for user in info]