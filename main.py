"""Hydro Network Editor - Entry Point."""
import sys
from PyQt6.QtWidgets import QApplication
from app.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Hydro Network Editor")

    window = MainWindow()
    window.show()

    if len(sys.argv) > 1:
        window._open_file_path(sys.argv[1])

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
