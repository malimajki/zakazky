from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QTableView, QHBoxLayout, QAbstractItemView, QLabel, QLineEdit, QVBoxLayout, QMessageBox, QMenu, QDialog, QStyledItemDelegate
from PySide6.QtSql import QSqlDatabase, QSqlTableModel, QSqlRelationalTableModel, QSqlRelationalDelegate, QSqlRelation, QSqlQueryModel, QSqlQuery
from PySide6.QtCore import QSortFilterProxyModel, Qt, QRegularExpression
from PySide6.QtGui import QIcon
import sys
import sqlite3
from datetime import datetime

from functions.pdf2data import extract_data_from_pdf
from classes.nova_zakazka_dialog import NovaZakazkaDialog
from classes.nova_polozka_dialog import AddPolozkaDialog
from classes.edit_polozka_dialog import EditItemDialog
import ctypes
import getpass

myappid = 'VHZ-DIS.konstrukcni_dokumentace.1.0'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
db_address="J:\Vývoj\database.db"
# db_address="database.db"

class CenterAlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if index.column() == 1:  # Pouze sloupec 1
            option.displayAlignment = Qt.AlignCenter


class NumberingOfDesignDocumentation(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        screen_width = QApplication.primaryScreen().size().width()

        search_layout = QVBoxLayout()
        search_layout.setContentsMargins(10, 20, 10, 20)

        # Input at the top
        self.search_input_label = QLabel("Vyhledávání v položkách:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pro vyhledávání začni psát")
        self.search_input.setFixedWidth(int(screen_width * 0.20))
        self.search_input.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_input_label)
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
        self.zakazka_table.setFixedWidth(330)
        zakazka_layout.addWidget(self.zakazka_label)
        zakazka_layout.addWidget(self.zakazka_table)
        layout.addLayout(zakazka_layout)
        
        # Table View for položka
        polozka_layout = QVBoxLayout()
        self.polozka_label = QLabel("Položky")
        self.polozka_table = QTableView()

        self.polozka_table.setFixedWidth(960)
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
        conn = sqlite3.connect(db_address)
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
                date TEXT NULL,
                user TEXT NULL, 
                FOREIGN KEY(zakazka) REFERENCES zakázka(id)
                       
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_db_connection():
        if not QSqlDatabase.contains("qt_sql_default_connection"):
            db = QSqlDatabase.addDatabase("QSQLITE")
            db.setDatabaseName(db_address)
            if not db.open():
                print("Chyba při otevírání databáze")
            return db
        else:
            return QSqlDatabase.database("qt_sql_default_connection")

    def setup_models(self):
        """Sets up the models for the tables."""
        # Set up QSqlDatabase connection
        db = QSqlDatabase.addDatabase("QSQLITE")
        db.setDatabaseName(db_address)
        db.open()

        # Zakázka model
        self.zakazka_model = QSqlTableModel(self, db)
        self.zakazka_model.setTable("zakázka")
        self.zakazka_model.select()  # Load the data
        self.zakazka_model.setHeaderData(1, Qt.Orientation.Horizontal, "Číslo")
        self.zakazka_model.setHeaderData(2, Qt.Orientation.Horizontal, "Název")
        
        self.zakazka_table.setModel(self.zakazka_model)
        self.zakazka_table.setSortingEnabled(True)
        self.zakazka_table.setAlternatingRowColors(True)
        self.zakazka_table.setStyleSheet("""
                QTableView { 
                    alternate-background-color: #2C2C2C; 
                    background-color: #3b3b3b; 
                    selection-background-color: #89CFF0;
                    selection-color: #3b3b3b;
                }
            """)
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
        self.polozka_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.polozka_table.verticalHeader().setVisible(False)
        self.polozka_table.setColumnWidth(1, 90)
        self.polozka_table.setColumnWidth(2, 350)
        self.polozka_table.setColumnWidth(3, 90)
        self.polozka_table.setColumnWidth(5, 180)
        self.polozka_table.setColumnWidth(6, 90)
        self.polozka_table.setColumnWidth(7, 40)
        self.polozka_table.setColumnWidth(8, 90)
        self.polozka_table.setItemDelegateForColumn(1, CenterAlignDelegate(self.polozka_table))

        # Model pro filtrování podle ID zakázky
        self.polozka_filter_helper = QSqlQueryModel()
        self.filter_polozky_by_zakazka()  # načte vše bez filtru

        self.polozka_filter_model = QSortFilterProxyModel(self)
        self.polozka_filter_model.setSourceModel(self.polozka_filter_helper)
        self.polozka_filter_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.polozka_filter_model.setFilterKeyColumn(-1)
        self.polozka_filter_model.setFilterFixedString("")  # No filter initially

        # Set headers
        self.polozka_filter_model.setHeaderData(1, Qt.Orientation.Horizontal, "Výkres")
        self.polozka_filter_model.setHeaderData(2, Qt.Orientation.Horizontal, "Název")
        self.polozka_filter_model.setHeaderData(3, Qt.Orientation.Horizontal, "Položka")
        self.polozka_filter_model.setHeaderData(5, Qt.Orientation.Horizontal, "Zakázka")
        self.polozka_filter_model.setHeaderData(6, Qt.Orientation.Horizontal, "Datum")
        self.polozka_filter_model.setHeaderData(7, Qt.Orientation.Horizontal, "Ks")
        self.polozka_filter_model.setHeaderData(8, Qt.Orientation.Horizontal, "Přidal")
        self.polozka_filter_model.sort(1, Qt.AscendingOrder)

        self.polozka_table.setAlternatingRowColors(True)
        self.polozka_table.setStyleSheet("""
                QTableView { 
                    alternate-background-color: #2C2C2C;  /* Světle šedá */
                    background-color: #3b3b3b;  /* Bílá pro normální řádky */
                }
            """)


        self.polozka_table.setModel(self.polozka_filter_model)

    def filter_polozky_by_zakazka(self, zakazka_id=None):
        """Filtruje položky podle ID zakázky pomocí parametrizovaného dotazu."""
        query = QSqlQuery()
        
        if zakazka_id is not None:
            query.prepare('''
                SELECT p.id, p.vykres, p.title, p.number, p.zakazka, z.title AS zakazka_name, p.date, p.ks, p.user
                FROM položka p
                LEFT JOIN zakázka z ON p.zakazka = z.id
                WHERE p.zakazka = :zakazka_id
            ''')
            query.bindValue(':zakazka_id', zakazka_id)
        else:
            query.prepare('''
                SELECT p.id, p.vykres, p.title, p.number, p.zakazka, z.title AS zakazka_name, p.date, p.ks, p.user
                FROM položka p
                LEFT JOIN zakázka z ON p.zakazka = z.id
            ''')
        
        query.exec()

        self.polozka_filter_helper.setQuery(query)

    def update_polozka_table(self):
        """Aktualizuje tabulku položek po změně názvu zakázky."""
        self.zakazka_model.submitAll()     # Uloží změny v zakazka_model
        self.polozka_model.select()        # Načte znovu data v polozka_model
        self.polozka_filter_model.invalidate()  # Obnoví proxy model
        self.polozka_filter_helper.setQuery('''
                SELECT p.id, p.vykres, p.title, p.number, p.zakazka, z.title AS zakazka_name, p.date, p.ks, p.user
                FROM položka p
                LEFT JOIN zakázka z ON p.zakazka = z.id
            ''')


    def show_zakazka_context_menu(self, position):
        """Shows context menu on right-click in the zakazka table."""
        index = self.zakazka_table.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu(self)

        menu.setStyleSheet("""
            QMenu {
                background-color: #2C2C2C;
                color: white;
                border: 1px solid #444;
            }
            QMenu::item {
                background-color: transparent;
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #444;
            }
        """)

        action_add_polozka = menu.addAction("Přidat položku")
        action_delete_zakazka = menu.addAction("Smazat zakázku")

        action = menu.exec(self.zakazka_table.viewport().mapToGlobal(position))
        if action == action_add_polozka:
            self.add_polozka(index.row())
        if action == action_delete_zakazka:
            self.delete_selected_zakazka(index.row())

    def delete_selected_zakazka(self, row):
         # Získej ID zakázky z tabulky (předpokládáme, že je v prvním sloupci)
        zakazka_id = int(self.zakazka_table.model().index(row, 0).data())

        if zakazka_id is None:
            return

        # Potvrzení od uživatele
        reply = QMessageBox.question(
            self,
            "Potvrzení smazání",
            "Opravdu chceš smazat tuto zakázku včetně všech jejích položek?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Smazání z databáze
        conn = sqlite3.connect(db_address)
        cursor = conn.cursor()

        # Smaž nejdřív položky, které na zakázku odkazují
        cursor.execute("DELETE FROM položka WHERE zakazka = ?", (zakazka_id,))
        # Smaž samotnou zakázku
        cursor.execute("DELETE FROM zakázka WHERE id = ?", (zakazka_id,))
        
        conn.commit()
        conn.close()

        # Aktualizuj zobrazení
        self.zakazka_model.select()

    def add_polozka(self, row):
        """Opens a dialog to add a new polozka and saves it to the database."""
        zakazka_id = self.zakazka_model.data(self.zakazka_model.index(row, 0))

        dialog = AddPolozkaDialog(zakazka_id, self)
        if dialog.exec():
            number, title, ks = dialog.get_data()

            if not title:  # Title is required
                return

            conn = sqlite3.connect(db_address)
            cursor = conn.cursor()

            cursor.execute("INSERT INTO položka (number, title, ks, zakazka) VALUES (?, ?, ?, ?)",
                           (number if number else None, title, ks, zakazka_id))
            
            new_item_id = cursor.lastrowid

            conn.commit()
            conn.close()

            # Refresh table
            self.update_polozka_table()

            for row in range(self.polozka_filter_model.rowCount()):
                index = self.polozka_filter_model.index(row, 0)
                item_id = self.polozka_filter_model.data(index, Qt.DisplayRole)
                if item_id == new_item_id:
                    self.generate_vykres(row)  # Zavolání funkce pro generování výkresu
                    break

    def show_polozka_context_menu(self, position):
        """Shows context menu on right-click in the položka table."""
        index = self.polozka_table.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu(self)

        menu.setStyleSheet("""
            QMenu {
                background-color: #2C2C2C;
                color: white;
                border: 1px solid #444;
            }
            QMenu::item {
                background-color: transparent;
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #444;
            }
        """)
        
        action_generate_number = menu.addAction("Generovat číslo")
        action_edit_item = menu.addAction("Editovat položku")
        action_delete_polozka = menu.addAction("Smazat položku")

        # Zobrazení menu a zachycení vybrané akce
        action = menu.exec(self.polozka_table.viewport().mapToGlobal(position))

        # Akce pro "Generovat číslo"
        if action == action_generate_number:
            self.generate_vykres(index.row())
        
        # Akce pro "Editovat položku"
        elif action == action_edit_item:
            self.edit_selected_item()

        elif action == action_delete_polozka:
            self.delete_selected_polozka()


    def edit_selected_item(self):

        def get_db_connection():
            if not QSqlDatabase.contains("qt_sql_default_connection"):
                db = QSqlDatabase.addDatabase("QSQLITE")
                db.setDatabaseName(db_address)
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
        current_number = self.polozka_filter_helper.data(self.polozka_filter_helper.index(source_index.row(), 3))
        current_title = self.polozka_filter_helper.data(self.polozka_filter_helper.index(source_index.row(), 2))
        current_vykres = self.polozka_filter_helper.data(self.polozka_filter_helper.index(source_index.row(), 1))
        current_ks = self.polozka_filter_helper.data(self.polozka_filter_helper.index(source_index.row(), 7))
        current_user = self.polozka_filter_helper.data(self.polozka_filter_helper.index(source_index.row(), 8))

        dialog = EditItemDialog(self.db, polozka_id, current_number, current_title, current_vykres, current_user, current_ks, self)
        if dialog.exec():
            self.polozka_model.select()
            self.polozka_filter_helper.setQuery(self.polozka_filter_helper.query().executedQuery())  # Refresh filter model

    def generate_vykres(self, row):
        """Generuje hodnotu vykres pro položku na daném řádku, pokud ještě není vyplněna."""
        # Získání indexu vybrané položky podle řádku
        user = getpass.getuser().capitalize()
        index = self.polozka_filter_model.index(row, 0)  # Sloupec 0 je ID položky
        item_id = self.polozka_filter_model.data(index, Qt.DisplayRole)

        # Připojení k databázi
        conn = sqlite3.connect(db_address)
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
        zakazka_number = zakazka_number[0]

        zakazka_prefix = zakazka_number[:3]  # Standardní tříznakový prefix

        # Získání nejvyššího čísla pro danou skupinu zakázek
        cursor.execute("""
            SELECT vykres FROM položka 
            WHERE zakazka IN (SELECT id FROM zakázka WHERE number LIKE ?) 
            AND vykres LIKE ?
            ORDER BY vykres DESC LIMIT 1
        """, (f"{zakazka_prefix}%", f"K-{zakazka_prefix}-%"))
        
        last_vykres = cursor.fetchone()
        if last_vykres:
            # Extrahování posledního čísla
            last_number = int(last_vykres[0].split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        # Vygenerování nového čísla
        new_vykres = f"K-{zakazka_prefix}-{new_number:02d}"
        current_date = datetime.today().strftime('%d. %m. %Y')

        # Aktualizace hodnoty v databázi
        cursor.execute("UPDATE položka SET date = ?, user=?, vykres = ? WHERE id = ?", (current_date, user, new_vykres, item_id))
        conn.commit()
        conn.close()

        self.update_polozka_table()

    def delete_selected_polozka(self):
        """Deletes the selected položka from the database."""
        selected_indexes = self.polozka_table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Smazání položky", "Nevybrali jste žádnou položku k odstranění.")
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Smazání položky")
        msg_box.setText("Opravdu chcete smazat vybranou položku?")
        yes_button = msg_box.addButton("Ano", QMessageBox.YesRole)
        no_button = msg_box.addButton("Ne", QMessageBox.NoRole)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.exec()

        if msg_box.clickedButton() == yes_button:
            db = QSqlDatabase.database()
            if not db.isOpen():
                QMessageBox.critical(self, "Chyba databáze", "Databáze není otevřená!")
                return

            query = QSqlQuery(db)
            for index in selected_indexes:
                row = index.row()
                id_index = self.polozka_filter_model.index(row, 0)  # Sloupec 0 obsahuje ID
                polozka_id = self.polozka_filter_model.data(id_index)

                query.prepare("DELETE FROM položka WHERE id = ?")
                query.addBindValue(polozka_id)
                if not query.exec():
                    QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat položku: {query.lastError().text()}")
                    return

            # Obnovíme model, aby se změny zobrazily
            self.polozka_filter_helper.setQuery(self.polozka_filter_helper.query().executedQuery()) 

    def on_search_text_changed(self, text):
        """Triggered when the search input changes."""
        # Nastaví regulární výraz s textem (case insensitive)
        self.polozka_filter_model.setFilterKeyColumn(-1)
        regex = QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.polozka_filter_model.setFilterRegularExpression(regex)


    def zakazka_changed(self, selected):
        indexes = selected.indexes()
        if indexes:
            row = indexes[0].row()
            zakazka_id = self.zakazka_model.data(self.zakazka_model.index(row, 0))
            self.filter_polozky_by_zakazka(zakazka_id)
        else:
            self.filter_polozky_by_zakazka(None)

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
        conn = sqlite3.connect(db_address)
        cursor = conn.cursor()
        
        # Insert zakázka data
        zakazka_data = data['zakázka']
        try:
            cursor.execute('''
                INSERT INTO zakázka (number, title) VALUES (?, ?)
            ''', (zakazka_data[0][0], zakazka_data[1][0]))
     
            # zakazka_id = zakazka_data[0][0]  # Get zakazka nuber as foreign key
            zakazka_id = cursor.lastrowid # Get the last inserted ID for foreign key
            print (zakazka_id)
            
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
            msg_box.setText(f"Zakázka s číslem {zakazka_data[0][0]} již existuje! \nChcete přidat vybrané položky k již vytvořené zakázce?")
            yes_button = msg_box.addButton("Ano", QMessageBox.YesRole)
            no_button = msg_box.addButton("Ne", QMessageBox.NoRole)
            result = msg_box.exec()

            if msg_box.clickedButton() == yes_button:
                zakazka_number = zakazka_data[0][0]
                cursor.execute("SELECT id FROM zakázka WHERE number = ?", (zakazka_number,))
                result = cursor.fetchone()
                if result:  # Ověření, zda byl nalezen výsledek
                    zakazka_id = result[0]  # Získání id z n-tice
                else:
                    zakazka_id = None  # Pokud žádný záznam neexistuje
                
                # Insert položka data
                for item in data['položky']:
                    cursor.execute('''
                        INSERT INTO položka (number, title, ks, zakazka) 
                        VALUES (?, ?, ?, ?)
                    ''', (item[0][0], item[1][0], item[2][0], zakazka_id))
            
                conn.commit()

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
            conn = sqlite3.connect(db_address)
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
    app.setStyleSheet("""
        QWidget {
            background-color: #1c1c1c;
            color: white;
        }
        QPushButton {
            background-color: #444;
            color: white;
            border: 1px solid #666;
            padding: 5px 10px;
            border-radius: 4px;
        }

        QPushButton:hover {
            background-color: #555;
        }

        QPushButton:pressed {
            background-color: #333;
        }

        QPushButton:disabled {
            background-color: #222;
            color: #888;
        }
        QTableView { 
            alternate-background-color: #2C2C2C; 
            background-color: #3b3b3b; 
            selection-background-color: #89CFF0;
            selection-color: #3b3b3b;
            color: white;
            border: none;
        }
        QHeaderView::section {
            background-color: #444;
            color: white;
        }
        QFrame {
            background-color: #2C2C2C;
            border: none;
        }
        QLabel {
            background-color: transparent;              
                      
        }
        QScrollBar:vertical {
            background: transparent;
            width: 12px;
            margin: 0px;
        }

        QScrollBar::handle:vertical {
            background: #666;
            min-height: 20px;
            border-radius: 4px;
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            background: none;
            height: 0px;
        }
        QScrollBar::add-page:vertical, 
        QScrollBar::sub-page:vertical {
            background: #2C2C2C;  /* Tady nastavíš čistou barvu tracku */
        }
        """)
    app.setWindowIcon(QIcon("J:/Vývoj/helpers/logo.ico"))
    window = NumberingOfDesignDocumentation()
    window.setWindowTitle("Konstrukční dokumentace")
    window.show()
    sys.exit(app.exec())