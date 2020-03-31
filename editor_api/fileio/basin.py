from .base import BaseFileModel
from database.project import base as project_base
from database.project import basin as project_basin
from database.datasets import base as datasets_base
from database.datasets import basin as datasets_basin
from database import lib as db_lib

from helpers import utils
import database.project.basin as db


class Codes_bsn(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self, database='project'):
		"""
		Read a codes.bsn text file into the database.
		:param database: project or datasets
		:return:
		"""
		if database == 'project':
			self.read_default_table(project_basin.Codes_bsn, project_base.db, 24, ignore_id_col=True)
		else:
			self.read_default_table(datasets_basin.Codes_bsn, datasets_base.db, 24, ignore_id_col=True)

	def write(self):
		self.write_default_table(db.Codes_bsn, True)


class Parameters_bsn(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self, database='project'):
		"""
		Read a parameters.bsn text file into the database.
		:param database: project or datasets
		:return:
		"""
		if database == 'project':
			self.read_default_table(project_basin.Parameters_bsn, project_base.db, 46, ignore_id_col=True)
		else:
			self.read_default_table(datasets_basin.Parameters_bsn, datasets_base.db, 46, ignore_id_col=True)

	def write(self):
		self.write_default_table(db.Parameters_bsn, True)
