import psycopg2
from psycopg2.extras import RealDictCursor
from model.User import User

class UserRepository:
    def __init__(self):
        self.connection = psycopg2.connect(
            dbname="medintel",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )

    def getUserByUsername(self, username):
        query = """SELECT username, password, "userType" FROM "User" WHERE username = %s;"""
        with (self.connection.cursor(cursor_factory=RealDictCursor) as cursor):
            cursor.execute(query, (username,))
            res = cursor.fetchone()
            if res is None:
                return None
            userFromDB = User()
            userFromDB.createUserFromDB(res)
            return userFromDB

    def addUser(self, user: User):
        query = """INSERT INTO "User" (username, password, "userType") VALUES (%s, %s, %s);"""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (user.getUsername(), user.getPassword(), user.getUserType()))
            self.connection.commit()
