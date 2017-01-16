CREATE TABLE
    streamer_messages
(
    id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    streamer_id INTEGER NOT NULL,
    channel_did TEXT NOT NULL,
    message_did TEXT NOT NULL
);

CREATE INDEX
    streamer_messages_streamer_id
ON
    streamer_messages
    (
        streamer_id
    );
