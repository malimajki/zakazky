from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTableView
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlRelationalTableModel
import sys
import sqlite3
from pdf2data import extract_data_from_pdf

class PDFImporterApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Správa zakázek - konstrukce")
        
        layout = QVBoxLayout()

        # Create Import button
        self.import_button = QPushButton("Import PDF")
        self.import_button.clicked.connect(self.import_pdf)
        layout.addWidget(self.import_button)

        # Table View for zakázka
        self.zakazka_table = QTableView()
        layout.addWidget(self.zakazka_table)
        
        # Table View for položka
        self.polozka_table = QTableView()
        layout.addWidget(self.polozka_table)

        self.setLayout(layout)
        
        # Initialize the database and tables
        self.initialize_database()

        # Set up models for the tables
        self.setup_models()

        # Maximize the window, keeping the title bar visible
        self.showMaximized()

    def initialize_database(self):
        """Creates the tables in the database."""
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        # Create zakázka table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS zakázka (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT,
                title TEXT,
                manazer TEXT NULL,
                projektant NULL,
                obchod NULL
            )
        ''')

        # Create položka table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS položka (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT,
                title TEXT,
                quantity INTEGER,
                foreign_key_zakazka INTEGER,
                vykres TEXT,
                vytvoreno TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                kreslil TEXT NULL,
                start DATE NULL,
                finish DATE NULL,
                cancel DATE NULL,
                poznamky TEXT,
                FOREIGN KEY(foreign_key_zakazka) REFERENCES zakázka(id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def setup_models(self):
        """Sets up the models for the tables."""
        # Set up QSqlDatabase connection
        db = QSqlDatabase.addDatabase("QSQLITE")
        db.setDatabaseName("database.db")
        db.open()

        # Zakázka model
        self.zakazka_model = QSqlTableModel(self, db)
        self.zakazka_model.setTable("zakázka")
        
        self.zakazka_model.setQuery("SELECT number, title FROM zakázka", db)
        # self.zakazka_model.select()  # Load the data
        self.zakazka_table.setModel(self.zakazka_model)

        # Polozka model
        self.polozka_model = QSqlRelationalTableModel(self, db)
        self.polozka_model.setTable("položka")          
        self.polozka_model.setQuery("""
            SELECT p.number, p.title, p.quantity, z.number as foreign_key_title 
            FROM položka p 
            LEFT JOIN zakázka z ON p.foreign_key_zakazka = z.number
        """)  # Perform the join to get the related title
        self.polozka_model.select()  # Load the data
        self.polozka_table.setModel(self.polozka_model)

        # Adjust column widths to fit content
        self.zakazka_table.resizeColumnsToContents()
        self.polozka_table.resizeColumnsToContents()

    def import_pdf(self):
        """Handles PDF import and data extraction."""
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(self, "Select PDF File", "", "PDF Files (*.pdf)")
        if file_path:
            print(f"Selected file: {file_path}")
            # Extract data from PDF
            data = extract_data_from_pdf(file_path)
            # Insert the extracted data into the database
            self.insert_data(data)

    def insert_data(self, data):
        """Inserts data into the database."""
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        # Insert zakázka data
        zakazka_data = data['zakázka']
        cursor.execute('''
            INSERT INTO zakázka (number, title) VALUES (?, ?)
        ''', (zakazka_data[0][0], zakazka_data[1][0]))
        
        zakazka_id = cursor.lastrowid  # Get the last inserted ID for foreign key
        
        # Insert položka data
        for item in data['položky']:
            cursor.execute('''
                INSERT INTO položka (number, title, quantity, foreign_key_zakazka) 
                VALUES (?, ?, ?, ?)
            ''', (item[0][0], item[1][0], item[2][0], zakazka_id))
        
        conn.commit()
        conn.close()

        # Refresh the models to reflect changes
        self.zakazka_model.select()
        self.polozka_model.select()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFImporterApp()
    window.show()
    sys.exit(app.exec())
