import sqlite3


class Highscore():

    def __init__(self):
        self.db = sqlite3.Connection('database.db')
        self.dbc = self.db.cursor()

        # check if database has the highscore tables
        self.create_and_fill_table_if_missing('highscore_easy')
        self.create_and_fill_table_if_missing('highscore_medium')
        self.create_and_fill_table_if_missing('highscore_hard')

    def has_table(self, table):
        table = self.dbc.execute(
            "SELECT name FROM sqlite_master \
            WHERE type='table' AND name=?", (table,)
        )
        return table.fetchone() is not None

    def create_and_fill_table_if_missing(self, table):
        if not self.has_table(table):
            self.dbc.execute(
                "CREATE TABLE " + table + "(\
                    id INTEGER PRIMARY KEY AUTOINCREMENT, \
                    time INTEGER, \
                    name TEXT \
                )"
            )
            for i in range(10):
                self.dbc.execute(
                    "INSERT INTO `" + table + "`(time, name) VALUES(999, '')"
                )
            self.db.commit()
            return True
        return False

    def get_all_entries(self, difficulty):
        table = 'highscore_' + difficulty
        entries = self.dbc.execute(
            "SELECT time, name FROM `" + table + "` ORDER BY time"
        )
        return entries.fetchall()

    def delete_entry(self, difficulty, time, limit=1):
        table = 'highscore_' + difficulty
        # self.dbc.execute(
        #     "DELETE FROM `" + table + "` WHERE time=? LIMIT ?", (time, limit)
        # )
        self.dbc.execute(
            "DELETE FROM `" + table + "` \
                WHERE id IN \
                (SELECT id FROM `" + table + "` WHERE time=? \
                ORDER BY time DESC LIMIT ?)",
            (time, limit)
        )
        self.db.commit()

    def delete_last_entry(self, difficulty):
        table = 'highscore_' + difficulty
        result = self.dbc.execute(
            "SELECT MAX(time) AS max_time FROM `" + table + "`"
        ).fetchone()
        self.delete_entry(difficulty, result[0])

    def delete_all_entries(self, difficulty):
        table = 'highscore_' + difficulty
        self.dbc.execute(
            "DROP TABLE " + table
        )
        self.create_and_fill_table_if_missing(table)

    def add_entry(self, difficulty, entry, delete_after=10):
        table = 'highscore_' + difficulty
        self.dbc.execute(
            "INSERT INTO `" + table + "`(time, name) VALUES(?, ?)",
            (entry[0], entry[1])
        )
        if delete_after and self.count_entries(difficulty) > delete_after:
            self.delete_last_entry(difficulty)

    def check_time_rank(self, difficulty, time):
        table = 'highscore_' + difficulty
        score = self.dbc.execute(
            "SELECT time FROM `" + table + "` WHERE time<? \
                ORDER BY time", (time,)
        ).fetchall()
        return len(score) + 1

    def count_entries(self, difficulty):
        # return len(self.get_all_entries(difficulty))
        table = 'highscore_' + difficulty
        return self.dbc.execute(
            "SELECT COUNT(*) FROM `" + table + "`"
        ).fetchone()[0]
