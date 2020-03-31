from .base import BaseFileModel, FileColumn as col
from peewee import *
from helpers import utils
from database.project import soils
import database.project.init as db


class Plant_ini(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Plant_ini
		order_by = db.Plant_ini.id

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				file.write(utils.string_pad("pcom_name", direction="left"))
				file.write(utils.int_pad("plt_cnt"))
				file.write(utils.int_pad("rot_yr_ini"))
				file.write(utils.string_pad("plt_name", default_pad=utils.DEFAULT_KEY_PAD))
				file.write(utils.code_pad("lc_status"))
				file.write(utils.num_pad("lai_init"))
				file.write(utils.num_pad("bm_init"))
				file.write(utils.num_pad("phu_init"))
				file.write(utils.num_pad("plnt_pop"))
				file.write(utils.num_pad("yrs_init"))
				file.write(utils.num_pad("rsd_init"))
				file.write("\n")

				for row in table.select().order_by(order_by):
					file.write(utils.string_pad(row.name, direction="left"))
					file.write(utils.int_pad(row.plants.count()))
					file.write(utils.int_pad(row.rot_yr_ini))
					file.write("\n")

					for plant in row.plants:
						file.write(utils.string_pad("", text_if_null=""))
						file.write(utils.string_pad("", text_if_null="", default_pad=utils.DEFAULT_INT_PAD))
						file.write(utils.key_name_pad(plant.plnt_name))
						utils.write_bool_yn(file, plant.lc_status)
						file.write(utils.num_pad(plant.lai_init))
						file.write(utils.num_pad(plant.bm_init))
						file.write(utils.num_pad(plant.phu_init))
						file.write(utils.num_pad(plant.plnt_pop))
						file.write(utils.num_pad(plant.yrs_init))
						file.write(utils.num_pad(plant.rsd_init))
						file.write("\n")


class Om_water_ini(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Om_water_ini, ignore_id_col=True)


class Soil_plant_ini(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Soil_plant_ini
		query = (table.select(table.name,
							  table.sw_frac,
							  soils.Nutrients_sol.name.alias("nutrients"),
							  db.Pest_hru_ini.name.alias("pest"),
							  db.Path_hru_ini.name.alias("path"),
							  db.Hmet_hru_ini.name.alias("hmet"),
							  db.Salt_hru_ini.name.alias("salt"))
					  .join(soils.Nutrients_sol, JOIN.LEFT_OUTER)
					  .switch(table)
					  .join(db.Pest_hru_ini, JOIN.LEFT_OUTER)
					  .switch(table)
					  .join(db.Path_hru_ini, JOIN.LEFT_OUTER)
					  .switch(table)
					  .join(db.Hmet_hru_ini, JOIN.LEFT_OUTER)
					  .switch(table)
					  .join(db.Salt_hru_ini, JOIN.LEFT_OUTER)
					  .order_by(table.id))

		cols = [col(table.name, direction="left"),
				col(table.sw_frac),
				col(table.nutrients, query_alias="nutrients"),
				col(table.pest, query_alias="pest"),
				col(table.path, query_alias="path"),
				col(table.hmet, query_alias="hmet"),
				col(table.salt, query_alias="salt")]
		self.write_query(query, cols)


class Pest_hru_ini(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Pest_hru_ini
		order_by = db.Pest_hru_ini.id

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())				

				for row in table.select().order_by(order_by):
					file.write(utils.string_pad("name", direction="left", default_pad=25))
					file.write(utils.num_pad("plant"))
					file.write(utils.num_pad("soil"))
					file.write("\n")

					file.write(utils.string_pad(row.name, direction="left", default_pad=25))
					file.write("\n")

					for item in row.pest_hrus:
						file.write(utils.string_pad("", text_if_null="", default_pad=1))
						file.write(utils.key_name_pad(item.name, default_pad=22))
						file.write(utils.num_pad(item.plant))
						file.write(utils.num_pad(item.soil))
						file.write("\n")


class Pest_water_ini(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Pest_water_ini
		order_by = db.Pest_water_ini.id

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())				

				for row in table.select().order_by(order_by):
					file.write(utils.string_pad("name", direction="left", default_pad=25))
					file.write(utils.num_pad("water_sol"))
					file.write(utils.num_pad("water_sor"))
					file.write(utils.num_pad("benthic_sol"))
					file.write(utils.num_pad("benthic_sor"))
					file.write("\n")

					file.write(utils.string_pad(row.name, direction="left", default_pad=25))
					file.write("\n")

					for item in row.pest_waters:
						file.write(utils.string_pad("", text_if_null="", default_pad=1))
						file.write(utils.key_name_pad(item.name, default_pad=22))
						file.write(utils.num_pad(item.water_sol))
						file.write(utils.num_pad(item.water_sor))
						file.write(utils.num_pad(item.benthic_sol))
						file.write(utils.num_pad(item.benthic_sor))
						file.write("\n")


class Path_hru_ini(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Path_hru_ini
		order_by = db.Path_hru_ini.id

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())				

				for row in table.select().order_by(order_by):
					file.write(utils.string_pad("name", direction="left", default_pad=25))
					file.write(utils.num_pad("plant"))
					file.write(utils.num_pad("soil"))
					file.write("\n")

					file.write(utils.string_pad(row.name, direction="left", default_pad=25))
					file.write("\n")

					for item in row.path_hrus:
						file.write(utils.string_pad("", text_if_null="", default_pad=1))
						file.write(utils.key_name_pad(item.name, default_pad=22))
						file.write(utils.num_pad(item.plant))
						file.write(utils.num_pad(item.soil))
						file.write("\n")


class Path_water_ini(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Path_water_ini
		order_by = db.Path_water_ini.id

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())				

				for row in table.select().order_by(order_by):
					file.write(utils.string_pad("name", direction="left", default_pad=25))
					file.write(utils.num_pad("water_sol"))
					file.write(utils.num_pad("water_sor"))
					file.write(utils.num_pad("benthic_sol"))
					file.write(utils.num_pad("benthic_sor"))
					file.write("\n")

					file.write(utils.string_pad(row.name, direction="left", default_pad=25))
					file.write("\n")

					for item in row.path_waters:
						file.write(utils.string_pad("", text_if_null="", default_pad=1))
						file.write(utils.key_name_pad(item.name, default_pad=22))
						file.write(utils.num_pad(item.water_sol))
						file.write(utils.num_pad(item.water_sor))
						file.write(utils.num_pad(item.benthic_sol))
						file.write(utils.num_pad(item.benthic_sor))
						file.write("\n")
