import sys
import sqlite3
from PySide6.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget
from PySide6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQueryModel

# Initialize the SQLite database
def initialize_database():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    ''')

    # Create projects table (without storing email)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Insert sample data
    cursor.execute("INSERT OR IGNORE INTO users (id, name, email) VALUES (1, 'Alice', 'alice@example.com')")
    cursor.execute("INSERT OR IGNORE INTO users (id, name, email) VALUES (2, 'Bob', 'bob@example.com')")

    cursor.execute("INSERT OR IGNORE INTO projects (id, title, user_id) VALUES (1, 'Project A', 1)")
    cursor.execute("INSERT OR IGNORE INTO projects (id, title, user_id) VALUES (2, 'Project B', 2)")

    conn.commit()
    conn.close()

# Main application
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize database connection
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName("database.db")

        if not self.db.open():
            print("Error: Unable to connect to database")
            return

        # Create main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        # Table model for users
        self.users_model = QSqlTableModel(self)
        self.users_model.setTable("users")
        self.users_model.select()

        # Query model for projects (fetching email dynamically)
        self.projects_model = QSqlQueryModel(self)
        self.load_projects()

        # Table views
        self.users_table = QTableView()
        self.users_table.setModel(self.users_model)

        self.projects_table = QTableView()
        self.projects_table.setModel(self.projects_model)

        # Add tables to layout
        layout.addWidget(self.users_table)
        layout.addWidget(self.projects_table)

    def load_projects(self):
        """Load projects with user emails dynamically."""
        query = """
        SELECT projects.id, projects.title, projects.user_id, users.email
        FROM projects
        JOIN users ON projects.user_id = users.id
        """
        self.projects_model.setQuery(query)

# Run the application
if __name__ == "__main__":
    initialize_database()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
