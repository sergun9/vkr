from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QLineEdit, QFormLayout, QFrame, QMessageBox
)
import os
import csv
from state import GlobalState


class ReferencesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.entries = []

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.unsaved_changes = False

        # Кнопки управления
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Добавить запись")
        self.add_button.clicked.connect(lambda: self.add_entry())  # фикс ошибки
        self.save_button = QPushButton("Сохранить справочник")
        self.save_button.clicked.connect(self.save_references)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

        # Скроллируемая зона для записей
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.form_container = QWidget()
        self.form_layout = QFormLayout()
        self.form_container.setLayout(self.form_layout)
        self.scroll_area.setWidget(self.form_container)
        layout.addWidget(self.scroll_area)

    def add_entry(self, name="", value=""):
        row_layout = QHBoxLayout()
        name_input = QLineEdit()
        name_input.setPlaceholderText("Название статьи")
        name_input.setText(name)

        value_input = QLineEdit()
        value_input.setPlaceholderText("Типовое значение (можно %) или число")
        value_input.setText(value)

        delete_button = QPushButton("✕")
        delete_button.setFixedWidth(30)
        container = QFrame()
        container.setLayout(row_layout)

        delete_button.clicked.connect(lambda: self.remove_entry(container))

        row_layout.addWidget(name_input)
        row_layout.addWidget(value_input)
        row_layout.addWidget(delete_button)

        name_input.textChanged.connect(self.mark_unsaved)
        value_input.textChanged.connect(self.mark_unsaved)

        self.form_layout.addRow(container)
        self.entries.append((container, name_input, value_input))

    def remove_entry(self, container):
        for entry in self.entries:
            if entry[0] == container:
                self.form_layout.removeWidget(container)
                container.deleteLater()
                self.entries.remove(entry)
                break

    def save_references(self):
        if not GlobalState.current_workspace_path:
            QMessageBox.warning(self, "Ошибка", "Не выбрано рабочее пространство.")
            return

        if not any(name_input.text().strip() and value_input.text().strip() for _, name_input, value_input in self.entries):
            QMessageBox.warning(self, "Пусто", "Невозможно сохранить пустой справочник.")
            return

        path_items = os.path.join(GlobalState.current_workspace_path, "reference_items.csv")

        GlobalState.references = {}  # Теперь словарь!

        with open(path_items, "w", newline="", encoding="utf-8") as f_items:
            writer_items = csv.writer(f_items)
            writer_items.writerow(["Название", "Значение"])

            for _, name_input, value_input in self.entries:
                name = name_input.text().strip()
                value = value_input.text().strip()
                if name and value:
                    writer_items.writerow([name, value])
                    GlobalState.references[name] = value  # Записываем в словарь!

        QMessageBox.information(self, "Сохранено", "Справочник успешно сохранён.")

        self.unsaved_changes = False


    def on_workspace_changed(self, path):
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, "Несохранённые изменения",
                "У вас есть несохранённые изменения в справочнике. Хотите сохранить их?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Yes:
                self.save_references()
            elif reply == QMessageBox.Cancel:
                return  # Отменить смену рабочего пространства

        # Очистить текущие поля
        while self.form_layout.rowCount():
            self.form_layout.removeRow(0)
        self.entries.clear()

        if not path:
            return

        file_path = os.path.join(path, "reference_items.csv")
        GlobalState.references = {}

        if os.path.exists(file_path):
            with open(file_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get('Название', '').strip()
                    value = row.get('Значение', '').strip()
                    if name:
                        self.add_entry(name=name, value=value)
                        GlobalState.references[name] = value  # <-- Всё остаётся, просто можно чутка отделить заполнение и загрузку


    def mark_unsaved(self):
        self.unsaved_changes = True
