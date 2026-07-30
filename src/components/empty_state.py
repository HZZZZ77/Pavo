from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class EmptyState(QWidget):
    open_requested = Signal()
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("emptyState")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAcceptDrops(True)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QWidget#emptyState {
                background-color: transparent;
            }
            QLabel#emptyStateTitle {
                color: rgba(255, 255, 255, 235);
                background-color: transparent;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                font-size: 32px;
                font-weight: 600;
            }
            QLabel#emptyStateHint {
                color: rgba(255, 255, 255, 135);
                background-color: transparent;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                font-size: 14px;
                font-weight: 400;
            }
            QPushButton#emptyStateOpenButton {
                min-width: 124px;
                min-height: 36px;
                color: rgba(255, 255, 255, 235);
                background-color: rgba(255, 255, 255, 24);
                border: 1px solid rgba(255, 255, 255, 45);
                border-radius: 7px;
                padding: 0 18px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton#emptyStateOpenButton:hover {
                background-color: rgba(255, 255, 255, 38);
                border-color: rgba(255, 255, 255, 65);
            }
            QPushButton#emptyStateOpenButton:pressed {
                background-color: rgba(255, 255, 255, 52);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 32, 24, 110)
        layout.setSpacing(0)
        layout.addStretch(3)

        self.title_label = QLabel("Pavo")
        self.title_label.setObjectName("emptyStateTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        layout.addSpacing(10)

        self.hint_label = QLabel("Drop a video here to play")
        self.hint_label.setObjectName("emptyStateHint")
        self.hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.hint_label)

        layout.addSpacing(22)

        self.open_button = QPushButton("Open File...")
        self.open_button.setObjectName("emptyStateOpenButton")
        self.open_button.setCursor(Qt.PointingHandCursor)
        self.open_button.clicked.connect(lambda: self.open_requested.emit())
        layout.addWidget(self.open_button, 0, Qt.AlignHCenter)

        layout.addStretch(4)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.toLocalFile()]
        if paths:
            event.acceptProposedAction()
            self.files_dropped.emit(paths)
