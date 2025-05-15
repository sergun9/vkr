from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget
import os

class WorkspaceTab(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Рабочие пространства"))
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Введите имя пространства")
        layout.addWidget(self.input)

        self.button = QPushButton("Создать пространство")
        self.button.clicked.connect(self.create_workspace)
        layout.addWidget(self.button)

        self.list_widget.itemClicked.connect(self.workspace_selected)

        self.load_workspaces()

    def load_workspaces(self):
        self.list_widget.clear()
        os.makedirs("workspaces", exist_ok=True)
        for name in os.listdir("workspaces"):
            self.list_widget.addItem(name)

    def create_workspace(self):
        name = self.input.text().strip()
        if name:
            path = os.path.join("workspaces", name)
            os.makedirs(path, exist_ok=True)
            os.makedirs(os.path.join(path, "references"), exist_ok=True)
            os.makedirs(os.path.join(path, "projects"), exist_ok=True)
            self.load_workspaces()

    def workspace_selected(self, item):
        name = item.text()
        path = os.path.join("workspaces", name)
        self.switch_callback(path)
