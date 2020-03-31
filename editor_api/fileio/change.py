from .base import BaseFileModel, FileColumn as col
from database.project import base as project_base
from database.project import change as project_db
from database.datasets import base as datasets_base
from database.datasets import change as datasets_db
from database import lib as db_lib

from helpers import utils, table_mapper
import database.project.change as db


class Cal_parms_cal(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self, database ='project'):
		"""
		Read a cal_parms.cal text file into the database.
		:param database: project or datasets
		:return:
		"""
		file = open(self.file_name, "r")

		i = 1
		values = []
		for line in file:
			if i > 3:
				val = line.split()
				self.check_cols(val, 5, 'cal_parms')

				v = {
					'name': val[0].lower(),
					'obj_typ': val[1],
					'abs_min': val[2],
					'abs_max': val[3],
					'units': val[4] if val[4] != 'null' else None
				}
				values.append(v)
			i += 1

		if database == 'project':
			db_lib.bulk_insert(project_base.db, project_db.Cal_parms_cal, values)
		else:
			db_lib.bulk_insert(datasets_base.db, datasets_db.Cal_parms_cal, values)

	def write(self):
		self.write_default_table(db.Cal_parms_cal, True, write_cnt_line=True)


class Codes_sft(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Codes_sft

		if table.select().count() > 0:
			row = table.select().first()

			with open(self.file_name, 'w') as file:
				self.write_meta_line(file)
				header_cols = [col(table.hyd_hru, direction="left"),
							   col(table.hyd_hrulte, direction="left"),
							   col(table.plnt, direction="left"),
							   col(table.sed, direction="left"),
							   col(table.nut, direction="left"),
							   col(table.ch_sed, direction="left"),
							   col(table.ch_nut, direction="left"),
							   col(table.res, direction="left")]
				self.write_headers(file, header_cols)
				file.write("\n")

				utils.write_bool_yn(file, row.hyd_hru, direction="left")
				utils.write_bool_yn(file, row.hyd_hrulte, direction="left")
				utils.write_bool_yn(file, row.plnt, direction="left")
				utils.write_bool_yn(file, row.sed, direction="left")
				utils.write_bool_yn(file, row.nut, direction="left")
				utils.write_bool_yn(file, row.ch_sed, direction="left")
				utils.write_bool_yn(file, row.ch_nut, direction="left")
				utils.write_bool_yn(file, row.res, direction="left")
				file.write("\n")


class Calibration_cal(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Calibration_cal
		cal_elem_table = db.Calibration_cal_elem
		cal_cond_table = db.Calibration_cal_cond

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				self.write_meta_line(file)
				file.write(str(table.select().count()))
				file.write("\n")
				
				header_cols = [col(table.cal_parm, direction="left", padding_override=utils.DEFAULT_CODE_PAD),
							   col(table.chg_typ),
							   col(table.chg_val),
							   col("conds", not_in_db=True, padding_override=utils.DEFAULT_INT_PAD),
							   col(table.soil_lyr1),
							   col(table.soil_lyr2),
							   col(table.yr1),
							   col(table.yr2),
							   col(table.day1),
							   col(table.day2),
							   col("obj_tot", not_in_db=True, padding_override=utils.DEFAULT_INT_PAD)]
				self.write_headers(file, header_cols)
				file.write("\n")

				for row in table.select().order_by(table.id):
					row_cols = [col(row.cal_parm.name, direction="left", padding_override=utils.DEFAULT_CODE_PAD),
								col(row.chg_typ),
								col(row.chg_val),
								col(len(row.conditions)),
								col(row.soil_lyr1),
								col(row.soil_lyr2),
								col(row.yr1),
								col(row.yr2),
								col(row.day1),
								col(row.day2)]
					self.write_row(file, row_cols)

					self.write_ele_ids(file, table, cal_elem_table, row.elements)
					file.write("\n")

					for cond in row.conditions.order_by(cal_cond_table.id):
						row_cols = [col(" ", padding_override=2),
									col(cond.cond_typ, padding_override=12, direction="left"),
									col(cond.cond_op, padding_override=2),
									col(cond.cond_val, text_if_null="0", padding_override=8),
									col(cond.cond_val_text, direction="left")]
						self.write_row(file, row_cols)
						file.write("\n")


class Wb_parms_sft(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self, database ='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Wb_parms_sft, True, write_cnt_line=True)


class Ch_sed_parms_sft(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self, database ='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Ch_sed_parms_sft, True, write_cnt_line=True)


class Plant_parms_sft(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self, database ='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Plant_parms_sft, True, write_cnt_line=True)	
		
		
class Water_balance_sft(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Water_balance_sft
		item_table = db.Water_balance_sft_item

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				self.write_meta_line(file)
				file.write(str(table.select().count()))
				file.write("\n")
				
				header_cols = [col(table.name, direction="left"),
							   col("num", not_in_db=True, padding_override=utils.DEFAULT_INT_PAD)]
				self.write_headers(file, header_cols)
				file.write("\n")

				for row in table.select().order_by(table.id):
					row_cols = [col(row.name, direction="left"),
								col(len(row.items))]
					self.write_row(file, row_cols)
					file.write("\n")

					row_header_cols = [col(" ", not_in_db=True, padding_override=2),
								col(item_table.name, direction="left"),
								col(item_table.surq_rto),
								col(item_table.latq_rto),
								col(item_table.perc_rto),
								col(item_table.et_rto),
								col(item_table.tileq_rto),
								col(item_table.pet),
								col(item_table.sed),
								col(item_table.orgn),
								col(item_table.orgp),
								col(item_table.no3),
								col(item_table.solp)]
					self.write_headers(file, row_header_cols)
					file.write("\n")

					for item in row.items.order_by(item_table.id):
						row_cols = [col(" ", padding_override=2),
									col(item.name, direction="left"),
									col(item.surq_rto),
									col(item.latq_rto),
									col(item.perc_rto),
									col(item.et_rto),
									col(item.tileq_rto),
									col(item.pet),
									col(item.sed),
									col(item.orgn),
									col(item.orgp),
									col(item.no3),
									col(item.solp)]
						self.write_row(file, row_cols)
						file.write("\n")
		
		
class Ch_sed_budget_sft(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Ch_sed_budget_sft
		item_table = db.Ch_sed_budget_sft_item

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				self.write_meta_line(file)
				file.write(str(table.select().count()))
				file.write("\n")
				
				header_cols = [col(table.name, direction="left"),
							   col("num", not_in_db=True, padding_override=utils.DEFAULT_INT_PAD),
							   col("npsu", not_in_db=True, padding_override=utils.DEFAULT_INT_PAD)]
				self.write_headers(file, header_cols)
				file.write("\n")

				for row in table.select().order_by(table.id):
					row_cols = [col(row.name, direction="left"),
								col(len(row.items)),
								col(0)]
					self.write_row(file, row_cols)
					file.write("\n")

					row_header_cols = [col(" ", not_in_db=True, padding_override=2),
								col(item_table.name, direction="left"),
								col(item_table.cha_wide),
								col(item_table.cha_dc_accr),
								col(item_table.head_cut),
								col(item_table.fp_accr)]
					self.write_headers(file, row_header_cols)
					file.write("\n")

					for item in row.items.order_by(item_table.id):
						row_cols = [col(" ", padding_override=2),
									col(item.name, direction="left"),
									col(item.cha_wide),
									col(item.cha_dc_accr),
									col(item.head_cut),
									col(item.fp_accr)]
						self.write_row(file, row_cols)
						file.write("\n")
		
		
class Plant_gro_sft(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Plant_gro_sft
		item_table = db.Plant_gro_sft_item

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				self.write_meta_line(file)
				file.write(str(table.select().count()))
				file.write("\n")
				
				header_cols = [col(table.name, direction="left"),
							   col("num", not_in_db=True, padding_override=utils.DEFAULT_INT_PAD)]
				self.write_headers(file, header_cols)
				file.write("\n")

				for row in table.select().order_by(table.id):
					row_cols = [col(row.name, direction="left"),
								col(len(row.items))]
					self.write_row(file, row_cols)
					file.write("\n")

					row_header_cols = [col(" ", not_in_db=True, padding_override=2),
								col(item_table.name, direction="left"),
								col(item_table.yld),
								col(item_table.npp),
								col(item_table.lai_mx),
								col(item_table.wstress),
								col(item_table.astress),
								col(item_table.tstress)]
					self.write_headers(file, row_header_cols)
					file.write("\n")

					for item in row.items.order_by(item_table.id):
						row_cols = [col(" ", padding_override=2),
									col(item.name, direction="left"),
									col(item.yld),
									col(item.npp),
									col(item.lai_mx),
									col(item.wstress),
									col(item.astress),
									col(item.tstress)]
						self.write_row(file, row_cols)
						file.write("\n")			
