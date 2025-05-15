from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QMessageBox, QInputDialog
)
import csv
import os
from state import GlobalState

class ProjectsTab(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Таблица проектов
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Название", "Описание", "Статус"])
        self.layout.addWidget(self.table)

        # Кнопки управления
        buttons_layout = QHBoxLayout()

        self.add_button = QPushButton("Добавить проект")
        self.add_button.clicked.connect(self.add_project)
        buttons_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Редактировать")
        self.edit_button.clicked.connect(self.edit_project)
        buttons_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_project)
        buttons_layout.addWidget(self.delete_button)

        self.toggle_status_button = QPushButton("Изменить статус")
        self.toggle_status_button.clicked.connect(self.toggle_status)
        buttons_layout.addWidget(self.toggle_status_button)

        self.layout.addLayout(buttons_layout)

    def on_workspace_changed(self, path):
        self.load_projects()

    def get_projects_path(self):
        if not GlobalState.current_workspace_path:
            return None
        return os.path.join(GlobalState.current_workspace_path, "projects.csv")

    def load_projects(self):
        self.table.setRowCount(0)
        path = self.get_projects_path()
        if not path or not os.path.exists(path):
            return

        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row_data in reader:
                row = self.table.rowCount()
                self.table.insertRow(row)
                for col, value in enumerate(row_data):
                    self.table.setItem(row, col, QTableWidgetItem(value))

    def save_projects(self):
        path = self.get_projects_path()
        if not path:
            return

        with open(path, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for row in range(self.table.rowCount()):
                data = [self.table.item(row, col).text() for col in range(self.table.columnCount())]
                writer.writerow(data)

    def add_project(self):
        name, ok = QInputDialog.getText(self, "Название проекта", "Введите название проекта:")
        if not ok or not name.strip():
            return

        description, ok = QInputDialog.getText(self, "Описание", "Введите описание проекта:")
        if not ok:
            return

        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(name.strip()))
        self.table.setItem(row, 1, QTableWidgetItem(description.strip()))
        self.table.setItem(row, 2, QTableWidgetItem("Активен"))

        self.save_projects()

    def edit_project(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Выбор проекта", "Выберите проект для редактирования.")
            return

        current_name = self.table.item(row, 0).text()
        current_desc = self.table.item(row, 1).text()

        new_name, ok = QInputDialog.getText(self, "Редактировать название", "Новое название:", text=current_name)
        if not ok:
            return

        new_desc, ok = QInputDialog.getText(self, "Редактировать описание", "Новое описание:", text=current_desc)
        if not ok:
            return

        self.table.setItem(row, 0, QTableWidgetItem(new_name))
        self.table.setItem(row, 1, QTableWidgetItem(new_desc))

        self.save_projects()

    def delete_project(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Удаление проекта", "Выберите проект для удаления.")
            return

        self.table.removeRow(row)
        self.save_projects()

    def toggle_status(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Статус проекта", "Выберите проект для смены статуса.")
            return

        current = self.table.item(row, 2).text()
        new_status = "Завершён" if current == "Активен" else "Активен"
        self.table.setItem(row, 2, QTableWidgetItem(new_status))

        self.save_projects()
