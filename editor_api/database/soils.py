from peewee import *
import sqlite3
#import pyodbc
import database.lib
db_lib = database.lib

db = SqliteDatabase(None)


class BaseModel(Model):
	class Meta:
		database = db


class Layer(BaseModel):
	layer_num = IntegerField()
	dp = DoubleField()
	bd = DoubleField()
	awc = DoubleField()
	soil_k = DoubleField()
	carbon = DoubleField()
	clay = DoubleField()
	silt = DoubleField()
	sand = DoubleField()
	rock = DoubleField()
	alb = DoubleField()
	usle_k = DoubleField()
	ec = DoubleField()
	caco3 = DoubleField(null=True)
	ph = DoubleField(null=True)


class Soil(BaseModel):
	name = CharField()
	muid = CharField(null=True)
	seqn = IntegerField(null=True)
	s5id = CharField(null=True)
	cmppct = IntegerField(null=True)
	hyd_grp = CharField()
	dp_tot = DoubleField()
	anion_excl = DoubleField()
	perc_crk = DoubleField()
	texture = CharField()


class Soil_layer(Layer):
	soil = ForeignKeyField(Soil, on_delete = 'CASCADE', related_name='layers')


class Ssurgo(Soil):
	pass


class Ssurgo_layer(Layer):
	soil = ForeignKeyField(Ssurgo, on_delete='CASCADE', related_name='layers')


class Statsgo(Soil):
	pass


class Statsgo_layer(Layer):
	soil = ForeignKeyField(Statsgo, on_delete='CASCADE', related_name='layers')


class SetupSoilsDatabase():
	def create_tables(self):
		db.create_tables([Soil, Soil_layer])
		db.create_tables([Ssurgo, Ssurgo_layer])
		db.create_tables([Statsgo, Statsgo_layer])


