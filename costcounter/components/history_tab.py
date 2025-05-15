from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QMessageBox
)
import os
import csv
from state import GlobalState

class HistoryTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel("История расчетов")
        self.layout.addWidget(self.label)

        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        self.load_data()

    def load_data(self):
        self.table.clear()
        if not GlobalState.current_workspace_path:
            return

        path = os.path.join(GlobalState.current_workspace_path, "cost_history.csv")
        if not os.path.exists(path):
            return

        try:
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if not rows:
                    return

                headers = rows[0]
                self.table.setColumnCount(len(headers))
                self.table.setRowCount(len(rows) - 1)
                self.table.setHorizontalHeaderLabels(headers)

                for row_idx, row_data in enumerate(rows[1:]):
                    for col_idx, cell in enumerate(row_data):
                        self.table.setItem(row_idx, col_idx, QTableWidgetItem(cell))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить историю: {e}")

    def on_workspace_changed(self, path):
        self.load_data()
