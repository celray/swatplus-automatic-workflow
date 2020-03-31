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

def get_con_args():
	parser = reqparse.RequestParser()
	parser.add_argument('id', type=int, required=False, location='json')
	parser.add_argument('name', type=str, required=True, location='json')
	parser.add_argument('gis_id', type=int, required=False, location='json')
	parser.add_argument('area', type=float, required=True, location='json')
	parser.add_argument('lat', type=float, required=True, location='json')
	parser.add_argument('lon', type=float, required=True, location='json')
	parser.add_argument('elev', type=float, required=False, location='json')
	parser.add_argument('wst', type=int, required=False, location='json')
	parser.add_argument('wst_name', type=str, required=False, location='json')
	parser.add_argument('cst', type=int, required=False, location='json')
	parser.add_argument('ovfl', type=int, required=False, location='json')
	parser.add_argument('rule', type=int, required=False, location='json')
	parser.add_argument('rec', type=int, required=False, location='json')
	parser.add_argument('rec_name', type=str, required=False, location='json')
	args = parser.parse_args(strict=True)
	return args


class RecallConApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Recall_con, 'Recall', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Recall_con, 'Recall')

	def put(self, project_db, id):
		args = get_con_args()
		try:
			SetupProjectDatabase.init(project_db)
			m = Recall_con.get(Recall_con.id == id)
			m.name = args['name']
			m.area = args['area']
			m.lat = args['lat']
			m.lon = args['lon']
			m.elev = args['elev']

			if args['rec_name'] is not None:
				m.rec_id = self.get_id_from_name(Recall_rec, args['recall_name'])

			if args['wst_name'] is not None:
				m.wst_id = self.get_id_from_name(Weather_sta_cli, args['wst_name'])

			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update recall {id}.'.format(id=id))
		except IntegrityError:
			abort(400, message='Recall name must be unique.')
		except Recall_con.DoesNotExist:
			abort(404, message='Recall {id} does not exist'.format(id=id))
		except Recall_rec.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['rec_name']))
		except Weather_sta_cli.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['wst_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class RecallConPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_con_args()
		SetupProjectDatabase.init(project_db)

		try:
			e = Recall_con.get(Recall_con.name == args['name'])
			abort(400, message='Recall name must be unique. Recall with this name already exists.')
		except Recall_con.DoesNotExist:
			try:
				m = Recall_con()
				m.name = args['name']
				m.area = args['area']
				m.lat = args['lat']
				m.lon = args['lon']
				m.elev = args['elev']
				m.ovfl = 0
				m.rule = 0

				if args['rec_name'] is not None:
					m.rec_id = self.get_id_from_name(Recall_rec, args['rec_name'])

				if args['wst_name'] is not None:
					m.wst_id = self.get_id_from_name(Weather_sta_cli, args['wst_name'])

				result = m.save()

				if result > 0:
					return model_to_dict(m), 201

				abort(400, message='Unable to create Exco.')
			except IntegrityError:
				abort(400, message='Exco name must be unique.')
			except Recall_rec.DoesNotExist:
				abort(400, message=invalid_name_msg.format(name=args['rec_name']))
			except Weather_sta_cli.DoesNotExist:
				abort(400, message=invalid_name_msg.format(name=args['wst_name']))
			except Exception as ex:
				abort(400, message="Unexpected error {ex}".format(ex=ex))


class RecallConListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Recall_con
		list_name = 'recall'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name, True)


class RecallConMapApi(BaseRestModel):
	def get(self, project_db):
		return self.get_con_map(project_db, Recall_con)


def get_con_out_args():
	parser = reqparse.RequestParser()
	parser.add_argument('id', type=int, required=False, location='json')
	parser.add_argument('order', type=int, required=True, location='json')
	parser.add_argument('obj_typ', type=str, required=True, location='json')
	parser.add_argument('obj_id', type=int, required=True, location='json')
	parser.add_argument('hyd_typ', type=str, required=True, location='json')
	parser.add_argument('frac', type=float, required=True, location='json')
	parser.add_argument('recall_con_id', type=int, required=False, location='json')
	args = parser.parse_args(strict=True)
	return args


class RecallConOutApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Recall_con_out, 'Outflow', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Recall_con_out, 'Outflow')

	def put(self, project_db, id):
		try:
			args = get_con_out_args()
			SetupProjectDatabase.init(project_db)

			m = Recall_con_out.get(Recall_con_out.id == id)
			m.order = args['order']
			m.obj_typ = args['obj_typ']
			m.obj_id = args['obj_id']
			m.hyd_typ = args['hyd_typ']
			m.frac = args['frac']

			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update recall outflow {id}.'.format(id=id))
		except Recall_con_out.DoesNotExist:
			abort(404, message='Recall outflow {id} does not exist'.format(id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class RecallConOutPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_con_out_args()
		SetupProjectDatabase.init(project_db)

		try:
			m = Recall_con_out()
			m.order = args['order']
			m.obj_typ = args['obj_typ']
			m.obj_id = args['obj_id']
			m.hyd_typ = args['hyd_typ']
			m.frac = args['frac']
			m.recall_con_id = args['recall_con_id']

			result = m.save()

			if result > 0:
				return model_to_dict(m), 201

			abort(400, message='Unable to create outflow.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class RecallRecListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Recall_rec
		list_name = 'recall'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class RecallRecApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Recall_rec, 'Recall', back_refs=True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Recall_rec, 'Recall')

	def put(self, project_db, id):
		#return self.base_put(project_db, id, Recall_rec, 'Recall')
		table = Recall_rec
		item_description = 'Recall'
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args_reflect(table, project_db)

			m = table.get(table.id==id)
			if m.rec_typ != args['rec_typ']:
				Recall_dat.delete().where(Recall_dat.recall_rec_id==id).execute()

				sim = Time_sim.get_or_create_default()
				years = 0
				months = 1
				days = 1
				start_day = 1
				start_month = 1
				insert_daily = False

				if args['rec_typ'] != 4:
					years = sim.yrc_end - sim.yrc_start
					if args['rec_typ'] != 3:
						start_date = datetime.datetime(sim.yrc_start, 1, 1) + datetime.timedelta(sim.day_start)
						end_date = datetime.datetime(sim.yrc_end, 1, 1) + datetime.timedelta(sim.day_end)
						if sim.day_end == 0:
							end_date = datetime.datetime(sim.yrc_end, 12, 31)

						start_month = start_date.month
						months = end_date.month
						
						if args['rec_typ'] != 2:
							insert_daily = True

				rec_data = []
				if not insert_daily:
					for x in range(years + 1):
						for y in range(start_month, months + 1):
							t_step = x + 1 if months == 1 else y
							data = {
								'recall_rec_id': id,
								'yr': x + sim.yrc_start if args['rec_typ'] != 4 else 0,
								't_step': t_step if args['rec_typ'] != 4 else 0,
								'flo': 0,
								'sed': 0,
								'ptl_n': 0,
								'ptl_p': 0,
								'no3_n': 0,
								'sol_p': 0,
								'chla': 0,
								'nh3_n': 0,
								'no2_n': 0,
								'cbn_bod': 0,
								'oxy': 0,
								'sand': 0,
								'silt': 0,
								'clay': 0,
								'sm_agg': 0,
								'lg_agg': 0,
								'gravel': 0,
								'tmp': 0
							}
							rec_data.append(data)
				else:
					current_date = start_date
					while current_date <= end_date:
						data = {
							'recall_rec_id': id,
							'yr': current_date.year,
							't_step': current_date.timetuple().tm_yday,
							'flo': 0,
							'sed': 0,
							'ptl_n': 0,
							'ptl_p': 0,
							'no3_n': 0,
							'sol_p': 0,
							'chla': 0,
							'nh3_n': 0,
							'no2_n': 0,
							'cbn_bod': 0,
							'oxy': 0,
							'sand': 0,
							'silt': 0,
							'clay': 0,
							'sm_agg': 0,
							'lg_agg': 0,
							'gravel': 0,
							'tmp': 0
						}
						rec_data.append(data)
						current_date = current_date + datetime.timedelta(1) 

				db_lib.bulk_insert(project_base.db, Recall_dat, rec_data)
			
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


class RecallRecPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Recall_rec, 'Recall')


class RecallDatApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Recall_dat, 'Recall', back_refs=True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Recall_dat, 'Recall')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Recall_dat, 'Recall')


class RecallDatPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Recall_dat, 'Recall')
