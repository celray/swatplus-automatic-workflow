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
from fileio.decision_table import D_table_dtl as file_dtable

from database.datasets.setup import SetupDatasetsDatabase
from database.datasets import decision_table as ds

special_tables = ['pl_hv_summer1', 'pl_hv_summer2', 'pl_hv_winter1']

def get_dtable_list(table, table_type, sort, reverse, page, per_page, filter_val):
	filter_cols = [table.name]
	selected_table = table.select().where(table.file_name == table_type)
	total = selected_table.count()

	if filter_val is not None:
		w = None
		for f in filter_cols:
			w = w | (f.contains(filter_val))
		s = selected_table.where(w)
	else:
		s = selected_table

	matches = s.count()

	sort_val = SQL('[{}]'.format(sort))
	if reverse == 'y':
		sort_val = SQL('[{}]'.format(sort)).desc()

	m = s.order_by(sort_val).paginate(int(page), int(per_page))
	ml = [{'id': v.id, 'name': v.name, 'conditions': len(v.conditions), 'actions': len(v.actions)} for v in m]

	return {
		'total': total,
		'matches': matches,
		'items': ml
	}

class DTableDtlListApi(BaseRestModel):
	def get(self, project_db, table_type):
		table = D_table_dtl
		SetupProjectDatabase.init(project_db)
		args = self.get_table_args()
		sort = self.get_arg(args, 'sort', 'name')
		reverse = self.get_arg(args, 'reverse', 'n')
		page = self.get_arg(args, 'page', 1)
		per_page = self.get_arg(args, 'per_page', 50)
		filter_val = self.get_arg(args, 'filter', None)
		return get_dtable_list(table, table_type, sort, reverse, page, per_page, filter_val)

class DTableDtlDatasetsListApi(BaseRestModel):
	def get(self, datasets_db, table_type):
		table = ds.D_table_dtl
		SetupDatasetsDatabase.init(datasets_db)
		args = self.get_table_args()
		sort = self.get_arg(args, 'sort', 'name')
		reverse = self.get_arg(args, 'reverse', 'n')
		page = self.get_arg(args, 'page', 1)
		per_page = self.get_arg(args, 'per_page', 50)
		filter_val = self.get_arg(args, 'filter', None)
		return get_dtable_list(table, table_type, sort, reverse, page, per_page, filter_val)


def get_dtable_args():
	parser = reqparse.RequestParser()

	parser.add_argument('id', type=int, required=False, location='json')
	parser.add_argument('name', type=str, required=True, location='json')
	parser.add_argument('file_name', type=str, required=True, location='json')
	parser.add_argument('description', type=str, required=False, location='json')
	parser.add_argument('conditions', type=list, required=False, location='json')
	parser.add_argument('actions', type=list, required=False, location='json')
	args = parser.parse_args(strict=False)
	return args


def save_dtable(args):
	table, created = D_table_dtl.get_or_create(name=args['name'], file_name=args['file_name'], description=args['description'])

	if not created:
		cond_ids = D_table_dtl_cond.select(D_table_dtl_cond.id).where(D_table_dtl_cond.d_table_id == table.id)
		act_ids = D_table_dtl_act.select(D_table_dtl_act.id).where(D_table_dtl_act.d_table_id == table.id)
		D_table_dtl_cond_alt.delete().where(D_table_dtl_cond_alt.cond_id.in_(cond_ids)).execute()
		D_table_dtl_act_out.delete().where(D_table_dtl_act_out.act_id.in_(act_ids)).execute()

		D_table_dtl_cond.delete().where(D_table_dtl_cond.d_table_id == table.id).execute()
		D_table_dtl_act.delete().where(D_table_dtl_act.d_table_id == table.id).execute()

	for c in args['conditions']:
		cond = D_table_dtl_cond()
		cond.d_table = table
		cond.var = c['var']
		cond.obj = c['obj']
		cond.obj_num = int(c['obj_num'])
		cond.lim_var = c['lim_var']
		cond.lim_op = c['lim_op']
		cond.lim_const = float(c['lim_const'])
		cond.description = c['description']
		cond.save()

		for l in c['alts']:
			alt = D_table_dtl_cond_alt()
			alt.cond = cond
			alt.alt = l['alt']
			alt.save()
	
	for a in args['actions']:
		act = D_table_dtl_act()
		act.d_table = table
		act.act_typ = a['act_typ']
		act.obj = a['obj']
		act.obj_num = int(a['obj_num'])
		act.name = a['name']
		act.option = a['option']
		act.const = a['const']
		act.const2 = a['const2']
		act.fp = a['fp']
		act.save()

		for o in a['outcomes']:
			oc = D_table_dtl_act_out()
			oc.act = act
			oc.outcome = o['outcome']
			oc.save()

	return table.id


class DTableDtlApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, D_table_dtl, 'Decision table', back_refs=True, max_depth=2)


class DTableDtlDatasetsApi(BaseRestModel):
	def get(self, datasets_db, id):
		return self.base_get_datasets(datasets_db, id, ds.D_table_dtl, 'Decision table', back_refs=True, max_depth=2)


class DTableDtlPostApi(BaseRestModel):
	def post(self, project_db):
		SetupProjectDatabase.init(project_db)
		try:
			args = get_dtable_args()
			if args['name'] in special_tables:
				abort(400, message='Decision table {} is reserved and cannot be modified or replaced. Please make a copy instead.'.format(args['name']))
			id = save_dtable(args)

			return {'id': id }, 201
		except IntegrityError as e:
			abort(400, message='Decision table name must be unique.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class DTableDtlPutTextApi(BaseRestModel):
	def put(self, project_db, id):
		SetupProjectDatabase.init(project_db)
		try:
			parser = reqparse.RequestParser()
			parser.add_argument('text', type=str, required=True, location='json')
			parser.add_argument('name', type=str, required=True, location='json')
			parser.add_argument('description', type=str, required=False, location='json')
			parser.add_argument('file_name', type=str, required=True, location='json')
			args = parser.parse_args(strict=False)

			file_processor = file_dtable(args['file_name'])
			file_processor.set_tables('project')
			i, new_table = file_processor.read_table(args['text'].splitlines(), 0, id)
			new_table.name = args['name']
			new_table.description = args['description']
			new_table.save()

			return {'id': new_table.id }, 201
		except D_table_dtl.DoesNotExist:
			abort(404, message='Decision table {id} does not exist'.format(id=id))
		except IndexError as e:
			abort(400, message='Error parsing decision table. {}'.format(e))
		except IntegrityError as e:
			abort(400, message='Decision table name must be unique.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))
