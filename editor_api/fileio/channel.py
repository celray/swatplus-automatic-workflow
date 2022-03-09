from .base import BaseFileModel, FileColumn as col
from peewee import *
from database.project import init
import database.project.channel as db
import database.project.link as link


class Initial_cha(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Initial_cha
		query = (table.select(table.name,
							  init.Om_water_ini.name.alias("org_min"),
							  init.Pest_water_ini.name.alias("pest"),
							  init.Path_water_ini.name.alias("path"),
							  init.Hmet_water_ini.name.alias("hmet"),
							  init.Salt_water_ini.name.alias("salt"),
							  table.description)
					  .join(init.Om_water_ini, JOIN.LEFT_OUTER)
					  .switch(table)
					  .join(init.Pest_water_ini, JOIN.LEFT_OUTER)
					  .switch(table)
					  .join(init.Path_water_ini, JOIN.LEFT_OUTER)
					  .switch(table)
					  .join(init.Hmet_water_ini, JOIN.LEFT_OUTER)
					  .switch(table)
					  .join(init.Salt_water_ini, JOIN.LEFT_OUTER)
					  .order_by(table.id))

		cols = [col(table.name, direction="left"),
				col(table.org_min, query_alias="org_min"),
				col(table.pest, query_alias="pest"),
				col(table.path, query_alias="path"),
				col(table.hmet, query_alias="hmet"),
				col(table.salt, query_alias="salt"),
				col(table.description, direction="left")]
		self.write_query(query, cols)


class Hydrology_cha(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Hydrology_cha, ignore_id_col=True, non_zero_min_cols=['wd','dp','slp','len','fps'])


class Sediment_cha(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Sediment_cha, ignore_id_col=True)


class Nutrients_cha(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Nutrients_cha, ignore_id_col=True)


class Channel_cha(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Channel_cha
		query = (table.select(table.id,
							  table.name,
							  db.Initial_cha.name.alias("cha_ini"),
							  db.Hydrology_cha.name.alias("cha_hyd"),
							  db.Sediment_cha.name.alias("cha_sed"),
							  db.Nutrients_cha.name.alias("cha_nut"))
					  .join(db.Initial_cha, JOIN.LEFT_OUTER)
					  .switch(table)
					  .join(db.Hydrology_cha, JOIN.LEFT_OUTER)
					  .switch(table)
					  .join(db.Sediment_cha, JOIN.LEFT_OUTER)
					  .switch(table)
					  .join(db.Nutrients_cha, JOIN.LEFT_OUTER)
					  .order_by(table.id))

		cols = [col(table.id),
				col(table.name, direction="left"),
				col(table.init, query_alias="cha_ini"),
				col(table.hyd, query_alias="cha_hyd"),
				col(table.sed, query_alias="cha_sed"),
				col(table.nut, query_alias="cha_nut")]
		self.write_query(query, cols)


class Hyd_sed_lte_cha(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Hyd_sed_lte_cha, ignore_id_col=True, non_zero_min_cols=['wd','dp','slp','len'])


class Channel_lte_cha(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Channel_lte_cha
		query = (table.select(table.id,
							  table.name,
							  db.Initial_cha.name.alias("cha_ini"),
							  db.Hyd_sed_lte_cha.name.alias("cha_hyd"),
							  db.Sediment_cha.name.alias("cha_sed"),
							  db.Nutrients_cha.name.alias("cha_nut"))
					  .join(db.Initial_cha, JOIN.LEFT_OUTER)
					  .switch(table)
					  .join(db.Hyd_sed_lte_cha, JOIN.LEFT_OUTER)
					  .switch(table)
					  .join(db.Sediment_cha, JOIN.LEFT_OUTER)
					  .switch(table)
					  .join(db.Nutrients_cha, JOIN.LEFT_OUTER)
					  .order_by(table.id))

		cols = [col(table.id),
				col(table.name, direction="left"),
				col(table.init, query_alias="cha_ini"),
				col(table.hyd, query_alias="cha_hyd"),
				col(table.sed, query_alias="cha_sed"),
				col(table.nut, query_alias="cha_nut")]
		self.write_query(query, cols)
