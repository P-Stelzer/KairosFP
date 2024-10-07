import sys
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QRegion
from PySide6.QtWidgets import QApplication, QPushButton, QCalendarWidget, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Slot

class CalendarWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        screen = QApplication.primaryScreen().geometry()
        print(f"Screen Dimensions: {screen.x()} x {screen.y()}")
        self.setWindowTitle("EL CALONDER")
        self.setGeometry(screen.x(), screen.y(), screen.width(), screen.height())

        # make widget for calendar
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)

        calendar = QCalendarWidget(self)

        layout.addWidget(calendar)

        self.setCentralWidget(central_widget)

        # Set a custom shape for the window
        self.setWindowFlags(Qt.FramelessWindowHint)  # No title bar
        self.setMask(self.createCalendarShape())
        self.styleCalendar()


    def createCalendarShape(self):
        size = self.size()
        rect = QRect(0, 0, size.width(), size.height())
        region = QRegion(rect)
        return region
    
    def styleCalendar(self):
        # Set custom styles for the calendar
        self.setStyleSheet("""
            QCalendarWidget {
                background-color: #FFFFFF;
                color: #000000; 
            }
            QCalendarWidget QToolButton {
                background-color: #000000; 
                color: white; 
                border: none;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #FFFFFF; 
            }
            QCalendarWidget QToolButton:pressed {
                background-color: #000000; 
            }
            QCalendarWidget .QCalendarHeader {
                background-color: #000000;
                color: white;
            }
            QCalendarWidget .QTextCharFormat {
                color: #0078d7;
            }
            QCalendarWidget .QTextCharFormat:hover {
                background-color: #cce4ff;
            }
        """)
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CalendarWindow()
    window.show()
    sys.exit(app.exec())