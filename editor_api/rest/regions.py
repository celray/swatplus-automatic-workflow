from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project import base as project_base
from database.project.setup import SetupProjectDatabase
from database.project.config import Project_config
from database.project.regions import Ls_unit_def, Ls_unit_ele


class LsUnitDefListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Ls_unit_def
		list_name = 'ls_units'

		SetupProjectDatabase.init(project_db)
		total = table.select().count()

		sort_val = SQL(sort)
		if reverse == 'true':
			sort_val = SQL(sort).desc()

		m = table.select().order_by(sort_val).paginate(int(page), int(items_per_page))
		ml = [{'id': v.id, 'name': v.name, 'area': v.area, 'num_elements': len(v.elements)} for v in m]

		return {'total': total, list_name: ml}


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
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Ls_unit_ele
		list_name = 'ls_unit_eles'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name, back_refs=True)


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