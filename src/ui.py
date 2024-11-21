from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QFrame,
    QMessageBox,
    QWidget,
    QLabel,
    QLineEdit,
    QDialog,
)
from PySide6.QtCore import Qt, QTimer
from datetime import date as Date, timedelta
import db
from db import Event, Tag

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


class EventEditorForm(QDialog):
    def __init__(self, event: Event) -> None:
        super().__init__()

        self.target_event = event

        self.added_tags: list[int] = list()
        self.removed_tags: list[int] = list()
        self.tag_editor_form = EventTagEditor(self)

        # container (box)
        self.box = QVBoxLayout(self)
        self.top_layer = QHBoxLayout()

        # WRAPPER: TOP_LAYER {

        # event name label (label)
        self.event_name_text_box = QLineEdit()
        self.event_name_text_box.setPlaceholderText("Event name...")
        self.event_name_text_box.setText(event.name)
        self.top_layer.addWidget(self.event_name_text_box)

        # tag edit (button)
        self.add_tag_button = QPushButton("Edit Tags")
        self.add_tag_button.clicked.connect(self.launch_tag_editor_form)
        self.top_layer.addWidget(self.add_tag_button)

        # event color (button)
        self.event_color_button = QPushButton("Select Event Color")
        self.top_layer.addWidget(self.event_color_button)

        self.box.addLayout(self.top_layer)
        # }

        # amount (text box)
        self.event_amount_text_box = QLineEdit()
        self.event_amount_text_box.setPlaceholderText("Enter amount...")
        self.amount_validator = QDoubleValidator(0, 999999999.99, 2, self)
        self.amount_validator.setNotation(
            QDoubleValidator.Notation.StandardNotation
        )
        self.event_amount_text_box.setValidator(self.amount_validator)
        if event.amount >= 0:
            self.event_amount_text_box.setText(
                f"{event.amount//100}.{event.amount%100}"
            )
        self.box.addWidget(self.event_amount_text_box)

        # memo (text box)
        self.event_memo_text_box = QLineEdit()
        self.event_memo_text_box.setPlaceholderText("Enter memo...")
        self.event_memo_text_box.setText(event.memo)
        self.box.addWidget(self.event_memo_text_box)

        # associated account (list of accounts)

        # add account (button)

        # confirm button (button)
        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.clicked.connect(self.attempt_confirm)
        self.box.addWidget(self.confirm_button)

        self.setLayout(self.box)

    def launch_tag_editor_form(self):
        self.tag_editor_form.exec()

    def attempt_confirm(self):
        name = self.event_name_text_box.text()
        amount = self.event_amount_text_box.text()
        memo = self.event_memo_text_box.text()
        if len(amount) == 0:
            print("Invlaid input amount")
            return

        split_amount = amount.split(".")
        dollar_amount = int(split_amount[0])
        cent_amount = int(split_amount[1]) if len(split_amount) > 1 else 0
        serialized_amount = (dollar_amount * 100) + cent_amount

        self.target_event.name = name
        self.target_event.memo = memo
        self.target_event.amount = serialized_amount

        print(self.target_event)

        if self.target_event.id < 0:
            db.insert_event(
                self.target_event.date,
                self.target_event.amount,
                self.target_event.name,
                self.target_event.memo,
                self.target_event.accounts,
                self.target_event.tag_ids,
            )
        else:
            db.alter_events(self.target_event)
            db.remove_tags_from_event(self.target_event.id, self.removed_tags)
            db.add_tags_to_event(self.target_event.id, self.added_tags)

        self.close()


class EventTagEditor(QDialog):
    def __init__(self, event_editor: EventEditorForm) -> None:
        super().__init__()

        self.event_editor = event_editor
        print(self.event_editor.target_event.tag_ids)

        self.tags_layout = QVBoxLayout(self)

        # clicking tag from list adds it to that specific event
        for tag in db.fetch_all_registered_tags():
            tag_button = EventTagEditorButton(
                self, tag, tag.id in self.event_editor.target_event.tag_ids
            )
            self.tags_layout.addWidget(tag_button)


class EventTagEditorButton(QPushButton):
    def __init__(
        self, tag_editor: EventTagEditor, tag: Tag, is_event_member: bool
    ):
        super().__init__()

        self.tag_editor = tag_editor
        self.tag = tag
        self.is_event_member = is_event_member
        self.is_activated = is_event_member

        self.update_text()

        self.clicked.connect(self.toggle_tag)

    def update_text(self):
        if self.is_activated:
            self.setText(f"Remove {self.tag.name}")
        else:
            self.setText(f"Add {self.tag.name}")

    def toggle_tag(self):
        self.is_activated = not self.is_activated
        self.update_text()

        match (self.is_event_member, self.is_activated):
            case (True, True):
                self.tag_editor.event_editor.removed_tags.remove(self.tag.id)
            case (True, False):
                self.tag_editor.event_editor.removed_tags.append(self.tag.id)
            case (False, True):
                self.tag_editor.event_editor.added_tags.append(self.tag.id)
            case (False, False):
                self.tag_editor.event_editor.added_tags.remove(self.tag.id)

        print(self.tag_editor.event_editor.removed_tags)
        print(self.tag_editor.event_editor.added_tags)
