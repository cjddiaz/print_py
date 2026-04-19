import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow


def apply_dark_palette(app: QApplication):
    """Apply a professional dark palette to the entire application."""
    app.setStyle("Fusion")
    palette = QPalette()

    dark    = QColor(30,  30,  30)
    mid     = QColor(45,  45,  45)
    light   = QColor(60,  60,  60)
    text    = QColor(220, 220, 220)
    accent  = QColor(26,  115, 232)
    white   = QColor(255, 255, 255)

    palette.setColor(QPalette.ColorRole.Window,          mid)
    palette.setColor(QPalette.ColorRole.WindowText,      text)
    palette.setColor(QPalette.ColorRole.Base,            dark)
    palette.setColor(QPalette.ColorRole.AlternateBase,   mid)
    palette.setColor(QPalette.ColorRole.ToolTipBase,     dark)
    palette.setColor(QPalette.ColorRole.ToolTipText,     text)
    palette.setColor(QPalette.ColorRole.Text,            text)
    palette.setColor(QPalette.ColorRole.Button,          light)
    palette.setColor(QPalette.ColorRole.ButtonText,      text)
    palette.setColor(QPalette.ColorRole.BrightText,      white)
    palette.setColor(QPalette.ColorRole.Link,            accent)
    palette.setColor(QPalette.ColorRole.Highlight,       accent)
    palette.setColor(QPalette.ColorRole.HighlightedText, white)

    app.setPalette(palette)

    app.setStyleSheet("""
        QToolBar { spacing: 4px; padding: 4px; }
        QToolBar QPushButton {
            padding: 4px 10px;
            border-radius: 4px;
            border: 1px solid #555;
            background: #3c3c3c;
            color: #ddd;
        }
        QToolBar QPushButton:hover { background: #4a4a4a; }
        QTabWidget::pane { border: 1px solid #555; }
        QTabBar::tab { padding: 6px 14px; }
        QTabBar::tab:selected { background: #1a73e8; color: white; }
        QStatusBar { background: #222; color: #aaa; }
        QGroupBox { border: 1px solid #555; border-radius: 4px; margin-top: 8px; }
        QGroupBox::title { subcontrol-origin: margin; left: 8px; }
        QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {
            background: #2a2a2a; color: #ddd; border: 1px solid #555;
            border-radius: 3px; padding: 2px 4px;
        }
        QTableWidget { gridline-color: #444; }
        QHeaderView::section { background: #333; color: #ddd; border: none; padding: 4px; }
    """)


def main():
    app = QApplication(sys.argv)
    apply_dark_palette(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
