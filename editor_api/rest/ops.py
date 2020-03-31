from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project import base as project_base
from database.project.setup import SetupProjectDatabase
from database.project.config import Project_config
from database.project import ops
from database.project.ops import Graze_ops 

from database.datasets.setup import SetupDatasetsDatabase
from database.datasets import ops as ds

import ast

harvest_name = 'Harvest'
irrigation_name = 'Irrigation'
chemapp_name = 'ChemApp'
fire_name = 'Fire'
sweep_name = 'Sweep'

""" Operations Database - Graze"""
class GrazeOpsListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Graze_ops
		list_name = 'ops'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name, back_refs=True)


class GrazeOpsApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Graze_ops, 'Graze operation', back_refs=True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Graze_ops, 'Graze operation')

	def put(self, project_db, id):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('graze_ops', project_db)

			result = self.save_args(Graze_ops, args, id=id, lookup_fields=['fert'])

			if result > 0:
				return 200

			abort(400, message='Unable to update graze operation {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Graze operation name must be unique.')
		except Graze_ops.DoesNotExist:
			abort(404, message='Graze operation {id} does not exist'.format(id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class GrazeOpsUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Graze_ops)

	def put(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('graze_ops', project_db, True)
			lookup_fields = ['fert']

			param_dict = {}
			for key in args.keys():
				if args[key] is not None and key != 'selected_ids':
					if key in lookup_fields:
						d = ast.literal_eval(args[key])
						if int(d['id']) != 0:
							param_dict[key] = int(d['id'])
					else:
						param_dict[key] = args[key]

			query = Graze_ops.update(param_dict).where(Graze_ops.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update graze operations.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class GrazeOpsPostApi(BaseRestModel):
	def post(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('graze_ops', project_db)

			result = self.save_args(Graze_ops, args, is_new=True, lookup_fields=['fert'])

			if result > 0:
				return 201

			abort(400, message='Unable to update graze operation {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Graze operation name must be unique. ' + str(e))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class GrazeOpsDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Graze_ops, 'Graze operation', back_refs=True)
""" Operations Database - Graze"""


""" Operations Database - Harvest"""
class HarvOpsListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = ops.Harv_ops
		list_name = 'harvest'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class HarvOpsApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, ops.Harv_ops, harvest_name)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, ops.Harv_ops, harvest_name)

	def put(self, project_db, id):
		return self.base_put(project_db, id, ops.Harv_ops, harvest_name)


class HarvOpsUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, ops.Harv_ops)

	def put(self, project_db):
		return self.base_put_many(project_db, ops.Harv_ops, harvest_name)


class HarvOpsPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, ops.Harv_ops, harvest_name)


class HarvOpsDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Harv_ops, harvest_name)
""" Operations Database - Harvest"""

""" Operations Database - Irrigation"""
class IrrOpsListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = ops.Irr_ops
		list_name = 'irrigation'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class IrrOpsApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, ops.Irr_ops, irrigation_name)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, ops.Irr_ops, irrigation_name)

	def put(self, project_db, id):
		return self.base_put(project_db, id, ops.Irr_ops, irrigation_name)


class IrrOpsUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, ops.Irr_ops)

	def put(self, project_db):
		return self.base_put_many(project_db, ops.Irr_ops, irrigation_name)


class IrrOpsPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, ops.Irr_ops, irrigation_name)


class IrrOpsDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Irr_ops, irrigation_name)
""" Operations Database - Irrigation"""

""" Operations Database - Chemical Applications"""
class ChemAppOpsListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = ops.Chem_app_ops
		list_name = 'chem_app'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class ChemAppOpsApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, ops.Chem_app_ops, chemapp_name)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, ops.Chem_app_ops, chemapp_name)

	def put(self, project_db, id):
		return self.base_put(project_db, id, ops.Chem_app_ops, chemapp_name)


class ChemAppOpsUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, ops.Chem_app_ops)

	def put(self, project_db):
		return self.base_put_many(project_db, ops.Chem_app_ops, chemapp_name)


class ChemAppOpsPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, ops.Chem_app_ops, chemapp_name)


class ChemAppOpsDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Chem_app_ops, chemapp_name)
""" Operations Database - Chemical Application"""

""" Operations Database - Fire"""
class FireOpsListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = ops.Fire_ops
		list_name = 'fire'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class FireOpsApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, ops.Fire_ops, fire_name)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, ops.Fire_ops, fire_name)

	def put(self, project_db, id):
		return self.base_put(project_db, id, ops.Fire_ops, fire_name)


class FireOpsUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, ops.Fire_ops)

	def put(self, project_db):
		return self.base_put_many(project_db, ops.Fire_ops, fire_name)


class FireOpsPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, ops.Fire_ops, fire_name)


class FireOpsDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Fire_ops, fire_name)
""" Operations Database - Fire"""

""" Operations Database - Sweep"""
class SweepOpsListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = ops.Sweep_ops
		list_name = 'sweep'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class SweepOpsApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, ops.Sweep_ops, sweep_name)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, ops.Sweep_ops, sweep_name)

	def put(self, project_db, id):
		return self.base_put(project_db, id, ops.Sweep_ops, sweep_name)


class SweepOpsUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, ops.Sweep_ops)

	def put(self, project_db):
		return self.base_put_many(project_db, ops.Sweep_ops, sweep_name)	


class SweepOpsPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, ops.Sweep_ops, sweep_name)	

class SweepOpsDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Sweep_ops, sweep_name)
""" Operations Database - Sweep"""