import sqlite3

from contextlib import closing


class Database:
    def __init__(self):
        self.database = sqlite3.connect('levbot.db')
        self.database.row_factory = sqlite3.Row
        if not self.database_exists():
            self.build_database()

    def database_exists(self):
        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                SELECT
                    COUNT(1)
                FROM
                    sqlite_master
                WHERE
                    type = 'table'
            """)
            return int(cursor.fetchone()[0]) > 0

    def build_database(self):
        query = ''

        with open('database.sql', 'r') as file:
            query = file.read()

        with closing(self.database.cursor()) as cursor:
            cursor.executescript(query)

        self.database.commit()

    def get_stream_alerts(self):
        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                SELECT
                    sa.id AS stream_alert_id,
                    sa.username,
                    sa.alert_channel_did,
                    sa.alert_format,
                    sam.channel_did AS message_channel_did,
                    sam.message_did
                FROM
                    stream_alerts AS sa
                LEFT OUTER JOIN
                    stream_alert_messages AS sam
                    ON
                        sam.stream_alert_id = sa.id
                ORDER BY
                    sa.username ASC
            """)

            return [row for row in cursor]

    def streamer_exists(self, username):
        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                SELECT
                    COUNT(1)
                FROM
                    stream_alerts
                WHERE
                    username = ?
            """,
                (username, )
            )
            return int(cursor.fetchone()[0]) > 0

    def add_streamer(self, username, alert_channel_did, alert_format=''):
        if self.streamer_exists(username):
            return False

        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                INSERT INTO
                    stream_alerts
                    (
                        username,
                        alert_channel_did,
                        alert_format
                    )
                VALUES
                    ( ?, ?, ? )
            """,
                (username, alert_channel_did, alert_format)
            )

        self.database.commit()

        return True

    def edit_streamer(self, username, alert_channel_did, alert_format=''):
        if not self.streamer_exists(username):
            return False

        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                UPDATE
                    stream_alerts
                SET
                    alert_channel_did = :alert_channel_did,
                    alert_format = :alert_format
                WHERE
                    username = :username
            """,
                {
                    'username': username,
                    'alert_channel_did': alert_channel_did,
                    'alert_format': alert_format
                }
            )

        self.database.commit()

        return True

    def remove_streamer(self, username):
        if not self.streamer_exists(username):
            return False

        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                DELETE FROM
                    stream_alerts
                WHERE
                    username = ?
            """,
                (username, )
            )

        self.database.commit()

        return True

    def get_streamers(self):
        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                SELECT
                    username,
                    alert_channel_did,
                    alert_format
                FROM
                    stream_alerts
                ORDER BY
                    username ASC
            """)

            return [row for row in cursor]

    def stream_alert_message_exists(self, message_did):
        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                SELECT
                    COUNT(1)
                FROM
                    stream_alert_messages
                WHERE
                    message_did = ?
            """,
                (message_did, )
            )
            return int(cursor.fetchone()[0]) > 0

    def add_stream_alert_message(self, stream_alert_id, channel_did, message_did):
        if self.stream_alert_message_exists(message_did):
            return False

        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                INSERT INTO
                    stream_alert_messages
                    (
                        stream_alert_id,
                        channel_did,
                        message_did
                    )
                VALUES
                    ( ?, ?, ? )
            """,
                (stream_alert_id, channel_did, message_did)
            )

        self.database.commit()

        return True

    def remove_stream_alert_message(self, message_did):
        if not self.stream_alert_message_exists(message_did):
            return False

        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                DELETE FROM
                    stream_alert_messages
                WHERE
                    message_did = ?
            """,
                (message_did, )
            )

        self.database.commit()

        return True

    def get_stream_alert_messages(self):
        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                SELECT
                    sa.username,
                    sam.channel_did,
                    sam.message_did
                FROM
                    stream_alert_messages AS sam
                LEFT OUTER JOIN
                    stream_alerts AS sa
                    ON
                        sa.id = sam.stream_alert_id
                ORDER BY
                    sa.username ASC
            """)

            return [row for row in cursor]

    def admin_exists(self, user_did):
        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                SELECT
                    COUNT(1)
                FROM
                    admins
                WHERE
                    user_did = ?
            """,
                (user_did, )
            )
            return int(cursor.fetchone()[0]) > 0

    def add_admin(self, user_did, friendly_name):
        if self.admin_exists(user_did):
            return False

        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                INSERT INTO
                    admins
                    (
                        user_did,
                        friendly_name
                    )
                VALUES
                    ( ?, ? )
            """,
                (user_did, friendly_name)
            )

        self.database.commit()

        return True

    def edit_admin(self, user_did, friendly_name):
        if not self.admin_exists(user_did):
            return False

        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                UPDATE
                    admins
                SET
                    friendly_name = :friendly_name,
                WHERE
                    user_did = :user_did
            """,
                {
                    'friendly_name': friendly_name,
                    'user_did': user_did
                }
            )

        self.database.commit()

        return True

    def remove_admin(self, user_did):
        if not self.admin_exists(user_did):
            return False

        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                DELETE FROM
                    admins
                WHERE
                    user_did = ?
            """,
                (user_did, )
            )

        self.database.commit()

        return True

    def get_admins(self):
        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                SELECT
                    user_did,
                    friendly_name
                FROM
                    admins
                ORDER BY
                    friendly_name ASC
            """)

            return [row for row in cursor]

    def alias_exists(self, alias):
        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                SELECT
                    COUNT(1)
                FROM
                    command_aliases
                WHERE
                    alias = ?
            """,
                (alias, )
            )
            return int(cursor.fetchone()[0]) > 0

    def add_alias(self, command, alias):
        if self.alias_exists(alias):
            return False

        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                INSERT INTO
                    command_aliases
                    (
                        command,
                        alias
                    )
                VALUES
                    ( ?, ? )
            """,
                (command, alias)
            )

        self.database.commit()

        return True

    def edit_alias(self, command, alias):
        if not self.alias_exists(alias):
            return False

        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                UPDATE
                    command_aliases
                SET
                    command = :command,
                WHERE
                    alias = :alias
            """,
                {
                    'command': command,
                    'alias': alias
                }
            )

        self.database.commit()

        return True

    def remove_alias(self, alias):
        if not self.alias_exists(alias):
            return False

        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                DELETE FROM
                    command_aliases
                WHERE
                    alias = ?
            """,
                (alias, )
            )

        self.database.commit()

        return True

    def get_aliases(self):
        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                SELECT
                    command,
                    alias
                FROM
                    command_aliases
                ORDER BY
                    command ASC
            """)

            return [row for row in cursor]

    def get_command_from_alias(self, alias):
        with closing(self.database.cursor()) as cursor:
            cursor.execute("""
                SELECT
                    command
                FROM
                    command_aliases
                WHERE
                    alias = ?
                ORDER BY
                    id DESC
                LIMIT 1
            """,
                (alias, )
            )
            result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return ''
