from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLineEdit, QPushButton, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QSplitter, QMenu, 
                               QInputDialog, QMessageBox, QLabel, QDialog)
from PySide6.QtGui import (QAction, QStandardItem)
from PySide6.QtCore import Qt
import sqlite3

from nova_polozka_dialog import NovaPolozkaDialog
from nova_zakazka_dialog import NovaZakazkaDialog
from pdf2data import extract_data_from_pdf
from init_db import init_db

class ZakazkyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Správa zakázek a položek")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowState(Qt.WindowMaximized)

        # Hlavní widget a layout
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        
        # Ovládací část
        ovladaci_cast = QWidget()
        ovladaci_layout = QVBoxLayout(ovladaci_cast)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Vyhledávání v položkách...")
        self.search_input.textChanged.connect(self.vyhledej_polozky)
        self.new_order_button = QPushButton("Nová zakázka")
        self.new_order_button.clicked.connect(self.vytvorit_zakazku)
        
        ovladaci_layout.addWidget(self.search_input)
        ovladaci_layout.addWidget(self.new_order_button)
        
        # Tabulka zakázek
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(2)
        self.orders_table.setHorizontalHeaderLabels(["Název zakázky", "Číslo zakázky"])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.orders_table.setSelectionBehavior(QTableWidget.SelectRows)

        self.orders_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.orders_table.customContextMenuRequested.connect(self.open_context_menu)
        self.orders_table.itemSelectionChanged.connect(self.nacti_polozky)
        
        # Tabulka položek
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["Číslo", "Název", "Počet kusů", "Zakázka", "Výkres"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Layout rozdělený na 3 části pomocí QSplitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(ovladaci_cast)
        splitter.addWidget(self.orders_table)
        splitter.addWidget(self.items_table)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 4)
        
        main_layout.addWidget(splitter)
        
        self.setCentralWidget(main_widget)

        self.nacti_zakazky()

    def nacti_zakazky(self):
        self.orders_table.setRowCount(0)
        conn = sqlite3.connect('zakazky.db')
        cursor = conn.cursor()
        cursor.execute("SELECT nazev, cislo FROM zakazky")
        zakazky = cursor.fetchall()
        for row_number, row_data in enumerate(zakazky):
            self.orders_table.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.orders_table.setItem(row_number, column_number, QTableWidgetItem(str(data)))
        conn.close()
    
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
            conn = sqlite3.connect('zakazky.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM zakazky WHERE cislo = ?", (cislo,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(self, "Duplicitní číslo", "Zakázka s tímto číslem již existuje.")
                conn.close()
                return
            
            # Uložení nové zakázky do databáze
            cursor.execute("INSERT INTO zakazky (nazev, cislo) VALUES (?, ?)", (nazev, cislo))
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Zakázka vytvořena", f"Zakázka '{nazev}' byla vytvořena.")
            
            # Aktualizace tabulky zakázek
            self.nacti_zakazky()

    def nacti_polozky(self):
        self.items_table.setRowCount(0)
        
        # Získání vybrané zakázky
        vybrany_radek = self.orders_table.currentRow()
        if vybrany_radek == -1:
            return
        
        zakazka_nazev = self.orders_table.item(vybrany_radek, 0).text()
        
        # Načtení položek podle vybrané zakázky
        conn = sqlite3.connect('zakazky.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.cislo, p.nazev, p.pocet_kusu, z.nazev 
            FROM polozky p
            JOIN zakazky z ON p.zakazka_id = z.id
            WHERE z.nazev = ?
        """, (zakazka_nazev,))
        
        polozky = cursor.fetchall()
        for row_number, row_data in enumerate(polozky):
            self.items_table.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.items_table.setItem(row_number, column_number, QTableWidgetItem(str(data)))
        
        conn.close()
    
    def open_context_menu(self, pos):
        menu = QMenu()
        pridat_polozku = QAction("Vytvořit položku", self)
        pridat_polozku.triggered.connect(self.vytvorit_polozku)
        pridat_podsestavu = QAction("Vytvořit podsestavu", self)
        pridat_podsestavu.triggered.connect(self.vytvorit_podsestavu)
        menu.addAction(pridat_polozku)
        menu.addAction(pridat_podsestavu)
        menu.exec(self.orders_table.mapToGlobal(pos))
    
    def vytvorit_polozku(self):
        # Získání vybrané zakázky
        vybrany_radek = self.orders_table.currentRow()
        if vybrany_radek == -1:
            QMessageBox.warning(self, "Nevybrána zakázka", "Nejprve vyberte zakázku.")
            return
        
        zakazka_nazev = self.orders_table.item(vybrany_radek, 0).text()
        
        # Získání ID zakázky
        conn = sqlite3.connect('zakazky.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM zakazky WHERE nazev = ?", (zakazka_nazev,))
        zakazka_id = cursor.fetchone()[0]
        conn.close()
        
        # Otevření dialogu pro novou položku
        dialog = NovaPolozkaDialog(self)
        if dialog.exec() == QDialog.Accepted:
            cislo, nazev, pocet_kusu = dialog.get_data()
            
            # Kontrola vyplnění všech polí
            if not cislo or not nazev or not pocet_kusu:
                QMessageBox.warning(self, "Neplatné údaje", "Vyplňte prosím všechna pole.")
                return
            
            # Uložení nové položky do databáze
            conn = sqlite3.connect('zakazky.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO polozky (cislo, nazev, pocet_kusu, zakazka_id) VALUES (?, ?, ?, ?)",
                           (cislo, nazev, int(pocet_kusu), zakazka_id))
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Položka vytvořena", f"Položka '{nazev}' byla vytvořena.")
            
            # Aktualizace tabulky položek
            self.nacti_polozky()

    def vytvorit_podsestavu(self, index):
        # Získání ID zakázky
        row = index.row()
        zakazka_id = self.orders_model.index(row, 0).data()
        
        # Dialog pro zadání názvu podsestavy
        nazev, ok = QInputDialog.getText(self, "Vytvořit podsestavu", "Název podsestavy:")
        
        if ok and nazev.strip():
            nazev = nazev.strip()
            
            # Automatické číslo a počet kusů
            cislo = f"PS-{zakazka_id}-{int(time.time())}"
            pocet = 1
            
            # Vložení do databáze
            self.cursor.execute("""
                INSERT INTO polozky (cislo, nazev, pocet, zakazka_id, vykres, poznamky, cas_vytvoreni)
                VALUES (?, ?, ?, ?, '', '', datetime('now'))
            """, (cislo, nazev, pocet, zakazka_id))
            self.conn.commit()
            
            # Aktualizace tabulky položek
            self.nacti_polozky(zakazka_id)

    def vyhledej_polozky(self, text):
        """Triggered when the search input changes."""
        self.polozka_filter_model.setFilterFixedString(text)



if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = ZakazkyApp()
    window.show()
    sys.exit(app.exec())