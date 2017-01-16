CREATE TABLE
    streamers
(
    id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    username TEXT NOT NULL
);

CREATE INDEX
    streamers_username
ON
    streamers
    (
        username
    );