class ImportSoils():
	def ssurgo(self, mdb_file_name):
		ImportSoils.insert(mdb_file_name, 'SSURGO_Soils', Ssurgo, Ssurgo_layer)

	def statsgo(self, mdb_file_name):
		self.statsgo_table(mdb_file_name, 'AlMUIDs')
		self.statsgo_table(mdb_file_name, 'ArMUIDs')
		self.statsgo_table(mdb_file_name, 'AzMUIDs')
		self.statsgo_table(mdb_file_name, 'CaMUIDs')
		self.statsgo_table(mdb_file_name, 'CoMUIDs')
		self.statsgo_table(mdb_file_name, 'CtMUIDs')
		self.statsgo_table(mdb_file_name, 'DeMUIDs')
		self.statsgo_table(mdb_file_name, 'FlMUIDs')
		self.statsgo_table(mdb_file_name, 'GaMUIDs')
		self.statsgo_table(mdb_file_name, 'IaMUIDs')
		self.statsgo_table(mdb_file_name, 'IdMUIDs')
		self.statsgo_table(mdb_file_name, 'IlMUIDs')
		self.statsgo_table(mdb_file_name, 'InMUIDs')
		self.statsgo_table(mdb_file_name, 'KsMUIDs')
		self.statsgo_table(mdb_file_name, 'KyMUIDs')
		self.statsgo_table(mdb_file_name, 'LaMUIDs')
		self.statsgo_table(mdb_file_name, 'MaMUIDs')
		self.statsgo_table(mdb_file_name, 'MdMUIDs')
		self.statsgo_table(mdb_file_name, 'MeMUIDs')
		self.statsgo_table(mdb_file_name, 'MiMUIDs')
		self.statsgo_table(mdb_file_name, 'MnMUIDs')
		self.statsgo_table(mdb_file_name, 'MoMUIDs')
		self.statsgo_table(mdb_file_name, 'MsMUIDs')
		self.statsgo_table(mdb_file_name, 'MtMUIDs')
		self.statsgo_table(mdb_file_name, 'NcMUIDs')
		self.statsgo_table(mdb_file_name, 'NdMUIDs')
		self.statsgo_table(mdb_file_name, 'NeMUIDs')
		self.statsgo_table(mdb_file_name, 'NhMUIDs')
		self.statsgo_table(mdb_file_name, 'NjMUIDs')
		self.statsgo_table(mdb_file_name, 'NmMUIDs')
		self.statsgo_table(mdb_file_name, 'NvMUIDs')
		self.statsgo_table(mdb_file_name, 'NyMUIDs')
		self.statsgo_table(mdb_file_name, 'OhMUIDs')
		self.statsgo_table(mdb_file_name, 'OkMUIDs')
		self.statsgo_table(mdb_file_name, 'OrMUIDs')
		self.statsgo_table(mdb_file_name, 'PaMUIDs')
		self.statsgo_table(mdb_file_name, 'RiMUIDs')
		self.statsgo_table(mdb_file_name, 'ScMUIDs')
		self.statsgo_table(mdb_file_name, 'SdMUIDs')
		self.statsgo_table(mdb_file_name, 'TnMUIDs')
		self.statsgo_table(mdb_file_name, 'TxMUIDs')
		self.statsgo_table(mdb_file_name, 'UtMUIDs')
		self.statsgo_table(mdb_file_name, 'VaMUIDs')
		self.statsgo_table(mdb_file_name, 'VtMUIDs')
		self.statsgo_table(mdb_file_name, 'WaMUIDs')
		self.statsgo_table(mdb_file_name, 'WiMUIDs')
		self.statsgo_table(mdb_file_name, 'WvMUIDs')
		self.statsgo_table(mdb_file_name, 'WyMUIDs')

	def statsgo_table(self, mdb_file_name, mdb_table):
		ImportSoils.insert(mdb_file_name, mdb_table, Statsgo, Statsgo_layer, False, Statsgo.select().count()+1)

	@staticmethod
	def insert(db_file_name, db_table, soil_table, soil_layer_table, insert_cal_ph=True, start_id=1, is_mdb=True, insert_db_obj=db):
		"""if is_mdb:
			odbc_conn_str = 'DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s' % db_file_name
			conn = pyodbc.connect(odbc_conn_str)
		else:
			conn = sqlite3.connect(db_file_name)"""
		conn = sqlite3.connect(db_file_name)

		"""if not db_lib.exists_table(conn, db_table):
			raise ValueError("Table {table} does not exist in {file}.".format(table=db_table, file=db_file_name))"""

		cursor = conn.cursor().execute('select * from {table_name} order by OBJECTID'.format(table_name=db_table))
		ncols = len(cursor.description)
		col = [cursor.description[i][0] for i in range(ncols)]

		soils = []
		layers = []

		c = 0
		id = start_id
		for row in cursor.fetchall():
			soil = {
				'id': id,
				'name': row[col.index('SNAM')],
				'muid': row[col.index('MUID')],
				'seqn': None if row[col.index('SEQN')] == '' else row[col.index('SEQN')],
				's5id': row[col.index('S5ID')],
				'cmppct': None if row[col.index('CMPPCT')] == '' else row[col.index('CMPPCT')],
				'hyd_grp': row[col.index('HYDGRP')],
				'dp_tot': row[col.index('SOL_ZMX')],
				'anion_excl': row[col.index('ANION_EXCL')],
				'perc_crk': row[col.index('SOL_CRK')],
				'texture': row[col.index('TEXTURE')]}
			soils.append(soil)

			for i in range(1, int(row[col.index('NLAYERS')]) + 1):
				cal = None
				ph = None
				if insert_cal_ph:
					cal = row[col.index('SOL_CAL%s' % i)]
					ph = row[col.index('SOL_PH%s' % i)]

				layer = {
					'soil': id,
					'layer_num': i,
					'dp': row[col.index('SOL_Z%s' % i)],
					'bd': row[col.index('SOL_BD%s' % i)],
					'awc': row[col.index('SOL_AWC%s' % i)],
					'soil_k': row[col.index('SOL_K%s' % i)],
					'carbon': row[col.index('SOL_CBN%s' % i)],
					'clay': row[col.index('CLAY%s' % i)],
					'silt': row[col.index('SILT%s' % i)],
					'sand': row[col.index('SAND%s' % i)],
					'rock': row[col.index('ROCK%s' % i)],
					'alb': row[col.index('SOL_ALB%s' % i)],
					'usle_k': row[col.index('USLE_K%s' % i)],
					'ec': row[col.index('SOL_EC%s' % i)],
					'caco3': cal,
					'ph': ph
				}
				layers.append(layer)

			id += 1
			c += 1
			if c == 100:
				db_lib.bulk_insert(insert_db_obj, soil_table, soils)
				db_lib.bulk_insert(insert_db_obj, soil_layer_table, layers)
				print('Saved {id} - {id2}'.format(id=soils[0]['id'], id2=soils[len(soils) - 1]['id']))
				c = 0
				soils.clear()
				layers.clear()

		if len(soils) > 0:
			print(soils[0])
			print(layers[0])
			db_lib.bulk_insert(insert_db_obj, soil_table, soils)
			db_lib.bulk_insert(insert_db_obj, soil_layer_table, layers)
