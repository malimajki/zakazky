from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtSql import QSqlQuery
from datetime import datetime
import getpass

class EditItemDialog(QDialog):
    def __init__(self, db, polozka_id, number, title, vykres, user, ks, parent=None):
        super().__init__(parent)
        self.db = db
        self.polozka_id = polozka_id

        self.setWindowTitle("Editace položky")
        self.setFixedSize(300, 320)

        layout = QVBoxLayout()

        self.input_number = QLineEdit(str(number))
        self.input_title = QLineEdit(str(title))
        self.input_vykres = QLineEdit(str(vykres))
        self.input_ks = QLineEdit(str(ks))
        self.input_user = QLineEdit(str(user))

        layout.addWidget(QLabel("Číslo položky:"))
        layout.addWidget(self.input_number)
        layout.addWidget(QLabel("Název:"))
        layout.addWidget(self.input_title)
        layout.addWidget(QLabel("Výkres:"))
        layout.addWidget(self.input_vykres)
        layout.addWidget(QLabel("Počet kusů:"))
        layout.addWidget(self.input_ks)
        layout.addStretch()

        self.button_ok = QPushButton("Uložit")
        self.button_cancel = QPushButton("Zrušit")
        
        layout.addWidget(self.button_ok)
        layout.addWidget(self.button_cancel)
        self.setLayout(layout)

        self.button_cancel.clicked.connect(self.reject)
        self.button_ok.clicked.connect(self.save_changes)

    def save_changes(self):
        new_number = self.input_number.text()
        new_title = self.input_title.text()
        new_vykres = self.input_vykres.text()
        new_ks = self.input_ks.text()
        current_date = datetime.today().strftime('%d. %m. %Y')
        new_user = self.input_user.text()

        if new_vykres == "":
            new_vykres = None
            current_date = None
            new_user = ""
        
        if not new_user and new_vykres:
            new_user = getpass.getuser().capitalize()

        query = QSqlQuery(self.db)
        query.prepare("UPDATE položka SET number = ?, title = ?, vykres = ?, ks = ?, user=?, date=? WHERE id = ?")
        query.addBindValue(new_number)
        query.addBindValue(new_title)
        query.addBindValue(new_vykres)
        query.addBindValue(new_ks)
        query.addBindValue(new_user)
        query.addBindValue(current_date)
        query.addBindValue(self.polozka_id)

        if query.exec():
            self.accept()
        else:
            QMessageBox.critical(self, "Chyba", "Nepodařilo se uložit změny.")
