from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project import base as project_base
from database.project.setup import SetupProjectDatabase
from database.project.config import Project_config
from database.project.decision_table import D_table_dtl, D_table_dtl_act, D_table_dtl_act_out, D_table_dtl_cond, D_table_dtl_cond_alt
from database import lib
from helpers import table_mapper

class DTableDtlListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page, table_type):
		table = D_table_dtl
		list_name = 'decision_tables'
		SetupProjectDatabase.init(project_db)
		total = table.select().where(table.file_name == table_type).count()

		sort_val = SQL(sort)
		if reverse == 'true':
			sort_val = SQL(sort).desc()

		m = table.select().where(table.file_name == table_type).order_by(sort_val).paginate(int(page), int(items_per_page))
		ml = [{'id': v.id, 'name': v.name, 'conditions': len(v.conditions), 'actions': len(v.actions)} for v in m]

		return {'total': total, list_name: ml}


class DTableDtlApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, D_table_dtl, 'Decision table', back_refs=True, max_depth=2)
