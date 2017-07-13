CREATE TABLE
    streamers
(
    id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    twitch_id TEXT NOT NULL,
    username TEXT NOT NULL
);

CREATE INDEX
    streamers_username
ON
    streamers
    (
        username
    );
