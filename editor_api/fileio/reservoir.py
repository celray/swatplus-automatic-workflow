from .base import BaseFileModel, FileColumn as col
from peewee import *
from helpers import utils
from database.project import init
import database.project.reservoir as db


class Reservoir_res(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Reservoir_res
		order_by = db.Reservoir_res.id

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				file.write(utils.int_pad("id"))
				file.write(utils.string_pad("name", direction="left"))
				file.write(utils.string_pad("init"))
				file.write(utils.string_pad("hyd"))
				file.write(utils.string_pad("rel"))
				file.write(utils.string_pad("sed"))
				file.write(utils.string_pad("nut"))
				file.write("\n")

				for row in table.select().order_by(order_by):
					file.write(utils.int_pad(row.id))
					file.write(utils.string_pad(row.name, direction="left"))
					file.write(utils.key_name_pad(row.init, default_pad=utils.DEFAULT_STR_PAD))
					file.write(utils.key_name_pad(row.hyd, default_pad=utils.DEFAULT_STR_PAD))
					file.write(utils.key_name_pad(row.rel, default_pad=utils.DEFAULT_STR_PAD))
					file.write(utils.key_name_pad(row.sed, default_pad=utils.DEFAULT_STR_PAD))
					file.write(utils.key_name_pad(row.nut, default_pad=utils.DEFAULT_STR_PAD))
					file.write("\n")


class Hydrology_res(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Hydrology_res, True)


class Initial_res(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Initial_res
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


class Sediment_res(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Sediment_res, True)


class Nutrients_res(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Nutrients_res, True)


class Weir_res(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Weir_res, True)


class Wetland_wet(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Wetland_wet
		order_by = db.Wetland_wet.id

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				file.write(utils.int_pad("id"))
				file.write(utils.string_pad("name", direction="left"))
				file.write(utils.string_pad("init"))
				file.write(utils.string_pad("hyd"))
				file.write(utils.string_pad("rel"))
				file.write(utils.string_pad("sed"))
				file.write(utils.string_pad("nut"))
				file.write("\n")

				for row in table.select().order_by(order_by):
					file.write(utils.int_pad(row.id))
					file.write(utils.string_pad(row.name, direction="left"))
					file.write(utils.key_name_pad(row.init, default_pad=utils.DEFAULT_STR_PAD))
					file.write(utils.key_name_pad(row.hyd, default_pad=utils.DEFAULT_STR_PAD))
					file.write(utils.key_name_pad(row.rel, default_pad=utils.DEFAULT_STR_PAD))
					file.write(utils.key_name_pad(row.sed, default_pad=utils.DEFAULT_STR_PAD))
					file.write(utils.key_name_pad(row.nut, default_pad=utils.DEFAULT_STR_PAD))
					file.write("\n")


class Hydrology_wet(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Hydrology_wet, True)
