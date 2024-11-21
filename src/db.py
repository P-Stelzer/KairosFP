import sqlite3
from typing import Any, Self

_conn = sqlite3.connect("kfp.db")


class Event:
    def __init__(
        self,
        id: int,
        date: int,
        amount: int,
        name: str,
        memo: str,
        accounts: list[tuple[int, bool]],
        tag_ids: list[int],
    ) -> None:
        self.id = id
        self.date = date
        self.amount = amount
        self.name = name
        self.memo = memo
        self.accounts = accounts
        self.tag_ids = tag_ids

    def __str__(self) -> str:
        return "\n".join(
            [f"{str(f)}: {str(v)}" for f, v in self.__dict__.items()]
        )


class Tag:
    def __init__(self, id: int, name: str, description: str) -> None:
        self.id = id
        self.name = name
        self.description = description


class Account:
    def __init__(
        self,
        id: int,
        name: str,
        description: str,
        min_balance: int | None,
        max_balance: int | None,
    ) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.min_balance = min_balance
        self.max_balance = max_balance


def __initialize_schema__():
    _conn.executescript(
        """
        BEGIN;
        CREATE TABLE IF NOT EXISTS event (
            id INTEGER PRIMARY KEY ASC,
            date INTEGER,
            amount INTEGER,
            name STRING,
            memo STRING
        );
        CREATE TABLE IF NOT EXISTS tag (
            id INTEGER PRIMARY KEY ASC,
            name STRING,
            description STRING
        );
        CREATE TABLE IF NOT EXISTS event_tags (
            event_id INTEGER REFERENCES event(id) ON DELETE CASCADE,
            tag_id INTEGER REFERENCES tag(id) ON DELETE CASCADE,
            UNIQUE (event_id, tag_id)
        );
        CREATE TABLE IF NOT EXISTS account (
            id INTEGER PRIMARY KEY ASC,
            name STRING,
            description STRING,
            min_balance INTEGER,
            max_balance INTEGER
        );
        CREATE TABLE IF NOT EXISTS event_accounts (
            event_id INTEGER REFERENCES event(id) ON DELETE CASCADE,
            account_id INTEGER REFERENCES account(id) ON DELETE CASCADE,
            is_credit INTEGER,
            UNIQUE (event_id, account_id)
        );
        COMMIT;
        """
    )


def __reset_schema__():
    cur = _conn.cursor()
    print(
        cur.executescript(
            """
        BEGIN;
        EXPLAIN QUERY PLAN DROP TABLE event;
        EXPLAIN QUERY PLAN DROP TABLE tag;
        EXPLAIN QUERY PLAN DROP TABLE event_tags;
        EXPLAIN QUERY PLAN DROP TABLE account;
        EXPLAIN QUERY PLAN DROP TABLE event_accounts;
        COMMIT;
        """
        )
    )
    _conn.commit()
    # __initialize_schema__()


def insert_event(
    date: int,
    amount: int,
    name: str,
    memo: str,
    accounts: list[tuple[int, bool]],
    tag_ids: list[int],
) -> Event:
    cur = _conn.execute(
        "INSERT INTO event VALUES (?,?,?,?,?)",
        (None, date, amount, name, memo),
    )
    if cur is None:
        raise RuntimeError("Event insert Error: cursor is None")

    id = cur.lastrowid

    if id is None:
        raise RuntimeError("Could not obtain id for new event")

    if len(accounts) > 0:
        _conn.execute(
            "INSERT INTO event_accounts VALUES (?,?,?)",
            [(id, account_id, is_credit) for account_id, is_credit in accounts],
        )

    if len(tag_ids) > 0:
        _conn.execute(
            "INSERT INTO event_tags VALUES (?,?)",
            [(id, tag_id) for tag_id in tag_ids],
        )

    _conn.commit()

    return Event(id, date, amount, name, memo, accounts, tag_ids)


def alter_events(*events: Event) -> None:
    _conn.executemany(
        "UPDATE event SET date = ?, amount = ?, name = ?, memo = ? WHERE id = ?",
        [(e.date, e.amount, e.name, e.memo, e.id) for e in events],
    )


