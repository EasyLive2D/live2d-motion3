from PySide6.QtWidgets import QMainWindow, QFileDialog
from ui_MainWindow import Ui_MainWindow
from MotionDesigner import MotionDesigner
import os
from motion_interpolate import Motion


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.actionNew.triggered.connect(self._on_new_action_triggered)
        self.ui.actionOpen.triggered.connect(self._on_open_action_triggered)
        self.ui.actionSave.triggered.connect(self._on_save_action_triggered)

        self.ui.tabs.tabCloseRequested.connect(self.ui.tabs.removeTab)

    def _create_tab(self, model_path, motion=None):
        motion_designer = MotionDesigner(model_path, motion)
        tab_name = os.path.split(os.path.dirname(model_path))[-1]
        self.ui.tabs.addTab(motion_designer, tab_name)
        self.ui.tabs.setCurrentIndex(self.ui.tabs.count() - 1)

    def _on_new_action_triggered(self):
        model_path = QFileDialog.getOpenFileName(self, "打开模型", "", "Live2D 模型 (*.model3.json)")[0]
        if model_path:
            self._create_tab(model_path)

    def _on_open_action_triggered(self):
        model_path = QFileDialog.getOpenFileName(self, "打开模型", "", "Live2D 模型 (*.model3.json)")[0]
        motion_path = QFileDialog.getOpenFileName(self, "打开motion", "", "Live2D Motion3 (*.motion3.json)")[0]
        if model_path and motion_path:
            self._create_tab(model_path, Motion.create(motion_path))

    def _on_save_action_triggered(self):
        designer: MotionDesigner = self.ui.tabs.currentWidget()
        name = self.ui.tabs.tabText(self.ui.tabs.currentIndex())
        designer.export_motion(f"{name}.motion3.json")
