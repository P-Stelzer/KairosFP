import sqlite3
from typing import Any, Self
from collections import deque

_conn = sqlite3.connect("kfp.db")
_conn.executescript(
    """
    BEGIN;
    CREATE TABLE IF NOT EXISTS event (
        id INTEGER PRIMARY KEY ASC,
        date INTEGER,
        amount INTEGER,
        name STRING,
        debit INTEGER REFERENCES account(id) ON DELETE SET NULL,
        credit INTEGER REFERENCES account(id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS tag (
        id INTEGER PRIMARY KEY ASC,
        name STRING,
        description STRING
    );
    CREATE TABLE IF NOT EXISTS tagged_event (
        event_id INTEGER REFERENCES event(id) ON DELETE CASCADE,
        tag_id INTEGER REFERENCES tag(id) ON DELETE CASCADE,
        UNIQUE (event_id, tag_id)
    );
    CREATE TABLE IF NOT EXISTS account (
        id INTEGER PRIMARY KEY ASC,
        name STRING,
        description STRING
    );
    COMMIT;
    
    """
)


def insert_event(date, amount, name, account, tags: list[int]) -> None:
    pass


def define_tag(name, description) -> None:
    pass


def define_account(name, description) -> None:
    pass


class EventFetcher:

    def __init__(self) -> None:
        self.params: list[int | str | None] = list()
        self.queue: deque[str] = deque()
        self.stack: list[str] = list()

    def exec(self) -> list[Any]:
        command = (
            "".join(self.queue) + "SELECT * FROM event" + "".join(reversed(self.stack))
        )
        self.params.reverse()
        curr = _conn.execute(command, self.params)
        return curr.fetchall()

    def before_date(self, date: int) -> Self:
        self.queue.append("SELECT * FROM (")
        self.stack.append(") WHERE date < ?")
        self.params.append(date)
        return self

    def after_date(self, date: int) -> Self:
        self.queue.append("SELECT * FROM (")
        self.stack.append(") WHERE date > ?")
        self.params.append(date)
        return self

    def with_any_tags(self, *tag_ids) -> Self:
        self.queue.append("SELECT id, date, amount, name, debit, credit FROM (")
        pred = list()
        pred.append(") JOIN tagged_event ON event.id = tagged_event.id")
        if len(tag_ids) > 0:
            pred.append(" WHERE tag_id = ?")
            self.params.append(tag_ids[0])
        for tag_id in tag_ids[1:]:
            pred.append(" OR tag_id = ?")
            self.params.append(tag_id)

        self.stack.append("".join(pred))
        return self

    def with_all_tags(self, *tag_ids) -> Self:
        self.queue.append("SELECT id, date, amount, name, debit, credit FROM (")
        pred = list()
        pred.append(") JOIN tagged_event ON event.id = tagged_event.id")
        if len(tag_ids) > 0:
            pred.append(" WHERE tag_id = ?")
            self.params.append(tag_ids[0])
        for tag_id in tag_ids[1:]:
            pred.append(" OR tag_id = ?")
            self.params.append(tag_id)

        self.stack.append("".join(pred))
        return self

    # SELECT * FROM event WHERE
    # date_pred(date)
    # amount_pred(amount)
    # name_pred(name)
    # debit

    # SELECT * FROM (SELECT * FROM (SELECT * FROM (SELECT * FROM event WHERE date > ?) WHERE date < ?) JOIN tagged_event ON event.id = tagged_event.event_id WHERE tag_id = ?), (1000, 10000, 3)


def fetch_events() -> EventFetcher:
    return EventFetcher()


def main() -> None:
    data = (
        (1, 1, 1, "A", None, None),
        (2, 10, 2, "B", None, None),
        (3, 11, 3, "C", None, None),
        (4, 50, 4, "D", None, None),
        (5, 99, 5, "E", None, None),
        (6, 100, 6, "F", None, None),
    )
    # _conn.executemany("INSERT INTO event VALUES (?,?,?,?,?,?)", data)
    events = fetch_events().after_date(10).before_date(100).exec()
    for e in events:
        print(e)


if __name__ == "__main__":
    main()
