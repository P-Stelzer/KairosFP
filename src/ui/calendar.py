from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QFrame,
    QLabel,
)
from PySide6.QtCore import Qt, QTimer
from datetime import date as Date, timedelta
import db
from db import Event, Tag
from event_editor import Form as EventEditorForm

CURRENT_YEAR, CURRENT_WEEK, _ = Date.today().isocalendar()
FIRST_DAY_OF_CURRENT_WEEK = Date.fromisocalendar(
    CURRENT_YEAR, CURRENT_WEEK, 1
) - timedelta(days=1)  # -1 days to make it sunday
UNIT_WEEK = timedelta(weeks=1)
UNIX_EPOCH = Date(1970, 1, 1)


class Day(QPushButton):
    def __init__(self, date: Date) -> None:
        super().__init__()

        self.date = date
        color = "blue" if date == Date.today() else "black"
        self.setStyleSheet(f"border-radius : 0; border : 2px solid {color}")
        self.setMinimumSize(100, 100)
        self.events_layout = QVBoxLayout(self)
        self.events_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.date_label = QLabel(
            f"{self.date.year}/{self.date.month}/{self.date.day}"
        )
        self.events_layout.addWidget(self.date_label)
        self.clicked.connect(self.create_new_event)

        for event in db.fetch_events().on((self.date - UNIX_EPOCH).days).exec():
            self.add_event_element(event)

    def create_new_event(self):
        form = EventEditorForm(
            Event(-1, (self.date - UNIX_EPOCH).days, -1, "", "", [], [])
        )
        form.exec()

    def add_event_element(self, event: Event):
        element = EventCalendarElement(event)
        self.events_layout.addWidget(element)


class EventCalendarElement(QPushButton):
    def __init__(self, data: Event) -> None:
        super().__init__()

        self.data = data

        self.setText(self.data.name)

        self.clicked.connect(self.launch_editor)

    def launch_editor(self):
        form = EventEditorForm(self.data)
        form.exec()


class Week(QHBoxLayout):
    def __init__(self, first_day_of_week: Date) -> None:
        super().__init__()

        self.setSpacing(0)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for i in range(7):
            day = first_day_of_week + timedelta(days=i)
            day_button = Day(day)
            self.addWidget(day_button)


class InfiniteScrollArea(QScrollArea):
    def __init__(self) -> None:
        super().__init__()

        self.setWidgetResizable(True)

        area_widget = QFrame(self)
        self.area_layout = QVBoxLayout()
        self.area_layout.setSpacing(0)
        self.area_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        area_widget.setLayout(self.area_layout)

        self.setWidget(area_widget)

        self.min = 0  # Number of weeks before current week
        self.max = 0  # Number of weeks after current week

        # Check scrollbar position on a timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.scrolled)
        self.timer.start(50)

        # Check scrollbar position when it changes
        # self.verticalScrollBar().valueChanged.connect(self.scrolled)

        # Correct scrollbar position after upward extension
        self.slider_max = self.verticalScrollBar().maximum()
        self.verticalScrollBar().rangeChanged.connect(self.correct_slider)

        # Do not show a scrollbar
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Add initial content
        self.extend_upwards(5)
        self.extend_downwards(10)

    def scrolled(self):
        value = self.verticalScrollBar().value()
        if value == self.verticalScrollBar().maximum():
            self.extend_downwards(5)
        elif value == self.verticalScrollBar().minimum():
            self.extend_upwards(5)

    def extend_downwards(self, n):
        for _ in range(n):
            new_week = FIRST_DAY_OF_CURRENT_WEEK + (self.max * UNIT_WEEK)
            self.area_layout.addLayout(Week(new_week))
            self.max += 1

    def extend_upwards(self, n):
        for _ in range(n):
            self.min -= 1
            new_week = FIRST_DAY_OF_CURRENT_WEEK + (self.min * UNIT_WEEK)
            self.area_layout.insertLayout(0, Week(new_week))

    def correct_slider(self, min, max):
        if self.verticalScrollBar().value() == min:
            self.verticalScrollBar().setValue(max - self.slider_max)
        self.slider_max = max
