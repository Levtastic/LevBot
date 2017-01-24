CREATE TABLE
    user_servers
(
    id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    server_did TEXT NOT NULL,
    admin INTEGER NOT NULL
);

CREATE INDEX
    user_servers_user_id
ON
    streamer_channels
    (
        user_id
    );