def add_tags_to_event(event_id: int, tag_ids: list[int]) -> None:
    _conn.executemany(
        "INSERT INTO event_tags VALUES (?,?)",
        [(event_id, tag_id) for tag_id in tag_ids],
    )


def remove_tags_from_event(event_id: int, tag_ids: list[int]) -> None:
    _conn.executemany(
        "DELETE FROM event_tags WHERE event_id = ? AND tag_id = ?",
        [(event_id, tag_id) for tag_id in tag_ids],
    )


def add_accounts_to_event(
    event_id: int, accounts: list[tuple[int, bool]]
) -> None:
    _conn.executemany(
        "INSERT INTO event_accounts VALUES (?,?)",
        [
            (event_id, account_id, is_credit)
            for account_id, is_credit in accounts
        ],
    )


def remove_accounts_from_event(event_id: int, account_ids: list[int]) -> None:
    _conn.executemany(
        "DELETE FROM event_accounts WHERE event_id = ? AND account_id = ?",
        [(event_id, account_id) for account_id in account_ids],
    )


def delete_events(*events: Event) -> None:
    _conn.executemany(
        "DELETE FROM event WHERE id = ?", [(e.id,) for e in events]
    )


def _get_accounts_for_event(event_id: int) -> list[tuple[int, bool]]:
    cur = _conn.execute(
        "SELECT account_id, is_credit FROM event_accounts WHERE event_id = ?",
        (event_id,),
    )

    result = cur.fetchall()

    accounts: list[tuple[int, bool]] = list()
    for account_id, is_credit in result:
        accounts.append((account_id, is_credit))

    return accounts


def _get_tags_for_event(event_id: int) -> list[int]:
    cur = _conn.execute(
        "SELECT tag_id FROM event_tags WHERE event_id = ?",
        (event_id,),
    )

    result = cur.fetchall()

    tags: list[int] = list()
    for tag_id in result:
        tags.append(tag_id)

    return tags


class EventFetcher:
    def __init__(self, columns: str = "id, date, amount, name, memo") -> None:
        self.params: list[int | str | None] = list()
        self.begin: list[str] = list()
        self.predicates: list[str] = list()
        self.begin.append("".join(("SELECT ", columns, " FROM event")))
        self.tag_joins = 0
        self.account_joins = 0

    def exec(self) -> list[Event]:
        command = " ".join(self.begin) + (
            (" WHERE " + " AND ".join(self.predicates))
            if len(self.predicates) > 0
            else ""
        )
        curr = _conn.execute(command, self.params)
        result = curr.fetchall()

        events: list[Event] = list()
        for id, date, amount, name, memo in result:
            accounts = _get_accounts_for_event(id)
            tags = _get_tags_for_event(id)
            events.append(Event(id, date, amount, name, memo, accounts, tags))

        return events

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

    def any_tags(self, *tag_ids: int) -> Self:
        if len(tag_ids) < 1:
            return self

        if len(self.begin) <= 1:
            self.begin.append(
                "NATURAL JOIN (SELECT event_id as id, tag_id as tag0 FROM event_tags)"
            )

        self.tag_joins += 1

        preds = " OR ".join(("tag0 = ?" for _ in tag_ids))
        self.predicates.append(preds.join(("(", ")")))

        for tag_id in tag_ids:
            self.params.append(tag_id)

        return self

    def all_tags(self, *tag_ids: int) -> Self:
        if len(tag_ids) < 1:
            return self

        for i in range(len(tag_ids) - self.tag_joins):
            self.begin.append(
                f"NATURAL JOIN (SELECT event_id as id, tag_id as tag{i+self.tag_joins} FROM event_tags)"
            )

        self.tag_joins += len(tag_ids) - self.tag_joins

        preds = " AND ".join((f"tag{i} = ?" for i in range(len(tag_ids))))
        self.predicates.append(preds)

        for tag_id in tag_ids:
            self.params.append(tag_id)

        return self

    def any_accounts(self, *account_ids: int) -> Self:
        if len(account_ids) < 1:
            return self

        if len(self.begin) <= 1:
            self.begin.append(
                "NATURAL JOIN (SELECT event_id as id, account_id as account0 FROM event_accounts)"
            )

        self.account_joins += 1

        preds = " OR ".join(("account0 = ?" for _ in account_ids))
        self.predicates.append(preds.join(("(", ")")))

        for account_id in account_ids:
            self.params.append(account_id)

        return self

    def all_accounts(self, *account_ids: int) -> Self:
        if len(account_ids) < 1:
            return self

        for i in range(len(account_ids) - self.account_joins):
            self.begin.append(
                f"NATURAL JOIN (SELECT event_id as id, account_id as account{i+self.account_joins} FROM event_accounts)"
            )

        self.account_joins += len(account_ids) - self.account_joins

        preds = " AND ".join((f"tag{i} = ?" for i in range(len(account_ids))))
        self.predicates.append(preds)

        for account_id in account_ids:
            self.params.append(account_id)

        return self


