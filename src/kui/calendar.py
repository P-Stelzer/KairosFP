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
from kui.event_editor import EventEditor

CURRENT_YEAR, CURRENT_WEEK, _ = Date.today().isocalendar()
FIRST_DAY_OF_CURRENT_WEEK = Date.fromisocalendar(
    CURRENT_YEAR, CURRENT_WEEK, 1
) - timedelta(days=1)  # -1 days to make it sunday
UNIT_WEEK = timedelta(weeks=1)
UNIX_EPOCH = Date(1970, 1, 1)


def date_to_serial(date: Date) -> int:
    return (date - UNIX_EPOCH).days


def serial_to_date(serial: int) -> Date:
    return UNIX_EPOCH + timedelta(days=serial)


LOADED_DAYS: dict[int, "Day"] = dict()
LOADED_EVENTS: list[Event] = list()


def get_loaded_events(date: Date) -> list[Event]:
    serial = date_to_serial(date)
    low = 0
    high = len(LOADED_EVENTS) - 1
    mid = 0
    while low <= high:
        mid = low + (high - low) // 2
        if LOADED_EVENTS[mid].date == serial:
            break
        elif LOADED_EVENTS[mid].date > serial:
            high = mid - 1
        else:
            low = mid + 1

    while mid - 1 >= 0 and LOADED_EVENTS[mid - 1].date == serial:
        mid -= 1

    events: list[Event] = list()
    while mid < len(LOADED_EVENTS) and LOADED_EVENTS[mid].date == serial:
        events.append(LOADED_EVENTS[mid])
        mid += 1

    return events


def insert_new_event(event: Event) -> None:
    low = 0
    high = len(LOADED_EVENTS) - 1
    mid = 0
    while low <= high:
        mid = low + (high - low) // 2
        if LOADED_EVENTS[mid].date == event.date:
            while (
                mid < len(LOADED_EVENTS)
                and LOADED_EVENTS[mid].date == event.date
            ):
                mid += 1
            low = mid
        elif LOADED_EVENTS[mid].date > event.date:
            high = mid - 1
        else:
            low = mid + 1

    LOADED_EVENTS.insert(low, event)
    refresh_day(event.date)


def refresh_day(date: int) -> None:
    day = LOADED_DAYS.get(date)
    if day is not None:
        day.clear_elements()
        day.load_elements()


class Day(QPushButton):
    def __init__(self, date: Date) -> None:
        super().__init__()

        LOADED_DAYS[date_to_serial(date)] = self

        self.date = date
        color = "blue" if date == Date.today() else "black"
        self.setStyleSheet(f"border-radius : 0; border : 2px solid {color}")
        self.setMinimumSize(100, 100)
        self.date_label = QLabel(
            f"{self.date.year}/{self.date.month}/{self.date.day}"
        )
        self.events_layout = QVBoxLayout(self)
        self.events_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.events_layout.addWidget(self.date_label)
        self.clicked.connect(self.create_new_event)
        self.load_elements()

    def load_elements(self):
        for event in get_loaded_events(self.date):
            element = EventCalendarElement(event)
            self.events_layout.addWidget(element)

    def clear_elements(self):
        for i in reversed(range(1, self.events_layout.count())):
            item = self.events_layout.itemAt(i)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def create_new_event(self):
        form = EventEditor(
            Event(-1, date_to_serial(self.date), -1, "", "", [], [])
        )
        form.exec()


class EventCalendarElement(QPushButton):
    def __init__(self, data: Event) -> None:
        super().__init__()

        self.data = data

        self.setText(self.data.name)

        self.clicked.connect(self.launch_editor)

    def launch_editor(self):
        form = EventEditor(self.data)
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

        self.min = FIRST_DAY_OF_CURRENT_WEEK
        self.max = self.min

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
        after = date_to_serial(self.max) - 1
        before = after + 1 + (7 * n)
        new_events = db.fetch_events().after(after).before(before).exec()
        LOADED_EVENTS.extend(new_events)
        for _ in range(n):
            self.area_layout.addLayout(Week(self.max))
            self.max += UNIT_WEEK

    def extend_upwards(self, n):
        global LOADED_EVENTS
        before = date_to_serial(self.min)
        after = before - 1 - (7 * n)
        new_events = db.fetch_events().before(before).after(after).exec()
        new_events.extend(LOADED_EVENTS)
        LOADED_EVENTS = new_events
        for _ in range(n):
            self.min -= UNIT_WEEK
            self.area_layout.insertLayout(0, Week(self.min))

    def correct_slider(self, min, max):
        if self.verticalScrollBar().value() == min:
            self.verticalScrollBar().setValue(max - self.slider_max)
        self.slider_max = max
