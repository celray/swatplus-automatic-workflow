from peewee import *
import sqlite3
#import pyodbc
import database.lib as db_lib

db = SqliteDatabase(None)


class BaseModel(Model):
	class Meta:
		database = db


class Monthly_value(BaseModel):
	month = IntegerField()
	tmp_max_ave = DoubleField()
	tmp_min_ave = DoubleField()
	tmp_max_sd = DoubleField()
	tmp_min_sd = DoubleField()
	pcp_ave = DoubleField()
	pcp_sd = DoubleField()
	pcp_skew = DoubleField()
	wet_dry = DoubleField()
	wet_wet = DoubleField()
	pcp_days = DoubleField()
	pcp_hhr = DoubleField()
	slr_ave = DoubleField()
	dew_ave = DoubleField()
	wnd_ave = DoubleField()


class Wgn(BaseModel):
	name = CharField()
	desc = CharField(null=True)
	state = CharField(null=True)
	lat = DoubleField()
	lon = DoubleField()
	elev = DoubleField()
	rain_yrs = IntegerField()


class Wgn_mon(Monthly_value):
	wgn = ForeignKeyField(Wgn, related_name='monthly_values', on_delete='CASCADE')


class Wgn_cfsr_world(Wgn):
	pass


class Wgn_cfsr_world_mon(Monthly_value):
	wgn = ForeignKeyField(Wgn_cfsr_world, related_name='monthly_values', on_delete='CASCADE')


class Wgn_us(Wgn):
	pass


class Wgn_us_mon(Monthly_value):
	wgn = ForeignKeyField(Wgn_us, related_name='monthly_values', on_delete='CASCADE')


class SetupWgnDatabase:
	@staticmethod
	def create_tables():
		db.create_tables([Wgn, Wgn_mon])
		db.create_tables([Wgn_cfsr_world, Wgn_cfsr_world_mon])
		db.create_tables([Wgn_us, Wgn_us_mon])


class ImportWgn():
	@staticmethod
	def insert(db_file_name, db_table, wgn_table, wgn_monthly_value_table, start_id=1, is_mdb=True,
			   insert_db_obj=db):
		#if is_mdb:
			#odbc_conn_str = 'DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s' % db_file_name
			#conn = pyodbc.connect(odbc_conn_str)
		#else:
			#conn = sqlite3.connect(db_file_name)
		conn = sqlite3.connect(db_file_name)

		if not db_lib.exists_table(conn, db_table):
			raise ValueError("Table {table} does not exist in {file}.".format(table=db_table, file=db_file_name))

		cursor = conn.cursor().execute('select * from {table_name} order by OBJECTID'.format(table_name=db_table))
		ncols = len(cursor.description)
		col = [cursor.description[i][0] for i in range(ncols)]

		wgns = []
		monthly_values = []

		c = 0
		id = start_id
		for row in cursor.fetchall():
			wgn = {
				'id': id,
				'name': row[col.index('STATION')],
				'desc': row[col.index('LSTATION')],
				'state': None if row[col.index('STATE')] == 'NA' else row[col.index('STATE')],
				'lat': row[col.index('WLATITUDE')],
				'lon': row[col.index('WLONGITUDE')],
				'elev': row[col.index('WELEV')],
				'rain_yrs': row[col.index('RAIN_YRS')]
			}
			wgns.append(wgn)

			for i in range(1, 13):
				mval = {
					'wgn': id,
					'month': i,
					'tmp_max_ave': row[col.index('TMPMX%s' % i)],
					'tmp_min_ave': row[col.index('TMPMN%s' % i)],
					'tmp_max_sd': row[col.index('TMPSTDMX%s' % i)],
					'tmp_min_sd': row[col.index('TMPSTDMN%s' % i)],
					'pcp_ave': row[col.index('PCPMM%s' % i)],
					'pcp_sd': row[col.index('PCPSTD%s' % i)],
					'pcp_skew': row[col.index('PCPSKW%s' % i)],
					'wet_dry': row[col.index('PR_W1_%s' % i)],
					'wet_wet': row[col.index('PR_W2_%s' % i)],
					'pcp_days': row[col.index('PCPD%s' % i)],
					'pcp_hhr': row[col.index('RAINHHMX%s' % i)],
					'slr_ave': row[col.index('SOLARAV%s' % i)],
					'dew_ave': row[col.index('DEWPT%s' % i)],
					'wnd_ave': row[col.index('WNDAV%s' % i)]
				}
				monthly_values.append(mval)

			id += 1
			c += 1
			if c == 100:
				db_lib.bulk_insert(insert_db_obj, wgn_table, wgns)
				db_lib.bulk_insert(insert_db_obj, wgn_monthly_value_table, monthly_values)
				print('Saved {id} - {id2}'.format(id=wgns[0]['id'], id2=wgns[len(wgns) - 1]['id']))
				c = 0
				wgns.clear()
				monthly_values.clear()

		if len(wgns) > 0:
			db_lib.bulk_insert(insert_db_obj, wgn_table, wgns)
			db_lib.bulk_insert(insert_db_obj, wgn_monthly_value_table, monthly_values)
