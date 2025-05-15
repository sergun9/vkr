import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from components.workspace_tab import WorkspaceTab
from components.cost_tab import CostTab
from components.history_tab import HistoryTab
from components.references_tab import ReferencesTab
from components.analysis_tab import AnalysisTab
from components.projects_tab import ProjectsTab
from state import GlobalState

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cost Analyzer")
        self.setGeometry(100, 100, 1000, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.workspace_tab = WorkspaceTab(self.on_workspace_changed)
        self.cost_tab = CostTab()
        self.history_tab = HistoryTab()
        self.references_tab = ReferencesTab()
        self.analysis_tab = AnalysisTab()
        self.projects_tab = ProjectsTab()

        self.tabs.addTab(self.workspace_tab, "Рабочие пространства")
        self.tabs.addTab(self.cost_tab, "Расчёт")
        self.tabs.addTab(self.history_tab, "История")
        self.tabs.addTab(self.references_tab, "Справочники")
        self.tabs.addTab(self.analysis_tab, "Анализ")
        self.tabs.addTab(self.projects_tab, "Поддержка проектов")

    def on_workspace_changed(self, workspace_path):
        GlobalState.current_workspace_path = workspace_path
        for tab in [self.cost_tab, self.history_tab, self.references_tab, self.analysis_tab, self.projects_tab]:
            if hasattr(tab, 'on_workspace_changed'):
                tab.on_workspace_changed(workspace_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
