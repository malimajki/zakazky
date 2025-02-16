from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QDialog)

class NovaZakazkaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nová zakázka")
        
        # Layouty
        layout = QVBoxLayout()
        
        # Pole pro název
        self.nazev_input = QLineEdit()
        self.nazev_input.setPlaceholderText("Název zakázky")
        layout.addWidget(QLabel("Název zakázky:"))
        layout.addWidget(self.nazev_input)
        
        # Pole pro číslo
        self.cislo_input = QLineEdit()
        self.cislo_input.setPlaceholderText("Číslo zakázky")
        layout.addWidget(QLabel("Číslo zakázky:"))
        layout.addWidget(self.cislo_input)
        
        # Tlačítka OK a Zrušit
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Zrušit")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def get_data(self):
        return self.nazev_input.text(), self.cislo_input.text()