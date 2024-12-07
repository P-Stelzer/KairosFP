from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMenu,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QFrame,
    QLabel,
)
from PySide6.QtCore import Qt, QTimer
from datetime import date as Date, timedelta
import db
from db import Event
from kui.event_editor import EventEditor

import threading

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


def get_loaded_events(date: Date) -> list[Event]:
    serial = date_to_serial(date)
    low = 0
    high = len(db.LOADED_EVENTS) - 1
    mid = 0
    while low <= high:
        mid = low + (high - low) // 2
        if db.LOADED_EVENTS[mid].date == serial:
            break
        elif db.LOADED_EVENTS[mid].date > serial:
            high = mid - 1
        else:
            low = mid + 1

    while mid - 1 >= 0 and db.LOADED_EVENTS[mid - 1].date == serial:
        mid -= 1

    events: list[Event] = list()
    while mid < len(db.LOADED_EVENTS) and db.LOADED_EVENTS[mid].date == serial:
        events.append(db.LOADED_EVENTS[mid])
        mid += 1

    return events


def insert_new_event(event: Event) -> None:
    low = 0
    high = len(db.LOADED_EVENTS) - 1
    mid = 0
    while low <= high:
        mid = low + (high - low) // 2
        if db.LOADED_EVENTS[mid].date == event.date:
            while (
                mid < len(db.LOADED_EVENTS)
                and db.LOADED_EVENTS[mid].date == event.date
            ):
                mid += 1
            low = mid
        elif db.LOADED_EVENTS[mid].date > event.date:
            high = mid - 1
        else:
            low = mid + 1

    db.LOADED_EVENTS.insert(low, event)
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
    def __init__(self, target_event: Event) -> None:
        super().__init__()

        self.target_event = target_event

        self.setText(self.target_event.name)

        self.clicked.connect(self.launch_editor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def launch_editor(self):
        form = EventEditor(self.target_event)
        form.exec()

    def delete_event(self):
        db.delete_events(self.target_event)
        db.LOADED_EVENTS.remove(self.target_event)
        db.commit_changes()
        refresh_day(self.target_event.date)

    def show_context_menu(self, position) -> None:
        context_menu = QMenu(self)

        edit_event = QAction("Edit Event", self)
        edit_event.triggered.connect(self.launch_editor)
        context_menu.addAction(edit_event)

        delete_event = QAction("Delete Event", self)
        delete_event.triggered.connect(self.delete_event)
        context_menu.addAction(delete_event)

        context_menu.exec(self.mapToGlobal(position))


class Week(QHBoxLayout):
    def __init__(
        self, calendar: "InfiniteScrollArea", first_day_of_week: Date
    ) -> None:
        super().__init__()

        self.calendar = calendar

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

        self.expanding = False

        # Check scrollbar position on a timer
        # self.timer = QTimer(self)
        # self.timer.timeout.connect(self.scrolled)
        # self.timer.start(50)

        # Check scrollbar position when it changes
        self.verticalScrollBar().valueChanged.connect(self.scrolled)

        # Correct scrollbar position after upward extension
        # self.slider_max = self.verticalScrollBar().maximum()
        # self.verticalScrollBar().rangeChanged.connect(self.correct_slider)

        # Do not show a scrollbar
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Add initial content
        self.extend_downwards(10)
        self.extend_upwards(5)
        # self.thread().msleep(100)
        self.show()
        self.verticalScrollBar().setValue(400)

    def scrolled(self):
        if self.expanding:
            return
        self.expanding = True
        value = self.verticalScrollBar().value()
        if value == self.verticalScrollBar().maximum():
            self.extend_downwards(5)
            # self.thread().sleep(50)
        elif value == self.verticalScrollBar().minimum():
            self.extend_upwards(5)
            # self.thread().msleep(20)
            self.verticalScrollBar().setValue(500)
        self.expanding = False

    def extend_downwards(self, n):
        after = date_to_serial(self.max) - 1
        before = after + 1 + (7 * n)
        new_events = db.fetch_events().after(after).before(before).exec()
        db.LOADED_EVENTS.extend(new_events)
        for _ in range(n):
            self.area_layout.addLayout(Week(self, self.max))
            self.max += UNIT_WEEK

    def extend_upwards(self, n):
        before = date_to_serial(self.min)
        after = before - 1 - (7 * n)
        new_events = db.fetch_events().before(before).after(after).exec()
        new_events.extend(db.LOADED_EVENTS)
        db.LOADED_EVENTS = new_events
        for _ in range(n):
            self.min -= UNIT_WEEK
            self.area_layout.insertLayout(0, Week(self, self.min))

    def correct_slider(self, min, max):
        # self.thread().msleep(50)
        if self.verticalScrollBar().value() == min:
            self.verticalScrollBar().setValue(1000)
            print(min, max, "Correcting", max - self.slider_max)
        self.slider_max = max