def fetch_events() -> EventFetcher:
    return EventFetcher()


def register_tag(name: str, description: str) -> Tag:
    cur = _conn.execute(
        "INSERT INTO tag VALUES (?, ?, ?)", (None, name, description)
    )

    if cur is None:
        raise RuntimeError("Tag insert Error: cursor is None")

    id = cur.lastrowid
    if id is None:
        raise RuntimeError("Could not obtain id for new tag")

    _conn.commit()

    return Tag(id, name, description)


def alter_tags(*tags: Tag) -> None:
    _conn.executemany(
        "UPDATE tag SET name = ?, description = ?",
        [(t.name, t.description) for t in tags],
    )


def delete_tags(*tags: Tag) -> None:
    _conn.executemany("DELETE FROM tag WHERE id = ?", [(t.id,) for t in tags])


def fetch_all_registered_tags() -> list[Tag]:
    cur = _conn.execute("SELECT * FROM tag")
    result = cur.fetchall()
    tags: list[Tag] = list()
    for id, name, description in result:
        tags.append(Tag(id, name, description))
    return tags


def register_account(
    name: str,
    description: str,
    min_balance: int | None,
    max_balance: int | None,
) -> Account:
    cur = _conn.execute(
        "INSERT INTO account VALUES (?, ?, ?, ?, ?)",
        (None, name, description, min_balance, max_balance),
    )

    if cur is None:
        raise RuntimeError("Account insert Error: cursor is None")

    id = cur.lastrowid
    if id is None:
        raise RuntimeError("Could not obtain id for new account")

    _conn.commit()

    return Account(id, name, description, min_balance, max_balance)


def alter_accounts(*accounts: Account) -> None:
    _conn.executemany(
        "UPDATE account SET name = ?, description = ?",
        [(a.name, a.description) for a in accounts],
    )


def delete_accounts(*accounts: Account) -> None:
    _conn.executemany(
        "DELETE FROM account WHERE id = ?", [(a.id,) for a in accounts]
    )


def fetch_all_registered_accounts() -> list[Account]:
    cur = _conn.execute("SELECT * FROM account")
    result = cur.fetchall()
    accounts: list[Account] = list()
    for id, name, description, min_balance, max_balance in result:
        accounts.append(
            Account(id, name, description, min_balance, max_balance)
        )
    return accounts


def main() -> None:
    __reset_schema__()
    register_tag("Tag1", "Desc1")
    register_tag("Tag2", "Desc2")
    register_tag("Tag3", "Desc3")

    for tag in fetch_all_registered_tags():
        print(tag.id, tag.name, tag.description)

    register_account("Account1", "Desc1", 100, 200)
    register_account("Account2", "Desc2", None, 200)
    register_account("Account3", "Desc3", 100, None)

    for account in fetch_all_registered_accounts():
        print(
            account.id,
            account.name,
            account.description,
            account.min_balance,
            account.max_balance,
        )


__initialize_schema__()
if __name__ == "__main__":
    main()
