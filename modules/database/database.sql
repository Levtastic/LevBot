CREATE TABLE
    stream_alerts
(
    id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    username TEXT NOT NULL,
    alert_channel_did TEXT NOT NULL,
    alert_format TEXT NOT NULL
);

CREATE INDEX
    stream_alerts_username
ON
    stream_alerts
    (
        username
    );


CREATE TABLE
    stream_alert_messages
(
    id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    stream_alert_id INTEGER NOT NULL,
    channel_did TEXT NOT NULL,
    message_did TEXT NOT NULL
);

CREATE INDEX
    stream_alert_messages_stream_alert_id
ON
    stream_alert_messages
    (
        stream_alert_id
    );


CREATE TABLE
    admins
(
    id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    user_did TEXT NOT NULL,
    friendly_name TEXT NOT NULL
);

CREATE INDEX
    admins_user_did
ON
    admins
    (
        user_did
    );


CREATE TABLE
    command_aliases
(
    id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    command TEXT NOT NULL,
    alias TEXT NOT NULL
);

CREATE INDEX
    command_aliases_alias
ON
    command_aliases
    (
        alias
    );
