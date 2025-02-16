from PySide6.QtWidgets import (QDialog, QLineEdit, QFormLayout, QDialogButtonBox)

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
    