from PySide6.QtSql import QSqlDatabase
import sqlite3
db_address="J:\Vývoj\database.db"

def get_db_connection():
    if not QSqlDatabase.contains("qt_sql_default_connection"):
        db = QSqlDatabase.addDatabase("QSQLITE")
        db.setDatabaseName(db_address)
        if not db.open():
            print("Chyba při otevírání databáze")
        return db
    else:
        return QSqlDatabase.database("qt_sql_default_connection")
    
class SQLiteDB:
    def __init__(self, db_path=db_address):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)

    def cursor(self):
        return self.connect().cursor()

    def execute(self, query, params=()):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

    def fetchall(self, query, params=()):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()