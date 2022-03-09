from .base import BaseFileModel, FileColumn as col
from helpers import utils
import database.project.ops as db
import database.datasets.ops as db_datasets

from database.project import base as project_base
from database.datasets import base as datasets_base
from database import lib as db_lib

from database.datasets.hru_parm_db import Fertilizer_frt


class Graze_ops(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database ='project'):
		"""
		Read a graze.ops text file into the database.
		:param database: project or datasets
		:return:
		"""
		file = open(self.file_name, "r")

		i = 1
		data = []
		for line in file:
			if i > 2:
				val = line.split()
				self.check_cols(val, 7, 'graze.ops')

				fert_name = val[1].strip().replace("-", "_")  # Replace '-' with '_' due to mismatch in files...
				try:
					fert = Fertilizer_frt.get(Fertilizer_frt.name == fert_name)

					d = {
						'name': val[0].lower(),
						'fert': fert.id,
						'bm_eat': val[2],
						'bm_tramp': val[3],
						'man_amt': val[4],
						'grz_bm_min': val[5],
						'description': val[6]
					}
					data.append(d)
				except Fertilizer_frt.DoesNotExist:
					raise ValueError("Could not find matching fertilizer {fert_name} in database.".format(fert_name=fert_name))

			i += 1

		if database == 'project':
			db_lib.bulk_insert(project_base.db, db.Graze_ops, data)
		else:
			db_lib.bulk_insert(datasets_base.db, db_datasets.Graze_ops, data)

	def write(self):
		table = db.Graze_ops
		order_by = db.Graze_ops.id

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				cols = [col(table.name, direction="left"),
						col(table.fert),
						col(table.bm_eat),
						col(table.bm_tramp),
						col(table.man_amt),
						col(table.grz_bm_min),
						col(table.description, is_desc=True)]
				self.write_headers(file, cols)
				file.write("\n")

				for row in table.select().order_by(order_by):
					file.write(utils.string_pad(row.name, direction="left"))
					file.write(utils.key_name_pad(row.fert))
					file.write(utils.num_pad(row.bm_eat))
					file.write(utils.num_pad(row.bm_tramp))
					file.write(utils.num_pad(row.man_amt))
					file.write(utils.num_pad(row.grz_bm_min))
					utils.write_desc_string(file, row.description)
					file.write("\n")


class Harv_ops(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database ='project'):
		"""
		Read a harv.ops text file into the database.
		:param database: project or datasets
		:return:
		"""
		file = open(self.file_name, "r")

		i = 1
		data = []
		for line in file:
			if i > 2:
				val = line.split()
				self.check_cols(val, 5, 'harv.ops')

				d = {
					'name': val[0].lower(),
					'harv_typ': val[1],
					'harv_idx': val[2],
					'harv_eff': val[3],
					'harv_bm_min': val[4]
				}
				data.append(d)
			i += 1

		if database == 'project':
			db_lib.bulk_insert(project_base.db, db.Harv_ops, data)
		else:
			db_lib.bulk_insert(datasets_base.db, db_datasets.Harv_ops, data)

	def write(self):
		self.write_default_table(db.Harv_ops, True)


class Irr_ops(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database ='project'):
		if database == 'project':
			self.read_default_table(db.Irr_ops, project_base.db, 0, ignore_id_col=True)
		else:
			self.read_default_table(db_datasets.Irr_ops, datasets_base.db, 0, ignore_id_col=True)

	def write(self):
		self.write_default_table(db.Irr_ops, True)


class Fire_ops(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database ='project'):
		"""
		Read a fire.ops text file into the database.
		:param database: project or datasets
		:return:
		"""
		file = open(self.file_name, "r")

		i = 1
		data = []
		for line in file:
			if i > 2:
				val = line.split()
				self.check_cols(val, 3, 'fire.ops')

				d = {
					'name': val[0].lower(),
					'chg_cn2': val[1],
					'frac_burn': val[2]
				}
				data.append(d)
			i += 1

		if database == 'project':
			db_lib.bulk_insert(project_base.db, db.Fire_ops, data)
		else:
			db_lib.bulk_insert(datasets_base.db, db_datasets.Fire_ops, data)

	def write(self):
		self.write_default_table(db.Fire_ops, True)


class Sweep_ops(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database ='project'):
		"""
		Read a sweep.ops text file into the database.
		:param database: project or datasets
		:return:
		"""
		file = open(self.file_name, "r")

		i = 1
		data = []
		for line in file:
			if i > 2:
				val = line.split()
				self.check_cols(val, 3, 'sweep.ops')

				d = {
					'name': val[0].lower(),
					'swp_eff': val[1],
					'frac_curb': val[2]
				}
				data.append(d)
			i += 1

		if database == 'project':
			db_lib.bulk_insert(project_base.db, db.Sweep_ops, data)
		else:
			db_lib.bulk_insert(datasets_base.db, db_datasets.Sweep_ops, data)

	def write(self):
		self.write_default_table(db.Sweep_ops, True)


class Chem_app_ops(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database ='project'):
		"""
		Read a chem_app.ops text file into the database.
		:param database: project or datasets
		:return:
		"""
		file = open(self.file_name, "r")

		i = 1
		data = []
		for line in file:
			if i > 2:
				val = line.split()
				self.check_cols(val, 9, 'chem_app.ops')

				d = {
					'name': val[0].lower(),
					'chem_form': val[1],
					'app_typ': val[2],
					'app_eff': val[3],
					'foliar_eff': val[4],
					'inject_dp': val[5],
					'surf_frac': val[6],
					'drift_pot': val[7],
					'aerial_unif': val[8]
				}
				data.append(d)
			i += 1

		if database == 'project':
			db_lib.bulk_insert(project_base.db, db.Chem_app_ops, data)
		else:
			db_lib.bulk_insert(datasets_base.db, db_datasets.Chem_app_ops, data)

	def write(self):
		self.write_default_table(db.Chem_app_ops, True)
