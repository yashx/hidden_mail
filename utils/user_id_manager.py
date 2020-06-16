import sqlite3
import random

class UserIdManager:
    """
        Class to manage user id of users. It stores psid and contact id of users.
        It also stores passwords generated for user.
    """
    def __init__(self, db_name):
        """
        Arguments:
            db_name {String} -- name of sqlite database to use
        """
        self.db_name = db_name
        sqlite_connection = sqlite3.connect(self.db_name)
        # to check if the db has the table we are going to use and create it if not
        sqlite_cursor = sqlite_connection.cursor()
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name='user_id_list';"
        result = sqlite_cursor.execute(query).fetchall()
        if len(result) == 0:
            query = '''CREATE TABLE user_id_list (
                    contactId TEXT UNIQUE,
                    psid TEXT,
                    password TEXT PRIMARY KEY);'''
            sqlite_cursor.execute(query)
            sqlite_connection.commit()
        sqlite_cursor.close()
        sqlite_connection.close()


    @classmethod
    def default_db(cls):
        return cls("base.db")

    def generate_user_id(self, psid, first_name):
        first_name = first_name.casefold()
        num = random.randint(1000, 9999)
        while self.verify_password(f"{first_name} {num}"):
            num = random.randint(1000, 9999)
        psid_list = list(psid)
        length = len(psid_list)//2
        contact_id = random.sample(psid_list, length)
        random.shuffle(contact_id)
        while self.verify_contact_id("".join(contact_id)):
            contact_id = random.sample(psid_list, length)
            random.shuffle(contact_id)

        self.store_user_id(psid, "".join(contact_id), f"{first_name} {num}")
        return f"{first_name} {num}"

    def store_user_id(self, psid, contact_id, password):
        sqlite_connection = sqlite3.connect(self.db_name)
        sqlite_cursor = sqlite_connection.cursor()
        query = f"SELECT COUNT(1) FROM user_id_list WHERE psid = '{psid}';"
        result = sqlite_cursor.execute(query).fetchall()
        if result[0][0] == 0:
            query = f"""INSERT INTO user_id_list
                    (contactId, psid, password) 
                    VALUES ('{contact_id}', '{psid}', '{password}');"""
            print(query)
            sqlite_cursor.execute(query)
        else:
            query = f"""UPDATE user_id_list set contactId = '{contact_id}',
            password = '{password}' where psid = '{psid}';"""
            sqlite_cursor.execute(query)
        sqlite_connection.commit()
        sqlite_cursor.close()
        sqlite_connection.close()

    def get_contact_id(self, psid):
        sqlite_connection = sqlite3.connect(self.db_name)
        sqlite_cursor = sqlite_connection.cursor()

        query = f"SELECT COUNT(1) FROM user_id_list WHERE psid = '{psid}';"
        result = sqlite_cursor.execute(query).fetchall()
        if result[0][0] == 0:
            sqlite_cursor.close()
            sqlite_connection.close()
            return None

        else:
            query = f"SELECT contactId from user_id_list WHERE psid = '{psid}';"
            sqlite_cursor.execute(query)
            result = sqlite_cursor.fetchall()
            sqlite_cursor.close()
            sqlite_connection.close()
            return result[0][0]

    def verify_password(self, password):
        sqlite_connection = sqlite3.connect(self.db_name)
        sqlite_cursor = sqlite_connection.cursor()

        query = f"SELECT COUNT(1) FROM user_id_list WHERE password = '{password}';"
        result = sqlite_cursor.execute(query).fetchall()
        if result[0][0] == 0:
            return False
        else:
            return True

    def verify_contact_id(self, contact_id):
        sqlite_connection = sqlite3.connect(self.db_name)
        sqlite_cursor = sqlite_connection.cursor()

        query = f"SELECT COUNT(1) FROM user_id_list WHERE contactId = '{contact_id}';"
        result = sqlite_cursor.execute(query).fetchall()
        if result[0][0] == 0:
            return False
        else:
            return True