import logging

import sqlite3

from werkzeug.exceptions import abort

from src.chainratchet import ChainRatchet

class SQLiteChainRatchet(ChainRatchet):

    def __init__(self,config ):
        self.db=config["db"]

    def check(self, sig_type, level=0, round=0):
        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()
        try:
          item=cursor.execute("SELECT * FROM signature WHERE sigtype = ?",(sig_type,)).fetchone()
        except Exception as err:
          print(f"Unexpected {err=}, {type(err)=}")
        if item is None:
            cursor.execute("INSERT INTO signature VALUES(?,?,?)",(sig_type,level,round))
            connection.commit()
            connection.close()
            return True

        self.lastlevel = item[1]
        self.lastround = item[2]

        logging.debug(f"Current sig is {self.lastlevel}/{self.lastround}")

        super().check(sig_type, level, round)

        cursor.execute("UPDATE signature SET lastblock = ? , lastround = ? WHERE sigtype = ?",(level,round, sig_type))
        connection.commit()
        connection.close()
   
        return True

