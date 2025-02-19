from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QTableView, QHBoxLayout, QAbstractItemView, QLabel, QLineEdit, QVBoxLayout, QMessageBox, QMenu, QDialog
from PySide6.QtSql import QSqlDatabase, QSqlTableModel, QSqlRelationalTableModel, QSqlRelationalDelegate, QSqlRelation, QSqlQueryModel, QSqlQuery
from PySide6.QtCore import QSortFilterProxyModel, Qt, QRegularExpression
from PySide6.QtGui import QAction
import sys
import sqlite3

from functions.pdf2data import extract_data_from_pdf
from classes.nova_zakazka_dialog import NovaZakazkaDialog
from classes.nova_polozka_dialog import AddPolozkaDialog
from classes.nova_podsestava_dialog import AddPodsestavaDialog
from classes.edit_polozka_dialog import EditItemDialog


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

        self.new_order_button = QPushButton("Nová zakázka")
        self.new_order_button.setFixedWidth(200)
        self.new_order_button.clicked.connect(self.vytvorit_zakazku)
        search_layout.addWidget(self.new_order_button)


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

        self.polozka_table.setFixedWidth(850)
        self.podpolozka_table = QTableView()
        polozka_layout.addWidget(self.polozka_label)
        polozka_layout.addWidget(self.polozka_table)
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
                vykres TEXT NULL UNIQUE,
                FOREIGN KEY(zakazka) REFERENCES zakázka(id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_db_connection():
        if not QSqlDatabase.contains("qt_sql_default_connection"):
            db = QSqlDatabase.addDatabase("QSQLITE")
            db.setDatabaseName("database.db")
            if not db.open():
                print("Chyba při otevírání databáze")
            return db
        else:
            return QSqlDatabase.database("qt_sql_default_connection")

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
        self.zakazka_model.dataChanged.connect(self.update_polozka_table)

        # Polozka model
        self.polozka_model = QSqlRelationalTableModel(self, db)
        self.polozka_model.setTable("položka")
        self.polozka_model.setRelation(4, QSqlRelation("zakázka", "id", "title"))
        self.polozka_model.select()
        self.polozka_model.setEditStrategy(QSqlTableModel.OnFieldChange)

        # Assign to table
        self.polozka_table.setModel(self.polozka_model)
        self.polozka_table.setItemDelegate(QSqlRelationalDelegate(self.polozka_table))  # Enables dropdown for relations
        self.polozka_table.hideColumn(0)
        self.polozka_table.hideColumn(4)
        self.polozka_table.setSortingEnabled(True)
        self.polozka_table.sortByColumn(6, Qt.DescendingOrder)
        self.polozka_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.polozka_table.verticalHeader().setVisible(False)
        self.polozka_table.setColumnWidth(1, 70)
        self.polozka_table.setColumnWidth(2, 350)
        self.polozka_table.setColumnWidth(3, 30)
        self.polozka_table.setColumnWidth(5, 150)
        self.polozka_table.setColumnWidth(6, 150)

        # Model pro filtrování podle ID zakázky
        self.polozka_filter_helper = QSqlQueryModel()
        self.polozka_filter_helper.setQuery('''
            SELECT p.id, p.number, p.title, p.ks, p.zakazka, z.title AS zakazka_name, p.vykres
            FROM položka p
            LEFT JOIN zakázka z ON p.zakazka = z.id
        ''') 

        self.polozka_filter_model = QSortFilterProxyModel(self)
        self.polozka_filter_model.setSourceModel(self.polozka_filter_helper)
        self.polozka_filter_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.polozka_filter_model.setFilterKeyColumn(-1)
        self.polozka_filter_model.setFilterFixedString("")  # No filter initially

                # Set headers
        self.polozka_filter_model.setHeaderData(1, Qt.Orientation.Horizontal, "Číslo")
        self.polozka_filter_model.setHeaderData(2, Qt.Orientation.Horizontal, "Název")
        self.polozka_filter_model.setHeaderData(3, Qt.Orientation.Horizontal, "Ks")
        self.polozka_filter_model.setHeaderData(5, Qt.Orientation.Horizontal, "Zakázka")
        self.polozka_filter_model.setHeaderData(6, Qt.Orientation.Horizontal, "Výkres")

        self.polozka_table.setModel(self.polozka_filter_model)

    def update_polozka_table(self):
        """Aktualizuje tabulku položek po změně názvu zakázky."""
        self.zakazka_model.submitAll()     # Uloží změny v zakazka_model
        self.polozka_model.select()        # Načte znovu data v polozka_model
        self.polozka_filter_model.invalidate()  # Obnoví proxy model
        self.polozka_filter_helper.setQuery('''
                SELECT p.id, p.number, p.title, p.ks, p.zakazka, z.title AS zakazka_name, p.vykres
                FROM položka p
                LEFT JOIN zakázka z ON p.zakazka = z.id
            ''')


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
            self.update_polozka_table()

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

            cursor.execute("INSERT INTO položka (title, zakazka) VALUES (?, ?)",
                        (title, zakazka_id))

            conn.commit()
            conn.close()

            # Refresh table
            self.update_polozka_table()

    def show_polozka_context_menu(self, position):
        """Shows context menu on right-click in the položka table."""
        index = self.polozka_table.indexAt(position)
        if not index.isValid():
            return

        # Vytvoření kontextového menu
        menu = QMenu(self)
        
        # Původní akce
        action_generate_number = menu.addAction("Generovat číslo")

        # Nová akce pro editaci položky
        action_edit_item = menu.addAction("Editovat položku")

        # Zobrazení menu a zachycení vybrané akce
        action = menu.exec(self.polozka_table.viewport().mapToGlobal(position))

        # Akce pro "Generovat číslo"
        if action == action_generate_number:
            self.generate_vykres(index.row())
        
        # Akce pro "Editovat položku"
        if action == action_edit_item:
            self.edit_selected_item()


    def edit_selected_item(self):

        def get_db_connection():
            if not QSqlDatabase.contains("qt_sql_default_connection"):
                db = QSqlDatabase.addDatabase("QSQLITE")
                db.setDatabaseName("database.db")
                if not db.open():
                    print("Chyba při otevírání databáze")
                return db
            else:
                return QSqlDatabase.database("qt_sql_default_connection")

        self.db = get_db_connection()

        if not self.db.open():
            print("Chyba při otevírání databáze")

        index = self.polozka_table.currentIndex()
        if not index.isValid():
            return

        source_index = self.polozka_filter_model.mapToSource(index)
        polozka_id = self.polozka_filter_helper.data(self.polozka_filter_helper.index(source_index.row(), 0))
        current_number = self.polozka_filter_helper.data(self.polozka_filter_helper.index(source_index.row(), 1))
        current_title = self.polozka_filter_helper.data(self.polozka_filter_helper.index(source_index.row(), 2))
        current_vykres = self.polozka_filter_helper.data(self.polozka_filter_helper.index(source_index.row(), 6))

        dialog = EditItemDialog(self.db, polozka_id, current_number, current_title, current_vykres, self)
        if dialog.exec():
            self.polozka_model.select()
            self.polozka_filter_helper.setQuery(self.polozka_filter_helper.query().executedQuery())  # Refresh filter model

    def generate_vykres(self, row):
        """Generuje hodnotu vykres pro položku na daném řádku, pokud ještě není vyplněna."""
        # Získání indexu vybrané položky podle řádku
        index = self.polozka_filter_model.index(row, 0)  # Sloupec 0 je ID položky
        item_id = self.polozka_filter_model.data(index, Qt.DisplayRole)

        # Připojení k databázi
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Kontrola, jestli už vykres existuje
        cursor.execute("SELECT vykres FROM položka WHERE id = ?", (item_id,))
        existing_vykres = cursor.fetchone()
        if existing_vykres and existing_vykres[0]:  # Pokud existuje a není prázdný
            QMessageBox.warning(self, "Upozornění", "Tato položka již má číslo výkresu.")
            conn.close()
            return

        # Získání ID zakázky
        zakazka_id = self.polozka_filter_model.data(index.siblingAtColumn(4), Qt.DisplayRole)

        # Získání čísla zakázky
        cursor.execute("SELECT number FROM zakázka WHERE id = ?", (zakazka_id,))
        zakazka_number = cursor.fetchone()
        if not zakazka_number:
            QMessageBox.warning(self, "Upozornění", "Nelze najít číslo zakázky.")
            conn.close()
            return
        zakazka_number = zakazka_number[0][:3]

        # Získání nejvyššího čísla pro danou zakázku
        cursor.execute("""
            SELECT vykres FROM položka 
            WHERE zakazka = ? AND vykres LIKE ?
            ORDER BY vykres DESC LIMIT 1
        """, (zakazka_id, f"K-{zakazka_number}-%"))
        last_vykres = cursor.fetchone()
        if last_vykres:
            # Extrahování posledního čísla
            last_number = int(last_vykres[0].split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        # Vygenerování nového čísla
        new_vykres = f"K-{zakazka_number}-{new_number:02d}"

        # Aktualizace hodnoty v databázi
        cursor.execute("UPDATE položka SET vykres = ? WHERE id = ?", (new_vykres, item_id))
        conn.commit()
        conn.close()

        self.update_polozka_table()


    def on_search_text_changed(self, text):
        """Triggered when the search input changes."""
        regex = QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.polozka_filter_model.setFilterRegularExpression(regex)

    def zakazka_changed(self):
        selected_indexes = self.zakazka_table.selectionModel().selectedRows()
        if selected_indexes:
            # Získání ID vybrané zakázky (první sloupec je ID, ale je skrytý)
            zakazka_id = self.zakazka_model.data(selected_indexes[0].siblingAtColumn(0), Qt.DisplayRole)
            self.polozka_filter_model.setFilterKeyColumn(4)  # Filtruj podle sloupce `zakazka` v tabulce položka
            self.polozka_filter_model.setFilterFixedString(str(zakazka_id))
        else:
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
        self.update_polozka_table()

    def vytvorit_zakazku(self):
        # Otevření vlastního dialogu
        dialog = NovaZakazkaDialog(self)
        if dialog.exec() == QDialog.Accepted:
            nazev, cislo = dialog.get_data()
            
            # Kontrola, zda jsou vyplněna obě pole
            if not nazev or not cislo:
                QMessageBox.warning(self, "Neplatné údaje", "Vyplňte prosím název i číslo zakázky.")
                return
            
            # Kontrola duplicitního čísla zakázky
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM zakázka WHERE number = ?", (cislo,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(self, "Duplicitní číslo", "Zakázka s tímto číslem již existuje.")
                conn.close()
                return
            
            # Uložení nové zakázky do databáze
            cursor.execute("INSERT INTO zakázka (title, number) VALUES (?, ?)", (nazev, cislo))
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Zakázka vytvořena", f"Zakázka '{nazev}' byla vytvořena.")
            
            # Aktualizace tabulky zakázek
            self.zakazka_model.select()
            self.update_polozka_table()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFImporterApp()
    window.show()
    sys.exit(app.exec())