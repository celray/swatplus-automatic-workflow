from .base import BaseFileModel
from helpers import utils
import database.project.hydrology as db


class Field_fld(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Field_fld, True)


class Topography_hyd(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		if db.Topography_hyd.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				file.write(utils.string_pad("name", direction="left"))
				file.write(utils.num_pad("slp"))
				file.write(utils.num_pad("slp_len"))
				file.write(utils.num_pad("lat_len"))
				file.write(utils.num_pad("dist_cha"))
				file.write(utils.num_pad("depos"))
				file.write("\n")

				self.write_rows(file, db.Topography_hyd.select().where(db.Topography_hyd.type == "hru"))
				self.write_rows(file, db.Topography_hyd.select().where(db.Topography_hyd.type == "sub"))

	def write_rows(self, file, items):
		for row in items.order_by(db.Topography_hyd.id):
			file.write(utils.string_pad(row.name, direction="left"))
			file.write(utils.num_pad(row.slp))
			file.write(utils.num_pad(row.slp_len))
			file.write(utils.num_pad(row.lat_len))
			file.write(utils.num_pad(row.dist_cha))
			file.write(utils.num_pad(row.depos))
			file.write("\n")


class Hydrology_hyd(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		if db.Hydrology_hyd.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				file.write(utils.string_pad("name", direction="left"))
				file.write(utils.num_pad("lat_ttime"))
				file.write(utils.num_pad("lat_sed"))
				file.write(utils.num_pad("can_max"))
				file.write(utils.num_pad("esco"))
				file.write(utils.num_pad("epco"))
				file.write(utils.num_pad("orgn_enrich"))
				file.write(utils.num_pad("orgp_enrich"))
				file.write(utils.num_pad("cn3_swf"))
				file.write(utils.num_pad("bio_mix"))
				file.write(utils.num_pad("perco"))
				file.write(utils.num_pad("lat_orgn"))
				file.write(utils.num_pad("lat_orgp"))
				file.write(utils.num_pad("harg_pet"))
				file.write(utils.num_pad("latq_co"))
				file.write("\n")

				for row in db.Hydrology_hyd.select().order_by(db.Hydrology_hyd.id):
					file.write(utils.string_pad(row.name, direction="left"))
					file.write(utils.num_pad(row.lat_ttime))
					file.write(utils.num_pad(row.lat_sed))
					file.write(utils.num_pad(row.can_max))
					file.write(utils.num_pad(row.esco))
					file.write(utils.num_pad(row.epco))
					file.write(utils.num_pad(row.orgn_enrich))
					file.write(utils.num_pad(row.orgp_enrich))
					file.write(utils.num_pad(row.cn3_swf))
					file.write(utils.num_pad(row.bio_mix))
					file.write(utils.num_pad(row.perco))
					file.write(utils.num_pad(row.lat_orgn))
					file.write(utils.num_pad(row.lat_orgp))
					file.write(utils.num_pad(row.harg_pet))
					file.write(utils.num_pad(row.latq_co))
					file.write("\n")
