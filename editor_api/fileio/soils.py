from .base import BaseFileModel, FileColumn as col
from peewee import *
from helpers import utils
import database.project.soils as db
import database.datasets.soils as db_ds
from database.project import base as project_base
from database.datasets import base as datasets_base


class Nutrients_sol(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Nutrients_sol, ignore_id_col=True, non_zero_min_cols=['exp_co'])


class Soils_sol(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		soils = db.Soils_sol.select().order_by(db.Soils_sol.id)
		layers = db.Soils_sol_layer.select().order_by(db.Soils_sol_layer.layer_num)
		query = prefetch(soils, layers)

		if soils.count() > 0:
			with open(self.file_name, 'w') as file:
				self.write_meta_line(file)
				header_cols = [col(db.Soils_sol.name, direction="left", padding_override=25),
							   col("nly", not_in_db=True, padding_override=utils.DEFAULT_INT_PAD),
							   col(db.Soils_sol.hyd_grp),
							   col(db.Soils_sol.dp_tot),
							   col(db.Soils_sol.anion_excl),
							   col(db.Soils_sol.perc_crk),
							   col(db.Soils_sol.texture, direction="left", padding_override=25)]
				self.write_headers(file, header_cols)

				total_pad = 122

				lt = db.Soils_sol_layer
				layer_cols = [col(lt.dp),
							  col(lt.bd),
							  col(lt.awc),
							  col(lt.soil_k),
							  col(lt.carbon),
							  col(lt.clay),
							  col(lt.silt),
							  col(lt.sand),
							  col(lt.rock),
							  col(lt.alb),
							  col(lt.usle_k),
							  col(lt.ec),
							  col(lt.caco3),
							  col(lt.ph)]
				self.write_headers(file, layer_cols)

				file.write("\n")

				for row in query:
					row_cols = [col(row.name, direction="left", padding_override=25),
								col(len(row.layers)),
								col(row.hyd_grp),
								col(row.dp_tot),
								col(row.anion_excl),
								col(row.perc_crk),
								col(row.texture, direction="left", padding_override=25)]
					self.write_row(file, row_cols)
					file.write("\n")

					for layer in row.layers:
						layer_row_cols = [col(" ", padding_override=total_pad),
										  col(layer.dp),
										  col(layer.bd),
										  col(layer.awc),
										  col(layer.soil_k),
										  col(layer.carbon),
										  col(layer.clay),
										  col(layer.silt),
										  col(layer.sand),
										  col(layer.rock),
										  col(layer.alb),
										  col(layer.usle_k),
										  col(layer.ec),
										  col(layer.caco3),
										  col(layer.ph)]
						self.write_row(file, layer_row_cols)
						file.write("\n")


class Soils_lte_sol(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database='project'):
		if database == 'project':
			self.read_default_table(db.Soils_lte_sol, project_base.db, 4, ignore_id_col=True)
		else:
			self.read_default_table(db_ds.Soils_lte_sol, datasets_base.db, 4, ignore_id_col=True)

	def write(self):
		self.write_default_table(db.Soils_lte_sol, ignore_id_col=True)
