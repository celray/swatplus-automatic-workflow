'''
date        : 31/03/2020
description : this module contains a class for managing sqlite databases
              easily

author      : Celray James CHAWANDA
contact     : celray.chawanda@outlook.com
licence     : MIT 2020
'''

import sqlite3
import sys
import pandas


class sqlite_connection:
    def __init__(self, sqlite_database):
        self.db_name = sqlite_database
        self.connection = None
        self.cursor = None

    def connect(self, report_ = False):
        self.connection = None
        self.connection = sqlite3.connect(self.db_name)
        self.cursor = self.connection.cursor()
        if report_:
            report("\t-> connection to " + self.db_name + " established...")
    
    def update_value(self, table_name, col_name, new_value, col_where1, val_1, report_ = False):
        """
        does not work yet!
        """
        if not new_value is None:
            new_value = str(new_value)
            self.cursor.execute("UPDATE " + table_name + " SET " + col_name + " = '" + new_value + "' WHERE " + col_where1 + " = " + val_1 + ";")
        if new_value is None:
            self.cursor.execute("UPDATE " + table_name + " SET " + col_name + " = ? " + " WHERE " + col_where1 + " = ?", (new_value, val_1))
        # self.cursor.execute(sql_str)
        if report_:
            report("\t -> updated {1} value in {0}".format(self.db_name.split("/")[-1].split("\\")[-1], table_name))

    def create_table(self, table_name, initial_field_name, data_type):
        '''
        can be text, real, etc
        '''
        try:
            self.cursor.execute('''CREATE TABLE ''' + table_name + '(' + initial_field_name + ' ' + data_type + ')')
            report("\t-> created table " + table_name + " in " + self.db_name)
        except:
            report("\t! table exists")

    def rename_table(self, old_table_name, new_table_name):
        """
        this function gives a new name to an existing table and saves the changes
        """
        self.cursor.execute("ALTER TABLE " + old_table_name +  " RENAME TO " + new_table_name)
        report("\t-> renamed " + old_table_name + " to " + new_table_name)
        self.commit_changes()

    def table_exists(self, table_name):
        self.cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table_name}'".format(table_name = table_name))
        if self.cursor.fetchone()[0] ==1:
            return True
        else:
            return False

    def delete_rows(self, table_to_clean, col_where = None, col_where_value = None, report_ = False):
        """

        """

        if (col_where is None) and (col_where_value is None):
            self.connection.execute("DELETE FROM " + table_to_clean)

        elif (not col_where is None) and (not col_where_value is None):
            self.connection.execute("DELETE FROM " + table_to_clean + " WHERE " + col_where + " = " + col_where_value + ";")

        else:
            raise ("\t! not all arguments were provided for selective row deletion")

        if report_:
            report("\t-> removed all rows from " + table_to_clean)

    def delete_table(self, table_name):
        """
        this function deletes the specified table
        """
        self.cursor.execute('''DROP TABLE ''' + table_name)
        report("\t-> deleted table " + table_name + " from " + self.db_name)


    def undo_changes(self):
        """
        This function reverts the database to status before last commit
        """
        report("\t-> undoing changes to " + self.db_name + " then saving")
        self.connection.rollback()
        self.commit_changes()

    def read_table_columns(self, table_name, column_list = "all", report_ = False):
        """
        this function takes a list to be a string separated by commmas and
        a table and puts the columns in the table into a variable

        "all" to select all columns
        """
        if column_list == "all":
            self.cursor = self.connection.execute("SELECT * from " + table_name)
        else:
            self.cursor = self.connection.execute("SELECT " + ",".join(column_list) + " from " + table_name)
            
        list_of_tuples = []
        for row in self.cursor:
            list_of_tuples.append(row)
        self.cursor = self.connection.cursor()
        if report_:
            report("\t-> read selected table columns from " + table_name)
        return list_of_tuples
        
    def insert_field(self, table_name, field_name, data_type, to_new_line = False, messages = True):
        """
        This will insert a new field into your sqlite database

        table_name: an existing table
        field_name: the field you want to add
        data_type : text, integer, float or real
        """
        self.cursor.execute("alter table " + table_name + " add column " + field_name + " " + data_type)
        if messages:
            if to_new_line:
                report("\t-> inserted into table {0} field {1}".format(table_name, field_name))
            else:
                sys.stdout.write("\r\t-> inserted into table {0} field {1}            ".format(table_name, field_name))
                sys.stdout.flush()

    def insert_row(self, table_name, ordered_content_list, messages = False):
        """
        ordered_list such as ['ha','he','hi']
        list should have data as strings
        """

        self.cursor.execute("INSERT INTO " + table_name + " VALUES(" + "'" + "','".join(ordered_content_list) + "'" + ')')
        if messages:
            report("\t-> inserted row into " + table_name)
    
    def insert_rows(self, table_name, list_of_tuples, messages = False):
        """
        list_of_tuples such as [('ha','he','hi')'
                                ('ha','he','hi')]
        not limited to string data
        """
        self.cursor.executemany('INSERT INTO ' + table_name + ' VALUES (?{qmarks})'.format(
            qmarks = ",?" * (len(list_of_tuples[0]) - 1)), list_of_tuples)
        if messages:
            report("\t-> inserted roes into " + table_name)

    def dump_csv(self, table_name, file_name, index = False, report_ = False):
        '''
        save table to csv
        '''
        tmp_conn = sqlite3.connect(self.db_name)
        df = pandas.read_sql_query("SELECT * FROM {tn}".format(tn = table_name), tmp_conn)
        df = df.replace('\n','',regex=True)
        df.to_csv(file_name) if index else df.to_csv(file_name, index = False)
        
        if report_:
            report("\t-> dumped table {0} to {1}".format(table_name, file_name))

    def commit_changes(self, report_ = False):

        '''
        save changes to the database.
        '''
        self.connection.commit()
        number_of_changes = self.connection.total_changes
        if report_:
            report("\t-> saved {0} changes to ".format(number_of_changes) + self.db_name)

    def close_connection(self, commit = True):
        '''
        disconnects from the database
        '''
        if commit:
            self.commit_changes()
        self.connection.close()
        report("\t-> closed connection to " + self.db_name)

def report(string, printing = True):
    if printing:
        print (string)
    else:
        sys.stdout.write("\r" + string)
        sys.stdout.flush()