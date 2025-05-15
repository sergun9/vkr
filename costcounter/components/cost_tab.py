from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QFormLayout, QHBoxLayout, QCompleter,
    QLineEdit, QPushButton, QMessageBox, QScrollArea, QFrame, QComboBox
)
from PyQt5.QtCore import QDateTime
import os
import csv
from state import GlobalState
from components.utils import load_references


class CostTab(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.inputs = []
        

        # Выбор проекта
        self.project_selector = QComboBox()
        self.project_selector.setEditable(True)
        self.layout.addWidget(QLabel("Выберите проект:"))
        self.layout.addWidget(self.project_selector)
        self.project_description_label = QLabel("")
        self.project_description_label.setStyleSheet("font-style: italic; color: gray;")
        self.layout.addWidget(self.project_description_label)

        self.project_selector.currentTextChanged.connect(self.update_project_description)

        self.load_projects()

        # Кнопки управления
        self.control_layout = QHBoxLayout()
        self.add_button = QPushButton("Добавить строку")
        self.add_button.clicked.connect(self.add_row)
        self.control_layout.addWidget(self.add_button)

        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_data)
        self.control_layout.addWidget(self.save_button)

        self.layout.addLayout(self.control_layout)

        # Скроллируемая зона для форм
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.form_container = QWidget()
        self.form_layout = QFormLayout()
        self.form_container.setLayout(self.form_layout)
        self.scroll_area.setWidget(self.form_container)
        self.layout.addWidget(self.scroll_area)

        self.total_label = QLabel("Итого: 0.00")
        self.layout.addWidget(self.total_label)

        # Инициализация с одной строкой
        #self.add_row()
        self.apply_defaults_button = QPushButton("Подставить типовые значения")
        self.apply_defaults_button.clicked.connect(self.apply_default_values)
        self.layout.addWidget(self.apply_defaults_button)


    def add_row(self, label_text=None, value_text=None):
        row_layout = QHBoxLayout()
        label_input = QLineEdit()
        label_input.setPlaceholderText("Название статьи")
        label_input.setText(label_text if isinstance(label_text, str) else "")

        value_input = QLineEdit()
        value_input.setPlaceholderText("0.00")
        value_input.setText(value_text)

        # Автодополнение из справочников
        label_input.textChanged.connect(lambda text, value_edit=value_input: self.on_article_changed(text, value_edit))
        completer = QCompleter(GlobalState.references)
        completer.setCaseSensitivity(False)
        label_input.setCompleter(completer)

        value_input.textChanged.connect(self.recalculate_total)

        delete_button = QPushButton("✕")
        delete_button.setFixedWidth(30)
        delete_button.clicked.connect(lambda: self.remove_row(row_layout))

        row_layout.addWidget(label_input)
        row_layout.addWidget(value_input)
        row_layout.addWidget(delete_button)

        container = QFrame()
        container.setLayout(row_layout)
        self.form_layout.addRow(container)

        self.inputs.append((container, label_input, value_input))

        self.recalculate_total()


    def remove_row(self, layout_to_remove):
        to_remove = None

        for container, label_input, value_input in self.inputs:
            if container.layout() == layout_to_remove:
                to_remove = (container, label_input, value_input)
                break

        if to_remove:
            container, label_input, value_input = to_remove
            self.form_layout.removeWidget(container)
            container.deleteLater()
            self.inputs.remove(to_remove)

        self.recalculate_total()





    def recalculate_total(self):
        base_total = 0.0
        parsed_inputs = []

        # Сначала собираем абсолютные значения
        for _, label_input, value_input in self.inputs:
            text = value_input.text().strip().replace(",", ".")
            if text.endswith("%"):
                parsed_inputs.append(('percent', text, value_input))
            else:
                try:
                    value = float(text)
                    parsed_inputs.append(('absolute', value, value_input))
                    base_total += value
                except ValueError:
                    parsed_inputs.append(('invalid', 0.0, value_input))

        total = base_total

        # Потом добавляем процентные значения
        for kind, val, _ in parsed_inputs:
            if kind == 'percent':
                try:
                    percent_value = float(val.strip('%'))
                    calculated = base_total * percent_value / 100
                    total += calculated
                except ValueError:
                    continue

        self.total_label.setText(f"Итого: {total:,.2f}")



    def save_data(self):
        if not GlobalState.current_workspace_path:
            QMessageBox.warning(self, "Ошибка", "Не выбрано рабочее пространство.")
            return

        selected_project = self.project_selector.currentText().strip()
        if not selected_project:
            QMessageBox.warning(self, "Ошибка", "Выберите проект перед сохранением.")
            return

        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        current_data = {}
        base_total = 0.0
        percent_entries = []

        # Сначала считаем абсолютные значения
        for _, label_input, value_input in self.inputs:
            label = label_input.text().strip() or "Без названия"
            raw_text = value_input.text().strip().replace(",", ".")

            if raw_text.endswith("%"):
                percent_entries.append((label, raw_text))
            else:
                try:
                    value = float(raw_text)
                except ValueError:
                    value = 0.0
                current_data[label] = value
                base_total += value

        # Теперь добавляем процентные значения
        for label, raw_text in percent_entries:
            try:
                percent = float(raw_text.rstrip('%'))
                value = base_total * percent / 100
            except ValueError:
                value = 0.0
            current_data[label] = value
            current_data[label + " (процент)"] = raw_text  # сохраняем % строкой

        total = sum(v for v in current_data.values() if isinstance(v, (int, float)))
        current_data["Итого"] = total
        current_data["Проект"] = selected_project

        history_path = os.path.join(GlobalState.current_workspace_path, "cost_history.csv")

        all_data = []
        existing_headers = set()
        if os.path.exists(history_path):
            with open(history_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    all_data.append(row)
                    existing_headers.update(row.keys())

        new_row = {"Дата": timestamp}
        new_row.update(current_data)
        all_data.append(new_row)
        existing_headers.update(new_row.keys())

        ordered_headers = (
            ["Дата", "Проект"] +
            sorted(h for h in existing_headers if h not in ["Дата", "Итого", "Проект"]) +
            ["Итого"]
        )

        with open(history_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=ordered_headers)
            writer.writeheader()
            for row in all_data:
                writer.writerow({h: row.get(h, "") for h in ordered_headers})

        self.load_projects()
        QMessageBox.information(self, "Сохранено", "Данные успешно сохранены.")






    def on_workspace_changed(self, path):
        # Очистка всех полей при смене пространства
        while self.form_layout.rowCount():
            self.form_layout.removeRow(0)
        self.inputs.clear()
        self.total_label.setText("Итого: 0.00")
        self.add_row()
        self.load_last_entry() 
        self.load_projects()

        # Загрузка проектов из файла, если есть
        projects_path = os.path.join(path, "projects.csv")
        self.project_selector.clear()
        if os.path.exists(projects_path):
            with open(projects_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and len(row) >= 1:
                        self.project_selector.addItem(row[0].strip())
        
        load_references()



    def load_last_entry(self):
        history_path = os.path.join(GlobalState.current_workspace_path, "cost_history.csv")
        if not os.path.exists(history_path):
            return

        try:
            with open(history_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if not rows:
                    return
                last_row = rows[-1]

            # Удалим всё старое
            while self.form_layout.rowCount():
                self.form_layout.removeRow(0)
            self.inputs.clear()

            # Загружаем значения из последней строки
            for key, value in last_row.items():
                if key in ["Дата", "Итого", "Проект"] or " (процент)" in key:
                    continue

                percent_key = key + " (процент)"
                if percent_key in last_row and last_row[percent_key].strip().endswith("%"):
                    value_str = last_row[percent_key].strip()
                else:
                    try:
                        value_str = f"{float(value):.2f}"
                    except (ValueError, TypeError):
                        value_str = "0.00"

                self.add_row(label_text=key, value_text=value_str)

                try:
                    value_str = f"{float(value):.2f}"
                except (ValueError, TypeError):
                    value_str = "0.00"

        except Exception as e:
            QMessageBox.warning(self, "Ошибка загрузки", f"Не удалось загрузить последний расчёт: {e}")


    def load_projects(self):
        self.project_selector.clear()
        if not GlobalState.current_workspace_path:
            return

        projects_path = os.path.join(GlobalState.current_workspace_path, "projects.csv")
        if os.path.exists(projects_path):
            with open(projects_path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and len(row) >= 1:
                        self.project_selector.addItem(row[0].strip())



    def update_project_description(self):
        project_name = self.project_selector.currentText().strip()
        projects_path = os.path.join(GlobalState.current_workspace_path, "projects.csv")

        if not os.path.exists(projects_path):
            self.project_description_label.setText("")
            return

        with open(projects_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip() == project_name:
                    description = row[1] if len(row) > 1 else ""
                    self.project_description_label.setText(f"Описание: {description}")
                    return

        self.project_description_label.setText("")


    def on_article_changed(self, text, value_edit):
        references = GlobalState.references
        print(f"DEBUG: references type = {type(references)}, content = {references}")  # <-- добавь это
        if text in references:
            value = references[text]
            if not value_edit.text().strip():
                value_edit.setText(str(value))



    def apply_default_values(self):
        """
        Применяет типовые значения ко всем строкам, где название совпадает со справочником.
        """
        for container, label_input, value_input in self.inputs:
            layout = container.layout()
            if layout.count() < 3:
                continue
            line_edit = layout.itemAt(0).widget()
            value_edit = layout.itemAt(1).widget()
            
            if isinstance(line_edit, QLineEdit) and isinstance(value_edit, QLineEdit):
                text = line_edit.text()
                clean_text = text.strip()
                if clean_text in GlobalState.references:
                    if not value_edit.text().strip():
                        value_edit.setText(str(GlobalState.references[clean_text]))

