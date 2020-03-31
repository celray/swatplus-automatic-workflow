from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project import base as project_base
from database.project.setup import SetupProjectDatabase
from database.project.config import Project_config
from database.project.basin import Parameters_bsn, Codes_bsn

from database.datasets.setup import SetupDatasetsDatabase
from database.datasets import basin as ds


class ParametersBsnApi(BaseRestModel):
	def get(self, project_db):
		return self.base_get(project_db, 1, Parameters_bsn, 'Basin parameters')

	def put(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('parameters_bsn', project_db)

			result = self.save_args(Parameters_bsn, args, id=1)

			if result > 0:
				return 200

			abort(400, message='Unable to update basin parameters.')
		except Parameters_bsn.DoesNotExist:
			abort(404, message='Could not find basin parameters in database.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class CodesBsnApi(BaseRestModel):
	def get(self, project_db):
		return self.base_get(project_db, 1, Codes_bsn, 'Basin codes')

	def put(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('codes_bsn', project_db)

			result = self.save_args(Codes_bsn, args, id=1)

			if result > 0:
				return 200

			abort(400, message='Unable to update basin codes.')
		except Codes_bsn.DoesNotExist:
			abort(404, message='Could not find basin codes in database.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))
