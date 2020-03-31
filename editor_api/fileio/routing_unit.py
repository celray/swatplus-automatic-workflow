from .base import BaseFileModel
from helpers import utils, table_mapper
from database.project import connect
import database.project.routing_unit as db

from peewee import *


class Rout_unit(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Rout_unit_rtu
		order_by = db.Rout_unit_rtu.id

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				file.write(utils.int_pad("id"))
				file.write(utils.string_pad("name"))
				file.write(utils.string_pad("define"))
				file.write(utils.string_pad("dlr"))
				file.write(utils.string_pad("topo"))
				file.write(utils.string_pad("field"))
				file.write("\n")

				i = 1
				for row in table.select().order_by(order_by):
					file.write(utils.int_pad(i))
					i += 1
					file.write(utils.string_pad(row.name))
					file.write(utils.string_pad(row.name))
					file.write(utils.key_name_pad(row.dlr))
					file.write(utils.key_name_pad(row.topo))
					file.write(utils.key_name_pad(row.field))
					file.write("\n")


class Rout_unit_ele(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = connect.Rout_unit_ele
		order_by = connect.Rout_unit_ele.id

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				file.write(utils.int_pad("id"))
				file.write(utils.string_pad("name", direction="left"))
				file.write(utils.code_pad("obj_typ"))
				file.write(utils.int_pad("obj_id"))
				file.write(utils.num_pad("frac"))
				file.write(utils.string_pad("dlr"))
				file.write("\n")

				i = 1
				for row in table.select().order_by(order_by):
					file.write(utils.int_pad(i))
					i += 1
					file.write(utils.string_pad(row.name, direction="left"))
					file.write(utils.code_pad(row.obj_typ))
					file.write(utils.int_pad(row.obj_id))
					file.write(utils.exp_pad(row.frac))
					file.write(utils.key_name_pad(row.dlr, text_if_null="0"))
					file.write("\n")


class Rout_unit_dr(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Rout_unit_dr, True)


class Rout_unit_def(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = connect.Rout_unit_con
		order_by = connect.Rout_unit_con.id
		count = table.select().count()

		if count > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				file.write(utils.int_pad("id"))
				file.write(utils.string_pad("name"))
				file.write(utils.int_pad("elem_tot"))
				file.write(utils.int_pad("elements"))
				file.write("\n")

				i = 1
				for row in table.select().order_by(order_by):
					file.write(utils.int_pad(i))
					i += 1
					file.write(utils.string_pad(row.name))

					self.write_ele_ids(file, table, connect.Rout_unit_ele, row.elements)
					file.write("\n")
