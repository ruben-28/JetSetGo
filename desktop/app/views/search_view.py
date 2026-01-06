from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox
)

class SearchView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JetsetGo - Recherche")
        self.setMinimumSize(900, 520)

        root = QVBoxLayout(self)

        # --- Form ---
        form = QHBoxLayout()
        root.addLayout(form)

        self.destination = QLineEdit()
        self.destination.setPlaceholderText("Destination (ex: Paris)")

        self.depart_date = QLineEdit()
        self.depart_date.setPlaceholderText("Départ YYYY-MM-DD")

        self.return_date = QLineEdit()
        self.return_date.setPlaceholderText("Retour YYYY-MM-DD")

        self.budget = QLineEdit()
        self.budget.setPlaceholderText("Budget (ex: 600)")

        self.search_btn = QPushButton("Rechercher")

        form.addWidget(QLabel("Destination"))
        form.addWidget(self.destination)
        form.addWidget(QLabel("Départ"))
        form.addWidget(self.depart_date)
        form.addWidget(QLabel("Retour"))
        form.addWidget(self.return_date)
        form.addWidget(QLabel("Budget"))
        form.addWidget(self.budget)
        form.addWidget(self.search_btn)

        # --- Results Table ---
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Compagnie", "Prix", "Durée", "Escales", "Score"])
        self.table.setSortingEnabled(True)
        root.addWidget(self.table)

        # --- Details button ---
        bottom = QHBoxLayout()
        root.addLayout(bottom)

        self.details_btn = QPushButton("Voir détails")
        self.details_btn.setEnabled(False)
        bottom.addWidget(self.details_btn)

        self.status = QLabel("")
        bottom.addWidget(self.status)

        self.table.itemSelectionChanged.connect(self._on_select)

    def _on_select(self):
        self.details_btn.setEnabled(len(self.table.selectedItems()) > 0)

    def set_status(self, txt: str):
        self.status.setText(txt)

    def show_error(self, message: str):
        QMessageBox.critical(self, "Erreur", message)

    def show_info(self, message: str):
        QMessageBox.information(self, "Info", message)

    def set_offers(self, offers: list):
        self.table.setRowCount(0)
        for o in offers:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(o["id"]))
            self.table.setItem(row, 1, QTableWidgetItem(o["airline"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(o["price"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(o["duration_min"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(o["stops"])))
            self.table.setItem(row, 5, QTableWidgetItem(str(o["score"])))
