import secrets
import sys

import mariadb
from flask import request, Response

import dbcreds


class xApiToken:
    conn = mariadb.connect(
        user=dbcreds.user,
        password=dbcreds.password,
        host=dbcreds.host,
        port=dbcreds.port,
        database=dbcreds.database
    )
    cursor = conn.cursor()

    def checkHasToken(self):
        if request.headers.getlist('X-Api-Key'):
            headerToken = request.headers['X-Api-Key']

            self.cursor.execute("SELECT EXISTS(SELECT id from token WHERE token=?)", [headerToken])
            checkTweet = self.cursor.fetchone()[0]
            return checkTweet == 1
        else:
            return False

    def makeNewApiToken(self):
        key = secrets.token_hex(16)

        self.cursor.execute("INSERT INTO token (`token`) VALUES (?)", [key])
        self.conn.commit()
        print(f"{self.cursor.rowcount} details inserted")

        return key

    def listToken(self):
        self.cursor.execute("SELECT token from token where status=1")
        rv = self.cursor.fetchall()
        for result in rv:
            print(result[0])


if len(sys.argv) > 1:
    cmd = sys.argv[1]
    if cmd.lower() == 'create':
        print('create token')
        token = xApiToken().makeNewApiToken()
        print(token, ' token created')
    elif cmd.lower() == 'list':
        print("All Api Token here")
        xApiToken().listToken()
    else:
        print("invalid arguments")
else:
    print("No arguments")
    exit()
