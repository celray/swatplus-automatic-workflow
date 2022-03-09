from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project import base as project_base
from database.project.setup import SetupProjectDatabase
from database.project.config import Project_config
from database.project.soils import Soils_sol, Soils_sol_layer, Nutrients_sol, Soils_lte_sol


class SoilsSolListApi(BaseRestModel):
	def get(self, project_db):
		table = Soils_sol
		filter_cols = [table.name, table.description, table.hyd_grp, table.texture]
		return self.base_paged_list(project_db, table, filter_cols)


class SoilsSolApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Soils_sol, 'Soil', back_refs=True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Soils_sol, 'Soil')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Soils_sol, 'Soil')


class SoilsSolPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Soils_sol, 'Soil')


class SoilsSolLayerApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Soils_sol_layer, 'Soil layer')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Soils_sol_layer, 'Soil layer')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Soils_sol_layer, 'Soil layer')


class SoilsSolLayerPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Soils_sol_layer, 'Soil layer', extra_args=[{'name': 'soil_id', 'type': int}])


class NutrientsSolListApi(BaseRestModel):
	def get(self, project_db):
		table = Nutrients_sol
		filter_cols = [table.name, table.description]
		return self.base_paged_list(project_db, table, filter_cols)


class NutrientsSolApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Nutrients_sol, 'Soil nutrients')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Nutrients_sol, 'Soil nutrients')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Nutrients_sol, 'Soil nutrients')


class NutrientsSolPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Nutrients_sol, 'Soil nutrients')


class NutrientsSolUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Nutrients_sol)

	def put(self, project_db):
		return self.base_put_many(project_db, Nutrients_sol, 'Soil nutrients')


class SoilsLteSolListApi(BaseRestModel):
	def get(self, project_db):
		table = Soils_lte_sol
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols)


class SoilsLteSolApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Soils_lte_sol, 'Soil')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Soils_lte_sol, 'Soil')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Soils_lte_sol, 'Soil')


class SoilsLteSolPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Soils_lte_sol, 'Soil')


class SoilsLteSolUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Soils_lte_sol)

	def put(self, project_db):
		return self.base_put_many(project_db, Soils_lte_sol, 'Soil')
