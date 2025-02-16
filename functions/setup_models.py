from PySide6.QtWidgets import  QAbstractItemView
from PySide6.QtSql import QSqlDatabase, QSqlTableModel, QSqlRelationalTableModel, QSqlRelationalDelegate, QSqlRelation
from PySide6.QtCore import QSortFilterProxyModel, Qt

def setup_models_call(self):
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
        self.polozka_model = QSqlRelationalTableModel(self, db)
        self.polozka_model.setTable("položka")

        self.polozka_model.setRelation(4, QSqlRelation("zakázka", "id", "title"))

        self.polozka_model.select()  # Load the data

        # Set headers
        self.polozka_model.setHeaderData(1, Qt.Orientation.Horizontal, "Číslo")
        self.polozka_model.setHeaderData(2, Qt.Orientation.Horizontal, "Název")
        self.polozka_model.setHeaderData(3, Qt.Orientation.Horizontal, "Ks")
        self.polozka_model.setHeaderData(4, Qt.Orientation.Horizontal, "Zakázka")
        self.polozka_model.setHeaderData(5, Qt.Orientation.Horizontal, "Výkres")

        # Assign to table
        self.polozka_table.setModel(self.polozka_model)
        self.polozka_table.setItemDelegate(QSqlRelationalDelegate(self.polozka_table))  # Enables dropdown for relations
        self.polozka_table.hideColumn(0)
        self.polozka_table.hideColumn(6)
        self.polozka_table.setSortingEnabled(True)
        self.polozka_table.sortByColumn(5, Qt.DescendingOrder)
        self.polozka_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.polozka_table.verticalHeader().setVisible(False)
        self.polozka_table.setColumnWidth(1, 70)
        self.polozka_table.setColumnWidth(2, 350)
        self.polozka_table.setColumnWidth(3, 30)
        self.polozka_table.setColumnWidth(4, 150)
        self.polozka_table.setColumnWidth(5, 80)

        # Proxy model for filtering polozka
        self.polozka_filter_model = QSortFilterProxyModel(self)
        self.polozka_filter_model.setSourceModel(self.polozka_model)
        self.polozka_filter_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.polozka_filter_model.setFilterKeyColumn(-1)  # Filter based on the zakazka_number (4th column in the polozka table
        self.polozka_filter_model.setFilterFixedString("")  # No filter initially

        self.polozka_table.setModel(self.polozka_filter_model)