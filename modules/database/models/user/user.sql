CREATE TABLE
    users
(
    id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    user_did TEXT NOT NULL,
    blacklisted INTEGER NOT NULL
);

CREATE INDEX
    users_user_did
ON
    users
    (
        user_did
    );
