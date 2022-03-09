from .base import BaseFileModel, FileColumn as col
from helpers import utils
import database.project.structural as db
import database.datasets.structural as db_datasets

from database.project import base as project_base
from database.datasets import base as datasets_base
from database import lib as db_lib


class Septic_str(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database ='project'):
		"""
		Read a septic.str text file into the database.
		:param database: project or datasets
		:return:
		"""
		file = open(self.file_name, "r")

		i = 1
		data = []
		for line in file:
			if i > 2:
				val = line.split()
				self.check_cols(val, 28, 'septic.str')

				d = {
					'name': val[0].lower(),
					'typ': val[1],
					'yr': val[2],
					'operation': val[3],
					'residents': val[4],
					'area': val[5],
					't_fail': val[6],
					'dp_bioz': val[7],
					'thk_bioz': val[8],
					'cha_dist': val[9],
					'sep_dens': val[10],
					'bm_dens': val[11],
					'bod_decay': val[12],
					'bod_conv': val[13],
					'fc_lin': val[14],
					'fc_exp': val[15],
					'fecal_decay': val[16],
					'tds_conv': val[17],
					'mort': val[18],
					'resp': val[19],
					'slough1': val[20],
					'slough2': val[21],
					'nit': val[22],
					'denit': val[23],
					'p_sorp': val[24],
					'p_sorp_max': val[25],
					'solp_slp': val[26],
					'solp_int': val[27]
				}
				data.append(d)
			i += 1

		if database == 'project':
			db_lib.bulk_insert(project_base.db, db.Septic_str, data)
		else:
			db_lib.bulk_insert(datasets_base.db, db_datasets.Septic_str, data)

	def write(self):
		self.write_default_table(db.Septic_str, True)


class Bmpuser_str(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database ='project'):
		"""
		Read a bmpuser.str text file into the database.
		:param database: project or datasets
		:return:
		"""
		file = open(self.file_name, "r")

		i = 1
		data = []
		for line in file:
			if i > 2:
				val = line.split()
				self.check_cols(val, 8, 'bmpuser.str')

				d = {
					'name': val[0].lower(),
					'flag': val[1],
					'sed_eff': val[2],
					'ptlp_eff': val[3],
					'solp_eff': val[4],
					'ptln_eff': val[5],
					'soln_eff': val[6],
					'bact_eff': val[7]
				}
				data.append(d)
			i += 1

		if database == 'project':
			db_lib.bulk_insert(project_base.db, db.Bmpuser_str, data)
		else:
			db_lib.bulk_insert(datasets_base.db, db_datasets.Bmpuser_str, data)

	def write(self):
		self.write_default_table(db.Bmpuser_str, True)


class Filterstrip_str(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database ='project'):
		"""
		Read a filterstrip.str text file into the database.
		:param database: project or datasets
		:return:
		"""
		file = open(self.file_name, "r")

		i = 1
		data = []
		for line in file:
			if i > 2:
				val = line.split()
				self.check_cols(val, 5, 'filterstrip.str')

				d = {
					'name': val[0].lower(),
					'flag': 0,
					'fld_vfs': val[1],
					'con_vfs': val[2],
					'cha_q': val[3],
					'description': val[4]
				}
				data.append(d)
			i += 1

		if database == 'project':
			db_lib.bulk_insert(project_base.db, db.Filterstrip_str, data)
		else:
			db_lib.bulk_insert(datasets_base.db, db_datasets.Filterstrip_str, data)

	def write(self):
		self.write_default_table(db.Filterstrip_str, True)


class Grassedww_str(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database ='project'):
		"""
		Read a grassedww.str text file into the database.
		:param database: project or datasets
		:return:
		"""
		file = open(self.file_name, "r")

		i = 1
		data = []
		for line in file:
			if i > 2:
				val = line.split()
				self.check_cols(val, 8, 'grassedww.str')

				d = {
					'name': val[0].lower(),
					'flag': 0,
					'mann': val[1],
					'sed_co': val[2],
					'dp': val[3],
					'wd': val[4],
					'len': val[5],
					'slp': val[6],
					'description': val[7]
				}
				data.append(d)
			i += 1

		if database == 'project':
			db_lib.bulk_insert(project_base.db, db.Grassedww_str, data)
		else:
			db_lib.bulk_insert(datasets_base.db, db_datasets.Grassedww_str, data)

	def write(self):
		self.write_default_table(db.Grassedww_str, True)


class Tiledrain_str(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database ='project'):
		"""
		Read a tiledrain.str text file into the database.
		:param database: project or datasets
		:return:
		"""
		file = open(self.file_name, "r")

		i = 1
		data = []
		for line in file:
			if i > 2:
				val = line.split()
				self.check_cols(val, 9, 'tiledrain.str')

				d = {
					'name': val[0].lower(),
					'dp': val[1],
					't_fc': val[2],
					'lag': val[3],
					'rad': val[4],
					'dist': val[5],
					'drain': val[6],
					'pump': val[7],
					'lat_ksat': val[8]
				}
				data.append(d)
			i += 1

		if database == 'project':
			db_lib.bulk_insert(project_base.db, db.Tiledrain_str, data)
		else:
			db_lib.bulk_insert(datasets_base.db, db_datasets.Tiledrain_str, data)

	def write(self):
		self.write_default_table(db.Tiledrain_str, True)
