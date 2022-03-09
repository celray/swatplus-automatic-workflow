from .base import BaseFileModel, FileColumn as col
from peewee import *
from helpers import utils
from database.project import soils, decision_table, hru_parm_db
import database.project.hru as db


class Hru_data_hru(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Hru_data_hru
		order_by = db.Hru_data_hru.id

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				file.write(utils.int_pad("id"))
				file.write(utils.string_pad("name", direction="left"))
				file.write(utils.string_pad("topo"))
				file.write(utils.string_pad("hydro"))
				file.write(utils.string_pad("soil"))
				file.write(utils.string_pad("lu_mgt"))
				file.write(utils.string_pad("soil_plant_init"))
				file.write(utils.string_pad("surf_stor"))
				file.write(utils.string_pad("snow"))
				file.write(utils.string_pad("field"))
				file.write("\n")

				for row in table.select().order_by(order_by):
					file.write(utils.int_pad(row.id))
					file.write(utils.string_pad(row.name, direction="left"))
					file.write(utils.key_name_pad(row.topo))
					file.write(utils.key_name_pad(row.hydro))
					file.write(utils.key_name_pad(row.soil))
					file.write(utils.key_name_pad(row.lu_mgt))
					file.write(utils.key_name_pad(row.soil_plant_init))
					file.write(utils.key_name_pad(row.surf_stor))
					file.write(utils.key_name_pad(row.snow))
					file.write(utils.string_pad(row.field))
					file.write("\n")


class Hru_lte_hru(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Hru_lte_hru

		grow_start = decision_table.D_table_dtl.alias()
		grow_end = decision_table.D_table_dtl.alias()
		
		query = (table.select(table.id, 
							table.name,
							table.area,
							table.cn2,
							table.cn3_swf,
							table.t_conc,
							table.soil_dp,
							table.perc_co,
							table.slp,
							table.slp_len,
							table.et_co,
							table.aqu_sp_yld,
							table.alpha_bf,
							table.revap,
							table.rchg_dp,
							table.sw_init,
							table.aqu_init,
							table.aqu_sh_flo,
							table.aqu_dp_flo,
							table.snow_h2o,
							table.lat,
							soils.Soils_lte_sol.name.alias('soil_text'),
							table.trop_flag,
							grow_start.name.alias('grow_start'),
							grow_end.name.alias('grow_end'),
							hru_parm_db.Plants_plt.name.alias('plnt_typ'),
							table.stress,
							table.pet_flag,
							table.irr_flag,
							table.irr_src,
							table.t_drain,
							table.usle_k,
							table.usle_c,
							table.usle_p,
							table.usle_ls)
					  .join(soils.Soils_lte_sol, JOIN.LEFT_OUTER)
					  .switch(table)
					  .join(grow_start, JOIN.LEFT_OUTER, on=(table.grow_start == grow_start.id).alias('grow_start'))
					  .switch(table)
					  .join(grow_end, JOIN.LEFT_OUTER, on=(table.grow_end == grow_end.id).alias('grow_end'))
					  .switch(table)
					  .join(hru_parm_db.Plants_plt, JOIN.LEFT_OUTER)
					  .order_by(table.id))

		self.write_custom_query_table(table, query, ignore_id_col=False)
