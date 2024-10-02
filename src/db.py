import sqlite3
from typing import Any, Self

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


class Event:
    def __init__(
        self,
        id: int,
        date: int,
        amount: int,
        name: str,
        debit: int | None,
        credit: int | None,
        *tag_ids: int,
    ) -> None:
        self.id = id
        self.date = date
        self.amount = amount
        self.name = name
        self.debit = debit
        self.credit = credit
        self.tag_ids = tag_ids


def insert_event(
    date: int,
    amount: int,
    name: str,
    debit: int | None,
    credit: int | None,
    *tag_ids: int,
) -> Event:
    cur = _conn.execute(
        "INSERT INTO event VALUES (?,?,?,?,?,?)",
        (None, date, amount, name, debit, credit),
    )
    if cur is None:
        raise RuntimeError("Event insert Error: cursor is None")

    id = cur.lastrowid

    if len(tag_ids) > 0:
        _conn.execute(
            "INSERT INTO tagged_event VALUES (?,?)",
            [(id, tag_id) for tag_id in tag_ids],
        )

    return Event(id, date, amount, name, debit, credit, *tag_ids)


def alter_events(*events: Event) -> None:
    _conn.executemany(
        "UPDATE event SET date = ?, amount = ?, name = ?, debit = ?, credit = ? WHERE id = ?",
        [(e.date, e.amount, e.name, e.debit, e.credit, e.id) for e in events],
    )


def delete_events(*events: Event) -> None:
    _conn.executemany("DELETE FROM event WHERE id = ?", [(e.id,) for e in events])


class EventFetcher:

    def __init__(self, columns: str = "id, date, amount, name, debit, credit") -> None:
        self.params: list[int | str | None] = list()
        self.begin: list[str] = list()
        self.predicates: list[str] = list()
        self.begin.append("".join(("SELECT ", columns, " FROM event")))

    def exec(self) -> list[Any]:
        command = " ".join(self.begin) + (
            (" WHERE " + " AND ".join(self.predicates))
            if len(self.predicates) > 0
            else ""
        )
        curr = _conn.execute(command, self.params)
        return curr.fetchall()

    def before(self, date: int) -> Self:
        self.predicates.append("date < ?")
        self.params.append(date)
        return self

    def after(self, date: int) -> Self:
        self.predicates.append("date > ?")
        self.params.append(date)
        return self

    def amount_less(self, amount: int) -> Self:
        self.predicates.append("amount < ?")
        self.params.append(amount)
        return self

    def amount_greater(self, amount: int) -> Self:
        self.predicates.append("amount > ?")
        self.params.append(amount)
        return self

    def name_is(self, name: str) -> Self:
        self.predicates.append("name = ?")
        self.params.append(name)
        return self

    def name_contains(self, name: str) -> Self:
        self.predicates.append("name LIKE ?")
        self.params.append(name.join(("%", "%")))
        return self

    def debited(self, account_id: int | None) -> Self:
        if account_id is None:
            self.predicates.append("debit ISNULL")
        else:
            self.predicates.append("debit = ?")
            self.params.append(account_id)
        return self

    def credited(self, account_id: int | None) -> Self:
        if account_id is None:
            self.predicates.append("credit ISNULL")
        else:
            self.predicates.append("credit = ?")
            self.params.append(account_id)
        return self

    def any_tags(self, *tag_ids: int) -> Self:
        if len(tag_ids) < 1:
            return self

        if len(self.begin) <= 1:
            self.begin.append(
                "NATURAL JOIN (SELECT event_id as id, tag_id as tag0 FROM tagged_event)"
            )

        preds = " OR ".join(("tag0 = ?" for _ in tag_ids))
        self.predicates.append(preds.join(("(", ")")))

        for tag_id in tag_ids:
            self.params.append(tag_id)

        return self

    def all_tags(self, *tag_ids: int) -> Self:
        if len(tag_ids) < 1:
            return self

        tag_offset = len(self.begin) - 1
        for i in range(len(tag_ids) - tag_offset):
            self.begin.append(
                f"NATURAL JOIN (SELECT event_id as id, tag_id as tag{i+tag_offset} FROM tagged_event)"
            )

        preds = " AND ".join((f"tag{i} = ?" for i in range(len(tag_ids))))
        self.predicates.append(preds)

        for tag_id in tag_ids:
            self.params.append(tag_id)

        return self


def fetch_events() -> EventFetcher:
    return EventFetcher()


class Tag:
    def __init__(self, id: int, name: str, description: str) -> None:
        self.id = id
        self.name = name
        self.description = description


def define_tag(name: str, description: str) -> Tag:
    cur = _conn.execute("INSERT INTO tag VALUES (?, ?, ?)", (None, name, description))

    if cur is None:
        raise RuntimeError("Tag insert Error: cursor is None")

    return Tag(cur.lastrowid, name, description)


def alter_tags(*tags: Tag) -> None:
    _conn.executemany(
        "UPDATE tag SET name = ?, description = ?",
        [(t.name, t.description) for t in tags],
    )


def delete_tags(*tags: Tag) -> None:
    _conn.executemany("DELETE FROM tag WHERE id = ?", [(t.id,) for t in tags])


class Account:
    def __init__(self, id: int, name: str, description: str) -> None:
        self.id = id
        self.name = name
        self.description = description


def new_account(name: str, description: str) -> Account:
    cur = _conn.execute(
        "INSERT INTO account VALUES (?, ?, ?)", (None, name, description)
    )

    if cur is None:
        raise RuntimeError("Account insert Error: cursor is None")

    return Account(cur.lastrowid, name, description)


def alter_accounts(*accounts: Account) -> None:
    _conn.executemany(
        "UPDATE account SET name = ?, description = ?",
        [(a.name, a.description) for a in accounts],
    )


def delete_accounts(*accounts: Account) -> None:
    _conn.executemany("DELETE FROM account WHERE id = ?", [(a.id,) for a in accounts])


def main() -> None:
    ev1 = insert_event(0, 1, "potat", None, None)
    ev2 = insert_event(0, 10, "potato", None, None)
    ev3 = insert_event(0, 100, "bigpotatoes", None, None)

    events = fetch_events().exec()
    for e in events:
        print(e)

    ev1.date = 1
    ev2.date = 2

    ev = [ev1, ev2]

    alter_events(*ev)
    delete_events(ev3)

    events = fetch_events().exec()
    for e in events:
        print(e)


if __name__ == "__main__":
    main()
