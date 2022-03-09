from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project import base as project_base
from database.project.setup import SetupProjectDatabase
from database.project.config import Project_config
from database.project.regions import Ls_unit_def, Ls_unit_ele


class LsUnitDefListApi(BaseRestModel):
	def get(self, project_db):
		table = Ls_unit_def
		filter_cols = [table.name]
		items = self.base_paged_items(project_db, table, filter_cols)
		m = items['model']
		ml = [{'id': v.id, 'name': v.name, 'area': v.area, 'num_elements': len(v.elements)} for v in m]

		return {
			'total': items['total'],
			'matches': items['matches'],
			'items': ml
		}


class LsUnitDefApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Ls_unit_def, 'Landscape unit', back_refs=True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Ls_unit_def, 'Landscape unit')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Ls_unit_def, 'Landscape unit')


class LsUnitDefPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Ls_unit_def, 'Landscape unit')


class LsUnitEleListApi(BaseRestModel):
	def get(self, project_db):
		table = Ls_unit_ele
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols, back_refs=True)


class LsUnitEleApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Ls_unit_ele, 'Landscape unit element', back_refs=True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Ls_unit_ele, 'Landscape unit element')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Ls_unit_ele, 'Landscape unit element')


class LsUnitElePostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Ls_unit_ele, 'Landscape unit element', extra_args=[{'name': 'ls_unit_def_id', 'type': int}])