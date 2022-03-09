from .base import BaseFileModel
from helpers import utils, table_mapper
import database.project.regions as db
from database.project import connect

from peewee import *


class Ls_unit_def(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Ls_unit_def
		order_by = db.Ls_unit_def.id
		count = table.select().count()

		element_table = db.Ls_unit_ele
		first_elem = element_table.get()
		obj_table = table_mapper.obj_typs.get(first_elem.obj_typ, None)
		obj_ids = [o.id for o in obj_table.select(obj_table.id).order_by(obj_table.id)]

		if count > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				file.write(str(count))
				file.write("\n")
				file.write(utils.int_pad("id"))
				file.write(utils.string_pad("name"))
				file.write(utils.num_pad("area"))
				file.write(utils.int_pad("elem_tot"))
				file.write(utils.int_pad("elements"))
				file.write("\n")

				i = 1
				for row in table.select().order_by(order_by):
					file.write(utils.int_pad(i))
					i += 1
					file.write(utils.string_pad(row.name))
					file.write(utils.num_pad(row.area))

					self.write_ele_ids2(file, table, element_table, row.elements, obj_table, obj_ids, use_obj_id=False)
					file.write("\n")


class Ls_unit_ele(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Ls_unit_ele
		order_by = db.Ls_unit_ele.id

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				file.write(utils.int_pad("id"))
				file.write(utils.string_pad("name", direction="left"))
				file.write(utils.code_pad("obj_typ"))
				file.write(utils.int_pad("obj_typ_no"))
				file.write(utils.num_pad("bsn_frac"))
				file.write(utils.num_pad("sub_frac"))
				file.write(utils.num_pad("reg_frac"))
				file.write("\n")

				i = 1
				for row in table.select().order_by(order_by):
					file.write(utils.int_pad(i))
					i += 1
					file.write(utils.string_pad(row.name, direction="left"))
					file.write(utils.code_pad(row.obj_typ))
					file.write(utils.int_pad(row.obj_typ_no, default_pad=10))
					file.write(utils.exp_pad(row.bsn_frac, use_non_zero_min=True))
					file.write(utils.num_pad(row.sub_frac))
					file.write(utils.num_pad(row.reg_frac))
					file.write("\n")

class Aqu_catunit_ele(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = connect.Aquifer_con
		order_by = table.id

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				file.write(utils.int_pad("id"))
				file.write(utils.string_pad("name", direction="left"))
				file.write(utils.code_pad("obj_typ"))
				file.write(utils.int_pad("obj_typ_no", default_pad=10))
				file.write(utils.num_pad("bsn_frac"))
				file.write(utils.num_pad("sub_frac"))
				file.write(utils.num_pad("reg_frac"))
				file.write("\n")

				tot_area = connect.Rout_unit_con.select(fn.Sum(connect.Rout_unit_con.area)).scalar()

				i = 1
				for row in table.select().order_by(order_by):
					file.write(utils.int_pad(i))
					file.write(utils.string_pad(row.name, direction="left"))
					file.write(utils.code_pad("aqu"))
					file.write(utils.int_pad(i, default_pad=10))
					file.write(utils.num_pad(row.area/tot_area, use_non_zero_min=True))
					file.write(utils.num_pad(0))
					file.write(utils.num_pad(0))
					file.write("\n")
					i += 1
