"""
Class meant to create database and store data for different types of data
http://www.sqlitetutorial.net/
"""
import sqlite3, os
from sqlite3 import IntegrityError


class Sqlite3Database:

    def __init__(self, dbName, in_folder=""):
        """

        :param dbName: Name of database to create or connect to
        :param in_folder: subfolder to create or where db is in
        """
        if in_folder:
            try:
                os.mkdir(in_folder)
            except OSError:
                pass

        self._name = os.path.abspath(os.path.join(in_folder, dbName))
        self._connection = self.__connect_or_create_database()
        self._cursor = self.__set_cursor()
        self._column_names = list()


    def __connect_or_create_database(self):
        if self._name[-1] == "b" and self._name[-2] == "d":
            return sqlite3.connect(self._name)
        else:
            self._name += ".db"
            return sqlite3.connect(self._name)

    def __set_cursor(self):
        return self._connection.cursor()

    def delete_database(self):
        self.close_connection()
        os.remove(self._name)
        return True

    def create_table_if_not_exist(self, tableName, primary_key=None, **kwargs):
        """

        use this class function to create a table for database
        Check documentation for data types

        to create columns and specify datatype
        create_table_if_not_exist(tablename, column_name1='columntype', column_name2='columntype', etc)
        you can create as many column names and types as needed
        :param tableName: name of table
        :param kwargs: Key = name of column, value = Data type To determine the order place alphabets infront of keys.
                        ie A_Key, B_Key....a_key, b_key
        :return:Nothing
        """

        createTableText = "CREATE TABLE IF NOT EXISTS {}(".format(tableName)
        if kwargs is not None:

            for i in sorted(kwargs):
                if i[2:] == primary_key:
                    createTableText += "{} {} PRIMARY KEY,".format(i[2:], kwargs[i])
                    self._column_names.append(i[2:])
                    pass
                else:
                    createTableText += "{} {}, ".format(i[2:], kwargs[i])
                    self._column_names.append(i[2:])

            createTableText = createTableText[0:-2]

            createTableText += ")"

            self._cursor.execute(createTableText)

    def delete_data_from_table(self, tableName, wipeALLDATA=False, boolCriteria=None, **kwargs):
        if wipeALLDATA is True and boolCriteria is None:
            ans = input('This will wipe all data from your table. There is no undo. Would You like to Proceed? y/n')
            if ans == "y":
                ans1 = input("please confirm that you would like to wipe out all data from table. is this true? y/n")
                if ans1 == "y":
                    self._cursor.execute("DELETE FROM {}".format(tableName))
                    self._connection.commit()
        else:
            self._cursor.execute("DELETE FROM {} WHERE {}".format(tableName, boolCriteria))

    def update_data_in_table(self, tableName, dict_of_column_new_values, boolCriteria, **kwargs):
        """

        :param tableName:
        :param dict_of_column_new_values: dictionary with keys being column(s) to change
        :param boolCriteria: a string, should tell what row to set values like "name = 'john doe'" this will set
        row/rows where column name is 'john doe'
        :param kwargs:
        :return:
        """
        if not isinstance(dict_of_column_new_values, dict):
            return False
        d = ["{} = {}".format(k, v) for k, v in dict_of_column_new_values.items()]
        set_values = ", ".join(d)

        self._cursor.execute("UPDATE {} SET {} WHERE {}}".format(tableName, set_values, boolCriteria))
        self._connection.commit()

    def insert_into_table(self, tableName, **kwargs):
        """
        to create columns and specify datatype
        insert_into_table(tablename, column_name='String data', column_name=INTdata, etc)
        column_name MUST be part of the columns created for the table

        :param tableName: name of table to insert data to
        :param kwargs: key = name of column to insert, value = value to insert
        :return: True, if successful and -1 if not
        """
        if len(self._column_names) == 0:  # populate column names when new instance used to access existing db
            column_names = self.get_column_names(tableName=tableName)

            for i in column_names:
                self._column_names.append(i[1])

        insertTableText = "INSERT INTO {} (".format(tableName)
        list1 = list()

        if kwargs is not None:
            for i in kwargs:
                if i in self._column_names:
                    insertTableText += "{}, ".format(i)


            insertTableText = insertTableText[0:-2]
            insertTableText += ") VALUES("
            for i in kwargs:
                if i in self._column_names:
                    insertTableText += "?, "
                    list1.append(kwargs[i])
            list1 = tuple(list1)
            insertTableText = insertTableText[0:-2]
            insertTableText += ")"
            try:
                self._cursor.execute(insertTableText, list1)
                self._connection.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def select_data_from_table(self, tableName, columnsToSelect, boolCriteria=None, printSqlStatement=False,
                               column_for_sorting=None):
        """

        :param tableName: String name of table to select from

        :param columnsToSelect: a STRING OR LIST with comma separated names of columns to select ie
        columnsToSelect="column1, column2, column" or columnsToSelect = "max(column1)"
        IF columnToSelect="*" or "all" then every column is chosen


        :param boolCriteria: string with conditionals ie "column1 > 2" or "column1 = 3 AND ROWID >= 4" etc
                this will be the criterias http://www.sqlitetutorial.net/that must be met for each data. If left blank then column data will be shown
                for every record
        :return: returns the data
        """
        if isinstance(columnsToSelect, list):
            tempStr = ""
            for i in columnsToSelect:
                tempStr += "{}, ".format(i)

            columnsToSelect = tempStr[0:-2]
        elif isinstance(columnsToSelect, str) and (columnsToSelect == "*" or columnsToSelect.lower() == "all"):
            columnsToSelect = "*"
        elif isinstance(columnsToSelect, str):
            pass
        else:
            return False

        if boolCriteria is not None and isinstance(boolCriteria, str):
            selectDataText = "SELECT {} FROM {} WHERE {}".format(columnsToSelect, tableName,
                                                                 boolCriteria) if not column_for_sorting else \
                "SELECT {} FROM {} WHERE {} ORDER BY {} ASC".format(columnsToSelect, tableName, boolCriteria, column_for_sorting)
        else:

            selectDataText = "SELECT {} FROM {}".format(columnsToSelect, tableName) if not column_for_sorting else \
                "SELECT {} FROM {} ORDER BY {} ASC".format(columnsToSelect, tableName, column_for_sorting)

        print(selectDataText) if printSqlStatement else None

        return self._cursor.execute(selectDataText).fetchall()

    def get_column_names(self, tableName):
        return self._cursor.execute("PRAGMA table_info({})".format(tableName)).fetchall()

    def close_connection(self):
        self._cursor.close()
        self._connection.close()
        return "connection closed"

if __name__ == '__main__':
    TEXT = "TEXT"
    INT = "iNT"
    GLOB = "GLOB"
    REAL = "REAL"
    op_tx_database = Sqlite3Database(dbName="reg_op_tx.db")
    op_tx_database.create_table_if_not_exist(tableName="reg_non_verified", A_tx_hash=TEXT, B_timestamp=INT,
                                             C_tx_id=TEXT, D_type=TEXT, E_title=TEXT, F_desc=TEXT,
                                             G_price=REAL, H_num_of_items=INT, I_total=REAL, J_fee_type=TEXT,
                                             K_fee=REAL, L_duration=INT)

    column_names = op_tx_database.get_column_names("reg_non1_verified")
    print(column_names)
    op_tx_database.close_connection()

    def lol(**kwargs):
        for i in kwargs:
            print(i, kwargs[i])

    my_dict = {
        "samuel": 1,
        "anna": 2,
        "lizzy": 3
    }

    lol(**my_dict)