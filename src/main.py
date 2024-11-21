import sys
from PySide6.QtWidgets import QApplication
import ui
import db

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = ui.InfiniteScrollArea()
    window.show()

    editor = ui.EventEditorForm(
        db.Event(1, 1, 1, "Test", "This is a test", [], [])
    )
    editor.show()

    app.exec()
