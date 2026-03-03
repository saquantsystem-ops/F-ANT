from peewee import SqliteDatabase
import jesse.helpers as jh
from jesse.services.env import ENV_VALUES
import os


# refactor above code into a class
class Database:
    def __init__(self):
        self.db = None

    def is_closed(self) -> bool:
        if self.db is None:
            return True
        return self.db.is_closed()

    def is_open(self) -> bool:
        if self.db is None:
            return False
        return not self.db.is_closed()

    def close_connection(self) -> None:
        if self.db:
            self.db.close()
            self.db = None

    def open_connection(self) -> None:
        print("Opening DB connection...")
        # if it's not None, then we already have a connection
        if self.db is not None:
            print("DB connection already exists.")
            return

        # Ensure storage directory exists
        path = os.path.join(os.getcwd(), 'storage')
        print(f"Creating storage dir at {path}")
        os.makedirs(path, exist_ok=True)
        
        db_path = os.path.join(path, 'db.sqlite')
        print(f"Connecting to SQLite at {db_path}")
        self.db = SqliteDatabase(db_path)

        # connect to the database
        self.db.connect()
        print("DB connected.")


database = Database()
