import sqlite3

def initialize_database_call(self):
        """Creates the tables in the database."""
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        # Create zakázka table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS zakázka (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT UNIQUE,
                title TEXT
            )
        ''')

        # Create položka table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS položka (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT,
                title TEXT,
                ks INTEGER,
                zakazka INTEGER,
                vykres TEXT NULL,
                FOREIGN KEY(zakazka) REFERENCES zakázka(id)
            )
        ''')
        
        conn.commit()
        conn.close()
