import sys

from PySide6.QtWidgets import QApplication, QHBoxLayout, QWidget

from kui.balance_sheet import BalanceSheet
from kui.calendar import Calendar

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setApplicationDisplayName("Kairos Financial Planner")

    main_widget = QWidget()
    layout = QHBoxLayout()
    main_widget.setLayout(layout)

    calendar = Calendar()
    balance_sheet = BalanceSheet()

    layout.addWidget(balance_sheet)
    layout.addWidget(calendar)

    main_widget.show()

    app.exec()
