import os, sys
sys.path.insert(0, os.path.join(os.environ["swatplus_wf_dir"], "packages"))

from peewee import *
import sqlite3


def bulk_insert(db, table, data):
	if (len(data) > 0):
		max_vars = 999  # SQLite limit to the number of parameters in a query
		total_params = len(data[0]) * len(data)
		num_insert = max_vars if max_vars > total_params else int(max_vars / len(data[0]))

		with db.atomic():
			for idx in range(0, len(data), num_insert):
				table.insert_many(data[idx:idx + num_insert]).execute()


def open_db(name):
	conn = sqlite3.connect(name)
	# Let rows returned be of dict/tuple type
	conn.row_factory = sqlite3.Row
	return conn


def copy_table(table, src, dest, include_id=False):
	src_conn = open_db(src)
	dest_conn = open_db(dest)

	sc = src_conn.execute('SELECT * FROM %s' % table)
	ins = None
	dc = dest_conn.cursor()
	for row in sc.fetchall():
		if not ins:
			if include_id:
				cols = tuple([k for k in row.keys()])
			else:
				cols = tuple([k for k in row.keys() if k != 'id'])
			ins = 'INSERT OR REPLACE INTO %s %s VALUES (%s)' % (table, cols, ','.join(['?'] * len(cols)))
		c = [row[c] for c in cols]
		dc.execute(ins, c)

	dest_conn.commit()


def exists_table(db_conn, name):
	query = "SELECT 1 FROM sqlite_master WHERE type='table' and name = ?"
	return db_conn.execute(query, (name,)).fetchone() is not None


def get_table_names(db_conn):
	query = "SELECT name FROM sqlite_master WHERE type='table'"
	return db_conn.execute(query).fetchall()


def get_column_names(db_conn, table):
	query = "PRAGMA table_info('{table}');".format(table=table)
	return db_conn.execute(query).fetchall()


def get_matching_table_names(db_conn, partial_name):
	query = "SELECT name FROM sqlite_master WHERE type='table' and name like ?"
	name = partial_name + "%"
	return db_conn.execute(query, (name,)).fetchall()


def get_matching_table_names_wgn(db_conn, partial_name):
	query = "SELECT name FROM sqlite_master WHERE type='table' and name like ? and name not like '%_mon'"
	name = partial_name + "%"
	return db_conn.execute(query, (name,)).fetchall()


def delete_table(db, table):
	conn = sqlite3.connect(db)
	cursor = conn.cursor()
	cursor.execute("DROP TABLE {t}".format(t=table))
	conn.commit()


def execute_non_query(db, sql):
	conn = sqlite3.connect(db)
	cursor = conn.cursor()
	cursor.execute(sql)
	conn.commit()
