CREATE TABLE
    admins
(
    id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    user_did TEXT NOT NULL
);

CREATE INDEX
    admins_user_did
ON
    admins
    (
        user_did
    );
