from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *
import datetime

from .base import BaseRestModel
from database.project.setup import SetupProjectDatabase
from database.project.connect import Recall_con, Recall_con_out
from database.project.recall import Recall_rec, Recall_dat
from database.project.climate import Weather_sta_cli
from database.project.simulation import Time_sim
from database.project import base as project_base
from database import lib as db_lib

invalid_name_msg = 'Invalid name {name}. Please ensure the value exists in your database.'

class RecallConApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Recall_con, 'Recall', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Recall_con, 'Recall', 'rec', Recall_rec)

	def put(self, project_db, id):
		return self.put_con(project_db, id, 'rec', Recall_con, Recall_rec)


class RecallConPostApi(BaseRestModel):
	def post(self, project_db):
		return self.post_con(project_db, 'rec', Recall_con, Recall_rec)


class RecallConListApi(BaseRestModel):
	def get(self, project_db):
		table = Recall_con
		prop_table = Recall_rec
		filter_cols = [table.name, table.wst]
		table_lookups = {
			table.wst: Weather_sta_cli
		}
		props_lookups = {}

		items = self.base_connect_paged_items(project_db, table, prop_table, filter_cols, table_lookups, props_lookups)
		ml = []
		for v in items['model']:
			d = self.base_get_con_item_dict(v)
			d['rec_typ'] = v.rec.rec_typ
			ml.append(d)
		
		return {
			'total': items['total'],
			'matches': items['matches'],
			'items': ml
		}


class RecallConMapApi(BaseRestModel):
	def get(self, project_db):
		return self.get_con_map(project_db, Recall_con)


class RecallConOutApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Recall_con_out, 'Outflow', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Recall_con_out, 'Outflow')

	def put(self, project_db, id):
		return self.put_con_out(project_db, id, 'recall_con', Recall_con_out)


class RecallConOutPostApi(BaseRestModel):
	def post(self, project_db):
		return self.post_con_out(project_db, 'recall_con', Recall_con_out)


class RecallRecListApi(BaseRestModel):
	def get(self, project_db):
		table = Recall_rec
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols)


def get_recallrec_args(get_selected_ids=False):
	parser = reqparse.RequestParser()

	if get_selected_ids:
		parser.add_argument('selected_ids', type=int, action='append', required=False, location='json')
		parser.add_argument('elev', type=float, required=False, location='json')
		parser.add_argument('wst_name', type=str, required=False, location='json')
	else:
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('name', type=str, required=True, location='json')

	parser.add_argument('rec_typ', type=int, required=False, location='json')
	args = parser.parse_args(strict=False)
	return args


def update_recall_rec(db, m, id, sim, new_rec_typ):
	if m.rec_typ != new_rec_typ:
		Recall_dat.delete().where(Recall_dat.recall_rec_id==id).execute()
		rec = Recall_rec.get_or_none(Recall_rec.id == id)
		name = '' if rec is None else rec.name

		ob_typs = {
			1: 'pt_day',
			2: 'pt_mon',
			3: 'pt_yr',
			4: 'pt_const'
		}
		ob_typ = ob_typs.get(new_rec_typ, 'pt')

		years = 0
		months = 1
		days = 1
		start_day = 1
		start_month = 1
		insert_daily = False

		if new_rec_typ != 4:
			years = sim.yrc_end - sim.yrc_start
			if new_rec_typ != 3:
				start_date = datetime.datetime(sim.yrc_start, 1, 1) + datetime.timedelta(sim.day_start)
				end_date = datetime.datetime(sim.yrc_end, 1, 1) + datetime.timedelta(sim.day_end)
				if sim.day_end == 0:
					end_date = datetime.datetime(sim.yrc_end, 12, 31)

				start_month = start_date.month
				months = end_date.month
				
				if new_rec_typ != 2:
					insert_daily = True

		rec_data = []
		if not insert_daily:
			for x in range(years + 1):
				for y in range(start_month, months + 1):
					t_step = x + 1 if months == 1 else y
					data = {
						'recall_rec_id': id,
						'jday': 1,
						'mo': t_step if new_rec_typ == 1 or new_rec_typ == 2 else 1,
						'day_mo': 1,
						'yr': x + sim.yrc_start if new_rec_typ != 4 else 1,
						'ob_typ': ob_typ,
						'ob_name': name,
						'flo': 0,
						'sed': 0,
						'orgn': 0,
						'sedp': 0,
						'no3': 0,
						'solp': 0,
						'chla': 0,
						'nh3': 0,
						'no2': 0,
						'cbod': 0,
						'dox': 0,
						'sand': 0,
						'silt': 0,
						'clay': 0,
						'sag': 0,
						'lag': 0,
						'gravel': 0,
						'tmp': 0
					}
					rec_data.append(data)
		else:
			current_date = start_date
			while current_date <= end_date:
				curent_tt = current_date.timetuple()
				data = {
					'recall_rec_id': id,
					'jday': curent_tt.tm_yday,
					'mo': curent_tt.tm_mon,
					'day_mo': curent_tt.tm_mday,
					'yr': current_date.year,
					'ob_typ': ob_typ,
					'ob_name': name,
					'flo': 0,
					'sed': 0,
					'orgn': 0,
					'sedp': 0,
					'no3': 0,
					'solp': 0,
					'chla': 0,
					'nh3': 0,
					'no2': 0,
					'cbod': 0,
					'dox': 0,
					'sand': 0,
					'silt': 0,
					'clay': 0,
					'sag': 0,
					'lag': 0,
					'gravel': 0,
					'tmp': 0
				}
				rec_data.append(data)
				current_date = current_date + datetime.timedelta(1) 

		db_lib.bulk_insert(project_base.db, Recall_dat, rec_data)


class RecallRecApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Recall_rec, 'Recall', back_refs=False)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Recall_rec, 'Recall')

	def put(self, project_db, id):
		#return self.base_put(project_db, id, Recall_rec, 'Recall')
		table = Recall_rec
		item_description = 'Recall'
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args_reflect(table, project_db)

			sim = Time_sim.get_or_create_default()
			m = table.get(table.id==id)
			update_recall_rec(project_base.db, m, id, sim, args['rec_typ'])
			
			result = self.save_args(table, args, id=id)

			if result > 0:
				return 201

			abort(400, message='Unable to update {item} {id}.'.format(item=item_description.lower(), id=id))
		except IntegrityError as e:
			abort(400, message='{item} name must be unique. '.format(item=item_description) + str(e))
		except table.DoesNotExist:
			abort(404, message='{item} {id} does not exist'.format(item=item_description, id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class RecallRecUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Recall_rec)

	def put(self, project_db):
		SetupProjectDatabase.init(project_db)
		args = get_recallrec_args(True)

		try:
			param_dict = {}

			if args['rec_typ'] is not None:
				param_dict['rec_typ'] = args['rec_typ']

			con_table = Recall_con
			con_prop_field = Recall_con.rec_id
			prop_table = Recall_rec

			con_param_dict = {}
			if args['wst_name'] is not None:
				con_param_dict['wst_id'] = self.get_id_from_name(Weather_sta_cli, args['wst_name'])
			if args['elev'] is not None:
				con_param_dict['elev'] = args['elev']

			con_result = 1
			if (len(con_param_dict) > 0):
				con_query = con_table.update(con_param_dict).where(con_table.id.in_(args['selected_ids']))
				con_result = con_query.execute()

			if con_result > 0:
				result = 1
				if (len(param_dict) > 0):
					prop_ids = con_table.select(con_prop_field).where(con_table.id.in_(args['selected_ids']))
					query = prop_table.select().where(prop_table.id.in_(prop_ids))
					sim = Time_sim.get_or_create_default()
					for m in query:
						update_recall_rec(project_base.db, m, m.id, sim, args['rec_typ'])

					query2 = prop_table.update(param_dict).where(prop_table.id.in_(prop_ids))
					result = query2.execute()

				if result > 0:
					return 200

			abort(400, message='Unable to update routing unit properties.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class RecallRecPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Recall_rec, 'Recall')


class RecallDatApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Recall_dat, 'Recall')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Recall_dat, 'Recall')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Recall_dat, 'Recall')


class RecallDatPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Recall_dat, 'Recall')


class RecallDatListApi(BaseRestModel):
	def get(self, project_db, id):
		table = Recall_dat
		SetupProjectDatabase.init(project_db)
		args = self.get_table_args()

		sort = self.get_arg(args, 'sort', 'name')
		reverse = self.get_arg(args, 'reverse', 'n')
		page = self.get_arg(args, 'page', 1)
		per_page = self.get_arg(args, 'per_page', 50)
		
		s = table.select().where(table.recall_rec_id == id)
		total = s.count()

		if sort == 'name':
			sort_val = table.name if reverse != 'y' else table.name.desc()
		else:
			sort_val = SQL('[{}]'.format(sort))
			if reverse == 'y':
				sort_val = SQL('[{}]'.format(sort)).desc()

		m = s.order_by(sort_val).paginate(int(page), int(per_page))

		return {
			'total': total,
			'matches': total,
			'items': [model_to_dict(v, recurse=False) for v in m]
		}
