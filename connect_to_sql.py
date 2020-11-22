import os
import sys
import sqlite3

class SongDatabase:

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.conn.close()
        return isinstance(value, TypeError)

    def __init__(self, dbname: str):
        self.dbname = dbname+'.db' if not dbname.endswith('.db') else dbname
        self.tablename = 'song_info'
        self.path = os.path.join(os.getcwd(), self.dbname)
        try:
            self.conn = sqlite3.connect(self.path)
        except Exception as err:
            return err.args(0)

    def isTableExist(self, cursor):
        """ check if table exist inside a DB or not"""

        # if file exists
        if os.path.isfile(self.path):
            if sys.getsizeof(self.path) > 100:
                # data is stored in bytes
                with open(self.path, 'rb') as file:
                    dbheader = file.read(100)
                    # defines an sql db file.
                    if dbheader[0:16] == b'SQLite format 3\x00':
                        # Check if table exists or not
                        cursor.execute("""
                                            SELECT count(*)
                                            FROM sqlite_master
                                            WHERE type='table'
                                            AND name='song_info'
                        """)

                        return cursor.fetchone()[0]
        return False

    def feed_data(self, data: list):

        # Create a cursor
        cursor = self.conn.cursor()
        tablename = "song_info"

        # Create the table if not exists in DB (better than IF statement)
        cursor.execute(" CREATE TABLE IF NOT EXISTS {0} ( songs text UNIQUE ) ".format(self.tablename))

        # IGNORE INTO -> ignores the error message when inserting the data 
        # that already has been existed (especially in the unique key column)
        cursor.executemany(""" INSERT OR IGNORE INTO {0} (songs) VALUES (?) """.format(self.tablename), data)

        self.conn.commit()

    def retrieve_data(self):

        cursor = self.conn.cursor()
        exist = self.isTableExist(cursor)
        if not exist:
            return 'Doesn\'t Exist'

        # Get the songs column
        cursor.execute(""" SELECT songs FROM {0}""".format(self.tablename))
        
        # fetch the result
        print(cursor.fetchall())

        # commit the change to database
        self.conn.commit()
