import sys
from db import Tag
from PySide6.QtWidgets import QApplication

from kui.calendar import InfiniteScrollArea
from kui.tag_editor import TagEditor

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = InfiniteScrollArea()
    window.show()
    tag_editor = TagEditor(Tag(-1, "testName", "testDesc"))
    tag_editor.show()

    app.exec()
