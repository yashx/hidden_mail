import sqlite3

class UserMessageHelper:
    """Class to help store messages that need to be send 
    and the email it needs to be sent to
    """

    def __init__(self, db_name):
        """
        Arguments:
            db_name {String} -- name of sqlite database to use
        """
        self.db_name = db_name
        sqlite_connection = sqlite3.connect(self.db_name)
        # to check if table exists in db
        sqlite_cursor = sqlite_connection.cursor()
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name='user_message_helper';"
        result = sqlite_cursor.execute(query).fetchall()
        if len(result) == 0:
            query = ''' CREATE TABLE user_message_helper (
                id TEXT PRIMARY KEY,
                email TEXT,
                message TEXT); '''
            sqlite_cursor.execute(query)
            sqlite_connection.commit()
        sqlite_cursor.close()
        sqlite_connection.close()

    @classmethod
    def default_db(cls):
        return cls("base.db")

    def store_message(self, psid, message):
        """Method to store messages of user. Messages are appended we called multiple times.

        Args:
            psid (String): Unique id of users
            message (String): Message to be sent
        """

        sqlite_connection = sqlite3.connect(self.db_name)
        sqlite_cursor = sqlite_connection.cursor()
        query = f"SELECT COUNT(1) FROM user_message_helper WHERE id='{psid}';"
        result = sqlite_cursor.execute(query).fetchall()
        if result[0][0] == 0:
            query = f"""INSERT INTO user_message_helper
            (id, message) VALUES ('{psid}', '{message}');"""
            sqlite_cursor.execute(query)
        else:
            query = f"SELECT message FROM user_message_helper WHERE id='{psid}';"
            res = sqlite_cursor.execute(query).fetchall()
            mess = None
            if res[0][0] is None:
                mess = message
            else:
                mess = '\n'.join((res[0][0], message))
            query = f"UPDATE user_message_helper set message = '{mess}' where id = '{psid}';"
            sqlite_cursor.execute(query)
        sqlite_connection.commit()
        sqlite_cursor.close()
        sqlite_connection.close()

    def store_email(self, psid, email):
        """Method to store email of user

        Args:
            psid (String): unique id of user
            email (String): email to send message to
        """
        sqlite_connection = sqlite3.connect(self.db_name)
        sqlite_cursor = sqlite_connection.cursor()
        query = f"SELECT COUNT(1) FROM user_message_helper WHERE id='{psid}';"
        result = sqlite_cursor.execute(query).fetchall()
        print(result)
        if result[0][0] == 0:
            query = f"""INSERT INTO user_message_helper
            (id, email) VALUES ('{psid}', '{email}');"""
            sqlite_cursor.execute(query)
        else:
            query = f"UPDATE user_message_helper set email = '{email}' where id = '{psid}';"
            sqlite_cursor.execute(query)
        sqlite_connection.commit()
        sqlite_cursor.close()
        sqlite_connection.close()

    def get_email(self, psid):
        """Get email of user

        Args:
            psid (String): unique id of user

        Returns:
            String: email of user. None if it doesn't exist
        """
        sqlite_connection = sqlite3.connect(self.db_name)
        sqlite_cursor = sqlite_connection.cursor()
        query = f"SELECT COUNT(1) FROM user_message_helper WHERE id='{psid}';"
        result = sqlite_cursor.execute(query).fetchall()
        if len(result) == 0:
            sqlite_cursor.close()
            sqlite_connection.close()
            return None
        else:
            query = f"SELECT email FROM user_message_helper WHERE id='{psid}';"
            res = sqlite_cursor.execute(query).fetchall()
            sqlite_cursor.close()
            sqlite_connection.close()
            return res[0][0]

    def get_message(self, psid):
        """Get full message that needs to be sent

        Args:
            psid (String): Unique id of user

        Returns:
            String: Message to send. None if user doesn't exist
        """
        sqlite_connection = sqlite3.connect(self.db_name)
        sqlite_cursor = sqlite_connection.cursor()
        query = f"SELECT COUNT(1) FROM user_message_helper WHERE id='{psid}';"
        result = sqlite_cursor.execute(query).fetchall()
        if len(result) == 0:
            sqlite_cursor.close()
            sqlite_connection.close()
            return None
        else:
            query = f"SELECT message FROM user_message_helper WHERE id='{psid}';"
            res = sqlite_cursor.execute(query).fetchall()
            sqlite_cursor.close()
            sqlite_connection.close()
            return res[0][0]

    def clear_message(self, psid):
        """Clear message that is stored

        Args:
            psid (String): Unique id of user
        """
        sqlite_connection = sqlite3.connect(self.db_name)
        sqlite_cursor = sqlite_connection.cursor()
        query = f"SELECT COUNT(1) FROM user_message_helper WHERE id='{psid}';"
        result = sqlite_cursor.execute(query).fetchall()
        if len(result) != 0:
            query = f"UPDATE user_message_helper set message = NULL where id = '{psid}';"
            sqlite_cursor.execute(query)
            sqlite_connection.commit()
        sqlite_cursor.close()
        sqlite_connection.close()

    def drop_user(self, psid):
        """Delete user

        Args:
            psid (String): Unique id of user
        """
        sqlite_connection = sqlite3.connect(self.db_name)
        sqlite_cursor = sqlite_connection.cursor()
        query = f"SELECT COUNT(1) FROM user_message_helper WHERE id='{psid}';"
        result = sqlite_cursor.execute(query).fetchall()
        if len(result) != 0:
            query = f"DELETE FROM user_message_helper WHERE id='{psid}';"
        sqlite_cursor.close()
        sqlite_connection.close()