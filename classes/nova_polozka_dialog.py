from PySide6.QtWidgets import (QDialog, QLineEdit, QFormLayout, QSpinBox, QDialogButtonBox)

class AddPolozkaDialog(QDialog):
    """Dialog window for adding a new položka."""
    def __init__(self, zakazka_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Přidat novou položku")
        self.zakazka_id = zakazka_id

        layout = QFormLayout()

        self.number_input = QLineEdit()
        self.number_input.setPlaceholderText("Číslo položky")

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Název")

        self.ks_input = QSpinBox()
        self.ks_input.setMinimum(1)

        layout.addRow("Číslo položky:", self.number_input)
        layout.addRow("Název:", self.title_input)
        layout.addRow("Ks:", self.ks_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)

        ok_button.setText("Vytvořit")
        cancel_button.setText("Zrušit")

        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_data(self):
        """Returns the entered data."""
        return self.number_input.text().strip(), self.title_input.text().strip(), self.ks_input.value()
    