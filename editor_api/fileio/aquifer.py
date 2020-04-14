from .base import BaseFileModel, FileColumn as col
from peewee import *
from helpers import utils
from database.project import init, connect
import database.project.aquifer as db


class Aquifer_aqu(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Aquifer_aqu
		query = (table.select(table.id,
							table.name,
							db.Initial_aqu.name.alias('init'),
							table.gw_flo,
							table.dep_bot,
							table.dep_wt,
							table.no3_n,
							table.sol_p,
							table.ptl_n,
							table.ptl_p,
							table.bf_max,
							table.alpha_bf,
							table.revap,
							table.rchg_dp,
							table.spec_yld,
							table.hl_no3n,
							table.flo_min,
							table.revap_min)
					  .join(db.Initial_aqu, JOIN.LEFT_OUTER)
					  .order_by(table.id))

		self.write_custom_query_table(table, query, ignore_id_col=False)


class Initial_aqu(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Initial_aqu
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


class Chan_aqu_lin(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = connect.Aquifer_con
		order_by = connect.Aquifer_con.id
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

					self.write_ele_ids(file, table, connect.Aquifer_con_out, row.con_outs)
					file.write("\n")
