from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QFrame, 
    QLabel, QMessageBox, QComboBox, QHBoxLayout, QDateEdit, QPushButton, 
    QFileDialog, QScrollArea
)
from PyQt5.QtCore import QDate, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from collections import defaultdict
from datetime import datetime
from statistics import mean, median
import os
import csv
import numpy as np
from state import GlobalState


class AnalysisTab(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel("<h2>Анализ сохранённых расчётов</h2>")
        self.layout.addWidget(self.label)

        self.pie_canvas = FigureCanvas(Figure(figsize=(5, 4)))
        self.bar_canvas = FigureCanvas(Figure(figsize=(8, 4)))
        self.stats_canvas = FigureCanvas(Figure(figsize=(8, 4)))

        filters_layout = QHBoxLayout()
        self.project_filter = QComboBox()
        self.project_filter.addItem("Все проекты")
        self.project_filter.currentIndexChanged.connect(self.update_display)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.dateChanged.connect(self.update_display)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.dateChanged.connect(self.update_display)

        filters_layout.addWidget(QLabel("Проект:"))
        filters_layout.addWidget(self.project_filter)
        filters_layout.addWidget(QLabel("с"))
        filters_layout.addWidget(self.date_from)
        filters_layout.addWidget(QLabel("по"))
        filters_layout.addWidget(self.date_to)

        self.save_pie_button = QPushButton("Сохранить круговую диаграмму")
        self.save_bar_button = QPushButton("Сохранить график по датам")
        self.save_pie_button.clicked.connect(self.save_pie_chart)
        self.save_bar_button.clicked.connect(self.save_bar_chart)

        

        self.export_button = QPushButton("Экспортировать отчёт в CSV")
        self.export_button.clicked.connect(self.export_report)

        # Контейнер для всех графиков в одну строку с прокруткой
        charts_scroll_area = QScrollArea()
        charts_scroll_area.setWidgetResizable(True)
        charts_container = QWidget()
        charts_layout = QHBoxLayout()

        # Круговая диаграмма
        pie_frame = QFrame()
        pie_frame.setFrameShape(QFrame.StyledPanel)
        pie_layout = QVBoxLayout()
        pie_layout.addWidget(self.pie_canvas)
        pie_frame.setLayout(pie_layout)

        # График по датам
        bar_frame = QFrame()
        bar_frame.setFrameShape(QFrame.StyledPanel)
        bar_layout = QVBoxLayout()
        bar_layout.addWidget(self.bar_canvas)
        bar_frame.setLayout(bar_layout)

        # Статистика
        stats_frame = QFrame()
        stats_frame.setFrameShape(QFrame.StyledPanel)
        stats_layout = QVBoxLayout()
        stats_layout.addWidget(self.stats_canvas)
        stats_frame.setLayout(stats_layout)

        charts_layout.addWidget(pie_frame)
        charts_layout.addWidget(bar_frame)
        charts_layout.addWidget(stats_frame)

        charts_container.setLayout(charts_layout)
        charts_scroll_area.setWidget(charts_container)
        charts_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        charts_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.save_pie_button)
        buttons_layout.addWidget(self.save_bar_button)
        buttons_layout.addWidget(self.export_button)

        buttons_container = QWidget()
        buttons_container.setLayout(buttons_layout)
        buttons_container.setContentsMargins(0, 10, 0, 10)
        buttons_layout.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(buttons_container)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.layout.addWidget(self.summary_label)

        self.layout.addLayout(filters_layout)

        self.table = QTableWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.table)
        self.layout.addWidget(scroll)
        self.layout.addWidget(charts_scroll_area)


        self.all_data = []
        self.current_path = ""

    def on_workspace_changed(self, path):
        self.current_path = path
        self.all_data.clear()
        self.project_filter.clear()
        self.project_filter.addItem("Все проекты")
        self.table.clearContents()
        self.table.setRowCount(0)
        self.pie_canvas.figure.clear()
        self.bar_canvas.figure.clear()

        if not path:
            return

        file_path = os.path.join(path, "cost_history.csv")
        if not os.path.exists(file_path):
            return

        try:
            with open(file_path, newline='', encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    date_str = r.get("Дата", "")
                    try:
                        date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        continue
                    project = r.get("Проект", "")
                    total_str = r.get("Итого", "").strip()
                    try:
                        total = float(total_str)
                    except ValueError:
                        total = 0.0
                    self.all_data.append((date, project, total))
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось прочитать файл истории:\n{str(e)}")
            return

        if not self.all_data:
            return

        unique_projects = sorted(set(p for _, p, _ in self.all_data))
        for proj in unique_projects:
            self.project_filter.addItem(proj)

        dates = [d for d, _, _ in self.all_data]
        min_date = min(dates)
        max_date = max(dates)

        self.date_from.setDate(QDate(min_date.year, min_date.month, min_date.day))
        self.date_to.setDate(QDate(max_date.year, max_date.month, max_date.day))

        self.update_display()

    def update_display(self):
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Дата", "Проект", "Итоговая себестоимость"])
        self.pie_canvas.figure.clear()
        self.bar_canvas.figure.clear()

        selected = self.project_filter.currentText()
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()

        filtered = [
            (d, p, t) for d, p, t in self.all_data
            if (selected == "Все проекты" or p == selected)
            and date_from <= d.date() <= date_to
        ]

        project_totals = defaultdict(float)
        for d, p, t in filtered:
            project_totals[p] += t

        for row, (d, p, t) in enumerate(filtered):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(d.strftime("%Y-%m-%d %H:%M:%S")))
            self.table.setItem(row, 1, QTableWidgetItem(p))
            self.table.setItem(row, 2, QTableWidgetItem(f"{t:.2f}"))

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

        # Круговая диаграмма
        pie_ax = self.pie_canvas.figure.add_subplot(111)
        if project_totals:
            labels = list(project_totals.keys())
            values = list(project_totals.values())
            pie_ax.pie(values, labels=labels, autopct='%1.1f%%', textprops={'fontsize': 9})
            pie_ax.set_title("Доли проектов по затратам", fontsize=11)
        self.pie_canvas.figure.tight_layout()
        self.pie_canvas.draw()

        self.filtered_data = [
            {"date": d, "project": p, "total_cost": t}
            for d, p, t in filtered
        ]
        self.update_statistics_chart()

        # Столбчатая диаграмма
        bar_ax = self.bar_canvas.figure.add_subplot(111)
        if filtered:
            filtered = sorted(filtered, key=lambda x: x[0])
            dates = [x[0].strftime("%Y-%m-%d") for x in filtered]
            totals = [x[2] for x in filtered]
            bar_ax.bar(dates, totals, color='skyblue')
            bar_ax.set_title("Изменение себестоимости во времени", fontsize=11)
            bar_ax.set_ylabel("Себестоимость", fontsize=10)
            bar_ax.tick_params(axis='x', rotation=45)

            if totals:
                avg = sum(totals) / len(totals)
                bar_ax.axhline(avg, color='red', linestyle='--', label=f'Среднее: {avg:.2f}')
                bar_ax.legend()
        self.bar_canvas.figure.tight_layout()
        self.bar_canvas.draw()

        data_by_project = defaultdict(list)
        for _, project, total in filtered:
            data_by_project[project].append(total)

        self.update_summary(data_by_project)

    def update_statistics_chart(self):
        self.stats_canvas.figure.clear()
        ax = self.stats_canvas.figure.add_subplot(111)

        stats = defaultdict(list)
        for row in self.filtered_data:
            project = row.get("project", "Без названия")
            cost = row.get("total_cost", 0)
            if cost:
                stats[project].append(cost)

        projects = []
        means, mins, maxs, medians = [], [], [], []

        for project, costs in stats.items():
            projects.append(project)
            means.append(np.mean(costs))
            mins.append(np.min(costs))
            maxs.append(np.max(costs))
            medians.append(np.median(costs))

        bar_width = 0.2
        x = np.arange(len(projects))

        ax.bar(x - bar_width*1.5, mins, width=bar_width, label="Минимум")
        ax.bar(x - bar_width/2, means, width=bar_width, label="Среднее")
        ax.bar(x + bar_width/2, medians, width=bar_width, label="Медиана")
        ax.bar(x + bar_width*1.5, maxs, width=bar_width, label="Максимум")

        ax.set_xticks(x)
        ax.set_xticklabels(projects, rotation=30, ha='right')
        ax.set_title("Статистика по проектам", fontsize=11)
        ax.legend()
        ax.grid(True)
        self.stats_canvas.figure.tight_layout()
        self.stats_canvas.draw()

    def update_summary(self, data_by_project):
        summary_text = "<b>Сводка по проектам:</b><br><ul>"
        for project, costs in data_by_project.items():
            if not costs:
                continue
            avg = mean(costs)
            med = median(costs)
            min_cost = min(costs)
            max_cost = max(costs)
            summary_text += (
                f"<li><b>{project}</b>: "
                f"среднее = {avg:.2f}, "
                f"медиана = {med:.2f}, "
                f"мин = {min_cost:.2f}, "
                f"макс = {max_cost:.2f}</li>"
            )
        summary_text += "</ul>"
        self.summary_label.setText(summary_text)

    def save_pie_chart(self):
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Сохранить круговую диаграмму", "", "PNG файл (*.png);;PDF файл (*.pdf)"
        )
        if file_path:
            if selected_filter == "PDF файл (*.pdf)" and not file_path.endswith(".pdf"):
                file_path += ".pdf"
            elif selected_filter == "PNG файл (*.png)" and not file_path.endswith(".png"):
                file_path += ".png"
            self.pie_canvas.figure.savefig(file_path)
            QMessageBox.information(self, "Успех", f"Круговая диаграмма сохранена:\n{file_path}")

    def save_bar_chart(self):
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Сохранить график по датам", "", "PNG файл (*.png);;PDF файл (*.pdf)"
        )
        if file_path:
            if selected_filter == "PDF файл (*.pdf)" and not file_path.endswith(".pdf"):
                file_path += ".pdf"
            elif selected_filter == "PNG файл (*.png)" and not file_path.endswith(".png"):
                file_path += ".png"
            self.bar_canvas.figure.savefig(file_path)
            QMessageBox.information(self, "Успех", f"График по датам сохранён:\n{file_path}")

    def export_report(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчёт", "", "CSV файл (*.csv)"
        )
        if not file_path:
            return
        if not file_path.endswith(".csv"):
            file_path += ".csv"

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Дата", "Проект", "Итоговая себестоимость"])
                for row in range(self.table.rowCount()):
                    date = self.table.item(row, 0).text()
                    project = self.table.item(row, 1).text()
                    total = self.table.item(row, 2).text()
                    writer.writerow([date, project, total])

                writer.writerow([])
                writer.writerow(["Сводка по проектам:"])

                summary_data = defaultdict(list)
                for d, p, t in self.all_data:
                    summary_data[p].append(t)

                for project, costs in summary_data.items():
                    if not costs:
                        continue
                    avg = mean(costs)
                    med = median(costs)
                    min_val = min(costs)
                    max_val = max(costs)
                    writer.writerow([
                        project,
                        f"Среднее: {avg:.2f}",
                        f"Медиана: {med:.2f}",
                        f"Мин: {min_val:.2f}",
                        f"Макс: {max_val:.2f}"
                    ])

            QMessageBox.information(self, "Успех", f"Отчёт сохранён:\n{file_path}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить отчёт:\n{str(e)}")


    def draw_pie_chart(self, data):
        self.pie_canvas.figure.clear()
        ax = self.pie_canvas.figure.add_subplot(111)

        category_totals = defaultdict(float)
        for _, _, _, article, total in data:
            category_totals[article] += total

        labels = list(category_totals.keys())
        sizes = list(category_totals.values())

        if not sizes:
            ax.set_title("Нет данных для отображения")
            self.pie_canvas.draw()
            return

        colors = plt.cm.tab20.colors  
        color_map = {label: colors[i % len(colors)] for i, label in enumerate(labels)}
        pie_colors = [color_map[label] for label in labels]

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            colors=pie_colors,
            textprops=dict(color="black"),
        )

        ax.axis("equal")
        ax.set_title("Распределение по статьям")

        # Легенда справа
        ax.legend(wedges, labels, title="Статьи", loc="center left", bbox_to_anchor=(1, 0.5))

        self.pie_canvas.figure.tight_layout()
        self.pie_canvas.draw()
