CREATE TABLE
    streamer_channels
(
    id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    streamer_id INTEGER NOT NULL,
    channel_did TEXT NOT NULL,
    template TEXT NOT NULL
);

CREATE INDEX
    streamer_channels_streamer_id
ON
    streamer_channels
    (
        streamer_id
    );
