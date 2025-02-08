from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QTableView, QHBoxLayout, QAbstractItemView, QLabel, QLineEdit, QVBoxLayout, QMessageBox, QMenu, QFormLayout, QSpinBox, QDialogButtonBox, QDialog, QStyledItemDelegate
from PySide6.QtSql import QSqlDatabase, QSqlTableModel
from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtGui import QBrush
import sys
import sqlite3

from pdf2data import extract_data_from_pdf

class AddPolozkaDialog(QDialog):
    """Dialog window for adding a new položka."""
    def __init__(self, zakazka_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Přidat novou položku")
        self.zakazka_id = zakazka_id

        layout = QFormLayout()

        self.number_input = QLineEdit()
        self.number_input.setPlaceholderText("Číslo")

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Název")

        self.ks_input = QSpinBox()
        self.ks_input.setMinimum(1)

        layout.addRow("Číslo:", self.number_input)
        layout.addRow("Název:", self.title_input)
        layout.addRow("Ks:", self.ks_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_data(self):
        """Returns the entered data."""
        return self.number_input.text().strip(), self.title_input.text().strip(), self.ks_input.value()
    
class AddPodsestavaDialog(QDialog):
    """Dialog window for adding a new podsestava."""
    def __init__(self, zakazka_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Přidat novou podsestavu")
        self.zakazka_id = zakazka_id

        layout = QFormLayout()

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Název")

        layout.addRow("Název:", self.title_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_data(self):
        """Returns the entered data."""
        return self.title_input.text().strip()

class PDFImporterApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Zakázky")
        
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        screen_width = QApplication.primaryScreen().size().width()

        search_layout = QVBoxLayout()
        search_layout.setContentsMargins(10, 20, 10, 20)

        # Input at the top
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pro vyhledávání začni psát")
        self.search_input.setFixedWidth(int(screen_width * 0.20))
        self.search_input.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_input)

        # Add stretch between input and button
        search_layout.addStretch()

        # Button at the bottom
        self.import_button = QPushButton("Nahrát objednávku")
        self.import_button.setFixedWidth(200)
        self.import_button.clicked.connect(self.import_pdf)
        search_layout.addWidget(self.import_button)

        layout.addLayout(search_layout)

        # Table View for zakázka
        zakazka_layout = QVBoxLayout()
        self.zakazka_label = QLabel("Zakázky")
        self.zakazka_table = QTableView()
        self.zakazka_table.setFixedWidth(340)
        zakazka_layout.addWidget(self.zakazka_label)
        zakazka_layout.addWidget(self.zakazka_table)
        layout.addLayout(zakazka_layout)
        
        # Table View for položka
        polozka_layout = QVBoxLayout()
        self.polozka_label = QLabel("Položky")
        self.podpolozka_label = QLabel("Podsestavy")
        self.polozka_table = QTableView()

        self.polozka_table.setFixedWidth(650)
        self.podpolozka_table = QTableView()
        self.podpolozka_table.setFixedWidth(650)
        polozka_layout.addWidget(self.polozka_label)
        polozka_layout.addWidget(self.polozka_table)
        # polozka_layout.addWidget(self.podpolozka_label)
        # polozka_layout.addWidget(self.podpolozka_table)
        layout.addLayout(polozka_layout)


         # Enable right-click context menu on polozka_table
        self.polozka_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.polozka_table.customContextMenuRequested.connect(self.show_polozka_context_menu)

        self.zakazka_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.zakazka_table.customContextMenuRequested.connect(self.show_zakazka_context_menu)


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
                podsestava BOOLEAN NOT NULL DEFAULT 0,
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
        self.zakazka_model.setHeaderData(1, Qt.Orientation.Horizontal, "Číslo")
        self.zakazka_model.setHeaderData(2, Qt.Orientation.Horizontal, "Název")


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
        self.polozka_model.setHeaderData(1, Qt.Orientation.Horizontal, "Číslo")
        self.polozka_model.setHeaderData(2, Qt.Orientation.Horizontal, "Název")
        self.polozka_model.setHeaderData(3, Qt.Orientation.Horizontal, "Ks")
        self.polozka_model.setHeaderData(4, Qt.Orientation.Horizontal, "Zakázka")
        self.polozka_model.setHeaderData(5, Qt.Orientation.Horizontal, "Výkres")

        self.polozka_table.setModel(self.polozka_model)
        self.polozka_table.hideColumn(0)
        self.polozka_table.hideColumn(6)
        self.polozka_table.setSortingEnabled(True)
        self.polozka_table.sortByColumn(5, Qt.DescendingOrder)
        self.polozka_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.polozka_table.verticalHeader().setVisible(False)
        self.polozka_table.setColumnWidth(1, 70)
        self.polozka_table.setColumnWidth(2, 350)
        self.polozka_table.setColumnWidth(3, 30)
        self.polozka_table.setColumnWidth(4, 80)
        self.polozka_table.setColumnWidth(5, 80)

        # Proxy model for filtering polozka
        self.polozka_filter_model = QSortFilterProxyModel(self)
        self.polozka_filter_model.setSourceModel(self.polozka_model)
        self.polozka_filter_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.polozka_filter_model.setFilterKeyColumn(4)  # Filter based on the zakazka_number
        self.polozka_filter_model.setFilterFixedString("")  # No filter initially

        self.polozka_table.setModel(self.polozka_filter_model)

    def show_zakazka_context_menu(self, position):
        """Shows context menu on right-click in the zakazka table."""
        index = self.zakazka_table.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu(self)
        action_add_polozka = menu.addAction("Přidat položku")
        action_add_podsestava = menu.addAction("Přidat podsestavu")

        action = menu.exec(self.zakazka_table.viewport().mapToGlobal(position))
        if action == action_add_polozka:
            self.add_polozka(index.row())
        if action == action_add_podsestava:
            self.add_podsestava(index.row())

    def add_polozka(self, row):
        """Opens a dialog to add a new polozka and saves it to the database."""
        zakazka_id = self.zakazka_model.data(self.zakazka_model.index(row, 0))

        dialog = AddPolozkaDialog(zakazka_id, self)
        if dialog.exec():
            number, title, ks = dialog.get_data()

            if not title:  # Title is required
                return

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()

            cursor.execute("INSERT INTO položka (number, title, ks, zakazka) VALUES (?, ?, ?, ?)",
                           (number if number else None, title, ks, zakazka_id))

            conn.commit()
            conn.close()

            # Refresh table
            self.polozka_model.select()

    def add_podsestava(self, row):
        """Opens a dialog to add a new podsestava and saves it to the database."""
        zakazka_id = self.zakazka_model.data(self.zakazka_model.index(row, 0))

        dialog = AddPodsestavaDialog(zakazka_id, self)
        if dialog.exec():
            title = dialog.get_data()

            if not title:  # Title is required
                return

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()

            cursor.execute("INSERT INTO položka (title, zakazka, podsestava) VALUES (?, ?, ?)",
                        (title, zakazka_id, 1))
            
            # Get the ID of the newly inserted podsestava
            polozka_id = cursor.lastrowid  

            conn.commit()
            conn.close()

            # Refresh table
            self.polozka_model.select()

            # Automatically generate number for the new podsestava
            self.generate_number(self.polozka_model.rowCount() - 1)  # Pass the last row index

    def show_polozka_context_menu(self, position):
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
            zakazka_number = self.zakazka_model.data(selected_indexes[0], Qt.DisplayRole)
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
            
            # zakazka_id = zakazka_data[0][0]  # Get zakazka nuber as foreign key
            zakazka_id = cursor.lastrowid # Get the last inserted ID for foreign key
            
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