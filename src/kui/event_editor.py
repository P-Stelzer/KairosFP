from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QLineEdit,
    QDialog,
)
import db
from db import Event, Tag
import kui.calendar as calendar


class EventEditor(QDialog):
    def __init__(self, event: Event) -> None:
        super().__init__()

        self.target_event = event

        self.added_tags: list[int] = list()
        self.removed_tags: list[int] = list()
        self.tag_editor_form = TagSelector(self)

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

        if self.target_event.id < 0:
            new_event = db.insert_event(
                self.target_event.date,
                self.target_event.amount,
                self.target_event.name,
                self.target_event.memo,
                self.target_event.accounts,
                self.target_event.tag_ids,
            )
            calendar.insert_new_event(new_event)

        else:
            db.alter_events(self.target_event)
            db.remove_tags_from_event(self.target_event.id, self.removed_tags)
            db.add_tags_to_event(self.target_event.id, self.added_tags)
            calendar.refresh_day(self.target_event.date)

        self.close()


class TagSelector(QDialog):
    def __init__(self, event_editor: EventEditor) -> None:
        super().__init__()

        self.event_editor = event_editor

        self.tags_layout = QVBoxLayout(self)

        # clicking tag from list adds it to that specific event
        for tag in db.fetch_all_registered_tags():
            tag_button = TagSelectorButton(
                self, tag, tag.id in self.event_editor.target_event.tag_ids
            )
            self.tags_layout.addWidget(tag_button)


class TagSelectorButton(QPushButton):
    def __init__(
        self, tag_editor: TagSelector, tag: Tag, is_event_member: bool
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
