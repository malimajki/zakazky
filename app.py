from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QTableView, QHBoxLayout, QAbstractItemView, QLabel, QLineEdit, QVBoxLayout, QMessageBox, QMenu
from PySide6.QtSql import QSqlDatabase, QSqlTableModel
from PySide6.QtCore import QSortFilterProxyModel, Qt
import sys
import sqlite3

from pdf2data import extract_data_from_pdf

class PDFImporterApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Zakázky")
        
        layout = QHBoxLayout()

        search_layout = QVBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pro vyhledávání začni psát")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.import_button = QPushButton("Nahrát objednávku")
        self.import_button.setFixedWidth(200)
        self.import_button.clicked.connect(self.import_pdf)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.import_button)
        layout.addLayout(search_layout)

        # Create Import button

        # Table View for zakázka
        self.zakazka_table = QTableView()
        self.zakazka_table.setFixedWidth(340)
        layout.addWidget(self.zakazka_table)
        
        # Table View for položka
        self.polozka_table = QTableView()
        self.polozka_table.setFixedWidth(670)
        layout.addWidget(self.polozka_table)

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Najdi:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pro vyhledávání začni psát")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

         # Enable right-click context menu on polozka_table
        self.polozka_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.polozka_table.customContextMenuRequested.connect(self.show_context_menu)


        self.setLayout(layout)
        self.showMaximized()
        
        # Initialize the database and tables
        self.initialize_database()

        # Set up models for the tables
        self.setup_models()

    def initialize_database(self):
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

    def setup_models(self):
        """Sets up the models for the tables."""
        # Set up QSqlDatabase connection
        db = QSqlDatabase.addDatabase("QSQLITE")
        db.setDatabaseName("database.db")
        db.open()

        # Zakázka model
        self.zakazka_model = QSqlTableModel(self, db)
        self.zakazka_model.setTable("zakázka")
        self.zakazka_model.select()  # Load the data
        self.zakazka_table.setModel(self.zakazka_model)
        self.zakazka_table.selectionModel().selectionChanged.connect(self.zakazka_changed)
        self.zakazka_table.hideColumn(0)
        self.zakazka_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.zakazka_table.verticalHeader().setVisible(False)
        self.zakazka_table.setColumnWidth(1, 80)
        self.zakazka_table.setColumnWidth(2, 250)

        # Polozka model
        self.polozka_model = QSqlTableModel(self, db)
        self.polozka_model.setTable("položka")
        self.polozka_model.select()  # Load the data
        self.polozka_table.setModel(self.polozka_model)
        self.polozka_table.hideColumn(0)
        self.polozka_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.polozka_table.verticalHeader().setVisible(False)
        self.polozka_table.setColumnWidth(1, 70)
        self.polozka_table.setColumnWidth(2, 400)
        self.polozka_table.setColumnWidth(3, 30)
        self.polozka_table.setColumnWidth(4, 80)
        self.polozka_table.setColumnWidth(5, 80)

        # Proxy model for filtering polozka
        self.polozka_filter_model = QSortFilterProxyModel(self)
        self.polozka_filter_model.setSourceModel(self.polozka_model)
        self.polozka_filter_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.polozka_filter_model.setFilterKeyColumn(-1)  # Filter based on the zakazka_number
        self.polozka_filter_model.setFilterFixedString("")  # No filter initially

        self.polozka_table.setModel(self.polozka_filter_model)

    def show_context_menu(self, position):
        """Shows context menu on right-click in the položka table."""
        index = self.polozka_table.indexAt(position)
        if not index.isValid():
            return
        menu = QMenu(self)
        action_generate_number = menu.addAction("Generovat číslo")

        action = menu.exec(self.polozka_table.viewport().mapToGlobal(position))
        if action == action_generate_number:
            self.generate_number(index.row())

    def generate_number(self, row):
        """Generates and assigns a number in the format K-{zakazka}-{unique_number}."""
        zakazka_index = self.polozka_filter_model.index(row, 4)  # Get zakazka column (foreign key)
        polozka_id_index = self.polozka_filter_model.index(row, 0)  # Get polozka ID column

        zakazka_id = self.polozka_filter_model.data(zakazka_index)
        polozka_id = self.polozka_filter_model.data(polozka_id_index)

        if zakazka_id is None or polozka_id is None:
            return

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Get the highest number assigned for this zakazka
        cursor.execute("SELECT vykres FROM položka WHERE zakazka = ? AND vykres LIKE ?", (zakazka_id, f"K-{zakazka_id[:3]}-%"))
        existing_numbers = cursor.fetchall()

        # Find the next available vykres
        next_number = 1
        if existing_numbers:
            existing_numbers = [int(num[0].split('-')[-1]) for num in existing_numbers if num[0] and num[0].startswith(f"K-{zakazka_id[:3]}-")]
            if existing_numbers:
                next_number = max(existing_numbers) + 1

        generated_number = f"K-{zakazka_id[:3]}-{next_number:02d}"

        # Update the database
        cursor.execute("UPDATE položka SET vykres = ? WHERE id = ? AND (vykres IS NULL OR vykres = '')", (generated_number, polozka_id))
        conn.commit()
        conn.close()

        # Refresh model
        self.polozka_model.select()


    def on_search_text_changed(self, text):
        """Triggered when the search input changes."""
        self.polozka_filter_model.setFilterFixedString(text)

    def zakazka_changed(self):
        selected_indexes = self.zakazka_table.selectionModel().selectedRows()
        if selected_indexes:
            # Get the selected zakazka_nuber
            zakazka_number = self.zakazka_model.data(selected_indexes[0].siblingAtColumn(1), Qt.DisplayRole)
            self.polozka_filter_model.setFilterFixedString(str(zakazka_number))
            
        else:
            # No customer selected, clear the car view
            self.polozka_filter_model.setFilterFixedString("")


    def import_pdf(self):
        """Handles PDF import and data extraction."""
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(self, "Vyberte PDF soubor s objednávkou", "", "PDF Files (*.pdf)")
        if file_path:
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
        try:
            cursor.execute('''
                INSERT INTO zakázka (number, title) VALUES (?, ?)
            ''', (zakazka_data[0][0], zakazka_data[1][0]))
            
            zakazka_id = zakazka_data[0][0]  # Get the last inserted ID for foreign key
            
            # Insert položka data
            for item in data['položky']:
                cursor.execute('''
                    INSERT INTO položka (number, title, ks, zakazka) 
                    VALUES (?, ?, ?, ?)
                ''', (item[0][0], item[1][0], item[2][0], zakazka_id))
        
            conn.commit()
            
        except sqlite3.IntegrityError:
            conn.rollback()  # Rollback in case of an error

            # Show pop-up warning message
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Duplicitní zakázka")
            msg_box.setText(f"Zakázka s číslem {zakazka_data[0][0]} již existuje!")
            msg_box.exec()

        finally:
            conn.close()

        # Refresh the models to reflect changes
        self.zakazka_model.select()
        self.polozka_model.select()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFImporterApp()
    window.show()
    sys.exit(app.exec())