from .base import BaseFileModel, FileColumn as col
from helpers import utils

from peewee import *

import database.project.simulation as db
from database.project.regions import Ls_unit_def
from database.project.connect import Rout_unit_con, Hru_con, Hru_lte_con, Modflow_con, Aquifer2d_con, Aquifer_con, Channel_con, Reservoir_con, Recall_con, Exco_con, Delratio_con, Outlet_con, Chandeg_con
from database.project.gis import Gis_subbasins, Gis_lsus


class Time_sim(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Time_sim, ignore_id_col=True)


class Object_prt(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Object_prt)


class Print_prt(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Print_prt

		if table.select().count() > 0:
			row = table.select().first()

			with open(self.file_name, 'w') as file:
				self.write_meta_line(file)
				header_cols = [col(table.nyskip, direction="left", padding_override=10),
							   col(table.day_start, direction="left"),
							   col(table.yrc_start, direction="left"),
							   col(table.day_end, direction="left"),
							   col(table.yrc_end, direction="left"),
							   col(table.interval, direction="left")]
				self.write_headers(file, header_cols)
				file.write("\n")

				row_cols = [col(row.nyskip, direction="left", padding_override=10),
							col(row.day_start, direction="left"),
							col(row.yrc_start, direction="left"),
							col(row.day_end, direction="left"),
							col(row.yrc_end, direction="left"),
							col(row.interval, direction="left")]
				self.write_row(file, row_cols)
				file.write("\n")

				aa_int_cnt = len(row.aa_ints)
				file.write(utils.int_pad("aa_int_cnt", default_pad=10, direction="left"))
				file.write("\n")
				file.write(utils.int_pad(aa_int_cnt, default_pad=10, direction="left"))

				if aa_int_cnt > 0:
					for aa_int in row.aa_ints:
						file.write(utils.int_pad(aa_int, direction="left"))

				file.write("\n")

				header_cols = [col(table.csvout, direction="left"),
							   col(table.dbout, direction="left"),
							   col(table.cdfout, direction="left")]
				self.write_headers(file, header_cols)
				file.write("\n")

				utils.write_bool_yn(file, row.csvout, direction="left")
				utils.write_bool_yn(file, row.dbout, direction="left")
				utils.write_bool_yn(file, row.cdfout, direction="left")
				file.write("\n")

				header_cols = [col(table.soilout, direction="left"),
							   col(table.mgtout, direction="left"),
							   col(table.hydcon, direction="left"),
							   col(table.fdcout, direction="left")]
				self.write_headers(file, header_cols)
				file.write("\n")

				utils.write_bool_yn(file, row.soilout, direction="left")
				utils.write_bool_yn(file, row.mgtout, direction="left")
				utils.write_bool_yn(file, row.hydcon, direction="left")
				utils.write_bool_yn(file, row.fdcout, direction="left")
				file.write("\n")

				obj_table = db.Print_prt_object
				header_cols = [col("objects", not_in_db=True, direction="left"),
							   col(obj_table.daily),
							   col(obj_table.monthly),
							   col(obj_table.yearly),
							   col(obj_table.avann)]
				self.write_headers(file, header_cols)
				file.write("\n")

				for obj in row.objects.order_by(obj_table.id):
					utils.write_string(file, obj.name, direction="left")
					utils.write_bool_yn(file, obj.daily)
					utils.write_bool_yn(file, obj.monthly)
					utils.write_bool_yn(file, obj.yearly)
					utils.write_bool_yn(file, obj.avann)
					file.write("\n")


class Object_cnt(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Object_cnt
		order_by = db.Object_cnt.id

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				self.write_meta_line(file)
				header_cols = [col(table.name, direction="left"),
							   col("ls_area", not_in_db=True, padding_override=utils.DEFAULT_NUM_PAD),
							   col("tot_area", not_in_db=True, padding_override=utils.DEFAULT_NUM_PAD),
							   col(table.obj),
							   col(table.hru),
							   col(table.lhru),
							   col(table.rtu),
							   col(table.mfl),
							   col(table.aqu),
							   col(table.cha),
							   col(table.res),
							   col(table.rec),
							   col(table.exco),
							   col(table.dlr),
							   col(table.can),
							   col(table.pmp),
							   col(table.out),
							   col(table.lcha),
							   col(table.aqu2d),
							   col(table.hrd),
							   col(table.wro)]
				self.write_headers(file, header_cols)
				file.write("\n")

				for row in table.select().order_by(order_by):
					ls_area = Ls_unit_def.select(fn.Sum(Ls_unit_def.area)).scalar()
					tot_area = Rout_unit_con.select(fn.Sum(Rout_unit_con.area)).scalar()

					file.write(utils.string_pad(row.name, direction="left"))
					file.write(utils.num_pad(ls_area))
					file.write(utils.num_pad(tot_area))

					hru = self.get_value_or_count(row.hru, Hru_con)
					lhru = self.get_value_or_count(row.lhru, Hru_lte_con)
					rtu = self.get_value_or_count(row.rtu, Rout_unit_con)
					mfl = self.get_value_or_count(row.mfl, Modflow_con)
					aqu = self.get_value_or_count(row.aqu, Aquifer_con)
					cha = self.get_value_or_count(row.cha, Channel_con)
					res = self.get_value_or_count(row.res, Reservoir_con)
					rec = self.get_value_or_count(row.rec, Recall_con)
					exco = self.get_value_or_count(row.exco, Exco_con)
					dlr = self.get_value_or_count(row.dlr, Delratio_con)
					out = self.get_value_or_count(row.out, Outlet_con)
					lcha = self.get_value_or_count(row.lcha, Chandeg_con)
					aqu2d = self.get_value_or_count(row.aqu2d, Aquifer2d_con)

					obj_tot = hru + lhru + rtu + mfl + aqu + cha + res + rec + exco + dlr + out + lcha + aqu2d
					obj_tot += row.can + row.pmp + row.hrd + row.wro

					file.write(utils.int_pad(obj_tot))

					file.write(utils.int_pad(hru))
					file.write(utils.int_pad(lhru))
					file.write(utils.int_pad(rtu))
					file.write(utils.int_pad(mfl))
					file.write(utils.int_pad(aqu))
					file.write(utils.int_pad(cha))
					file.write(utils.int_pad(res))
					file.write(utils.int_pad(rec))
					file.write(utils.int_pad(exco))
					file.write(utils.int_pad(dlr))

					file.write(utils.int_pad(row.can))
					file.write(utils.int_pad(row.pmp))

					file.write(utils.int_pad(out))
					file.write(utils.int_pad(lcha))
					file.write(utils.int_pad(aqu2d))

					file.write(utils.int_pad(row.hrd))
					file.write(utils.int_pad(row.wro))

					file.write("\n")

	def get_value_or_count(self, db_value, db_table):
		v = db_value
		if v == 0:
			v = db_table.select().count()

		return 0 if v is None else v
