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

CURRENT_YEAR, CURRENT_WEEK, _ = Date.today().isocalendar()
FIRST_DAY_OF_CURRENT_WEEK = Date.fromisocalendar(
    CURRENT_YEAR, CURRENT_WEEK, 1
) - timedelta(days=1)  # -1 days to make it sunday
UNIT_WEEK = timedelta(weeks=1)


class Day(QPushButton):
    def __init__(self, date: Date) -> None:
        super().__init__()

        self.date = date
        color = "blue" if date == Date.today() else "black"
        self.setStyleSheet(f"border-radius : 0; border : 2px solid {color}")
        self.setMinimumSize(100, 100)
        self.setText(f"{self.date.year}/{self.date.month}/{self.date.day}")


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


class EventEditorForm(QWidget):
    def __init__(self, event: db.Event) -> None:
        super().__init__()

        self.event_editor = EventEditor(event)
        self.tag_editor_form = EventTagEditor(event.tag_ids)

        # container (box)
        self.box = QVBoxLayout(self)
        self.top_layer = QHBoxLayout(self)

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
        self.event_amount_text_box.setText(str(event.amount))
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
        if self.event_editor.confirm_event_changes(name, amount, memo):
            pass


class EventTagEditor(QDialog):
    def __init__(self, event_tags: list[int]) -> None:
        super().__init__()

        self.event_tags = event_tags

        self.tags_layout = QVBoxLayout(self)

        self.db_tags = db.fetch_all_registered_tags()

        # clicking tag from list adds it to that specific event
        for tag in self.db_tags:
            tag_button = EventTagEditorButton(self, tag, tag in event_tags)
            self.tags_layout.addWidget(tag_button)


class EventTagEditorButton(QPushButton):
    def __init__(
        self, tag_editor: EventTagEditor, tag: db.Tag, tag_present: bool
    ):
        super().__init__()

        self.tag_editor = tag_editor
        self.tag = tag
        self.tag_present = tag_present

        self.update_text()

        self.clicked.connect(self.toggle_tag)

    def update_text(self):
        if self.tag_present:
            self.setText(f"Remove {self.tag.name}")
        else:
            self.setText(f"Add {self.tag.name}")

    def toggle_tag(self):
        if self.tag_present:
            self.tag_editor.event_tags.remove(self.tag.id)
        else:
            self.tag_editor.event_tags.append(self.tag.id)

        self.tag_present = not self.tag_present
        self.update_text()


class EventEditor:
    def __init__(self, event: db.Event) -> None:
        self.event = event

    # updates the self variables to the database
    def confirm_event_changes(self, name, amount, memo) -> bool:
        print(f"Updated name: {name}")
        print(f"Updated amount: {amount}")
        print(f"Updated memo: {memo}")
        return True
