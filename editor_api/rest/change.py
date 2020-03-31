from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project import base as project_base
from database.project.setup import SetupProjectDatabase
from database.project.config import Project_config
from database.project import change
from database import lib
from helpers import table_mapper


class CodesSftApi(BaseRestModel):
	def get(self, project_db):
		SetupProjectDatabase.init(project_db)
		if change.Codes_sft.select().count() > 0:
			return self.base_get(project_db, 1, change.Codes_sft, 'Calibration codes')
		else:
			return {
				'hyd_hru': False,
				'hyd_hrulte': False,
				'plnt': False,
				'sed': False,
				'nut': False,
				'ch_sed': False,
				'ch_nut': False,
				'res': False
			}

	def delete(self, project_db):
		SetupProjectDatabase.init(project_db)
		if change.Codes_sft.select().count() > 0:
			return self.base_delete(project_db, 1, change.Codes_sft, 'Calibration codes')

		return 204

	def put(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args_reflect(change.Codes_sft, project_db)

			if change.Codes_sft.select().count() > 0:
				result = self.save_args(change.Codes_sft, args, id=1)
			else:
				result = self.save_args(change.Codes_sft, args, is_new=True)

			if result > 0:
				return 200

			abort(400, message='Unable to update calibration codes.')
		except change.Codes_sft.DoesNotExist:
			abort(404, message='Could not find calibration codes in database.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class CalParmsCalListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = change.Cal_parms_cal
		list_name = 'cal_parms'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class CalParmsCalApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, change.Cal_parms_cal, 'Calibration parameter')

	def put(self, project_db, id):
		return self.base_put(project_db, id, change.Cal_parms_cal, 'Calibration parameter')


class CalParmsTypesApi(BaseRestModel):
	def get(self, project_db):
		SetupProjectDatabase.init(project_db)
		table = change.Cal_parms_cal
		sol_types = table.select(table.name).where(table.obj_typ == 'sol').order_by(table.name)
		cli_types = table.select(table.name).where(table.obj_typ == 'cli').order_by(table.name)

		return {
			'sol': [v.name for v in sol_types],
			'cli': [v.name for v in cli_types]
		}


class CalibrationCalListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = change.Calibration_cal
		list_name = 'calibrations'

		SetupProjectDatabase.init(project_db)
		total = table.select().count()

		sort_val = SQL(sort)
		if reverse == 'true':
			sort_val = SQL(sort).desc()

		m = table.select().order_by(sort_val).paginate(int(page), int(items_per_page))
		ml = []
		for v in m:
			d = model_to_dict(v, recurse=True)
			d['conditions'] = len(v.conditions)
			d['obj_tot'] = len(v.elements)
			ml.append(d)

		return {'total': total, list_name: ml}


class CalibrationCalApi(BaseRestModel):
	def get(self, project_db, id):
		SetupProjectDatabase.init(project_db)
		table = change.Calibration_cal
		description = 'Calibration'
		try:
			m = table.get(table.id == id)
			item = model_to_dict(m, recurse=True, backrefs=True, max_depth=1)

			obj_options = []
			parm_type = m.cal_parm.obj_typ
			obj_typ = table_mapper.cal_to_obj.get(parm_type, None)
			if obj_typ is not None:
				obj_table = table_mapper.obj_typs.get(obj_typ, None)
				if obj_table is not None:
					t = obj_table.select(obj_table.id, obj_table.name).order_by(obj_table.name)
					obj_options = [{'value': v.id, 'text': v.name} for v in t]

			return {'item': item, 'obj_options': obj_options}
		except table.DoesNotExist:
			abort(404, message='{description} {id} does not exist'.format(description=description, id=id))

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, change.Calibration_cal, 'Calibration')

	def put(self, project_db, id):
		table = change.Calibration_cal
		description = 'Calibration'

		parser = reqparse.RequestParser()
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('cal_parm_id', type=int, required=True, location='json')
		parser.add_argument('chg_typ', type=str, required=True, location='json')
		parser.add_argument('chg_val', type=float, required=True, location='json')
		parser.add_argument('soil_lyr1', type=int, required=True, location='json')
		parser.add_argument('soil_lyr2', type=int, required=True, location='json')
		parser.add_argument('yr1', type=int, required=True, location='json')
		parser.add_argument('yr2', type=int, required=True, location='json')
		parser.add_argument('day1', type=int, required=True, location='json')
		parser.add_argument('day2', type=int, required=True, location='json')
		parser.add_argument('conditions', type=list, required=False, location='json')
		parser.add_argument('elements', type=list, required=False, location='json')
		args = parser.parse_args(strict=False)

		try:
			SetupProjectDatabase.init(project_db)
			result = self.save_args(table, args, id=id)

			if args['elements'] is not None:
				cal_parm = change.Cal_parms_cal.get(change.Cal_parms_cal.id == args['cal_parm_id'])
				obj_typ = table_mapper.cal_to_obj.get(cal_parm.obj_typ, None)
				if obj_typ is not None:
					obj_table = table_mapper.obj_typs.get(obj_typ, None)
					if obj_table is not None:
						elements = []
						for e in args['elements']:
							elements.append({
								'calibration_cal_id': id,
								'obj_typ': obj_typ,
								'obj_id': int(e)
							})
						
						change.Calibration_cal_elem.delete().where(change.Calibration_cal_elem.calibration_cal_id == id).execute()
						lib.bulk_insert(project_base.db, change.Calibration_cal_elem, elements)

			if args['conditions'] is not None:
				conditions = []
				for c in args['conditions']:
					conditions.append({
						'calibration_cal_id': id,
						'cond_typ': c['cond_typ'],
						'cond_op': c['cond_op'],
						'cond_val': c['cond_val'],
						'cond_val_text': c['cond_val_text']
					})
				
				change.Calibration_cal_cond.delete().where(change.Calibration_cal_cond.calibration_cal_id == id).execute()
				lib.bulk_insert(project_base.db, change.Calibration_cal_cond, conditions)

			return 200
		except IntegrityError as e:
			abort(400, message='{item} save error. '.format(item=description) + str(e))
		except table.DoesNotExist:
			abort(404, message='{item} {id} does not exist'.format(item=description, id=id))
		except change.Cal_parms_cal.DoesNotExist:
			abort(404, message='{item} {id} does not exist'.format(item='Calibration parameter', id=args['cal_parm_id']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class CalibrationCalPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, change.Calibration_cal, 'Calibration')


class WbParmsSftListApi(BaseRestModel):
    def get(self, project_db, sort, reverse, page, items_per_page):
        table = change.Wb_parms_sft
        list_name = 'parms'
        return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class WbParmsSftApi(BaseRestModel):
    def get(self, project_db, id):
        return self.base_get(project_db, id, change.Wb_parms_sft, 'Parameter')

    def delete(self, project_db, id):
        return self.base_delete(project_db, id, change.Wb_parms_sft, 'Parameter')

    def put(self, project_db, id):
        return self.base_put(project_db, id, change.Wb_parms_sft, 'Parameter')


class WbParmsSftPostApi(BaseRestModel):
    def post(self, project_db):
        return self.base_post(project_db, change.Wb_parms_sft, 'Parameter')


class ChsedParmsSftListApi(BaseRestModel):
    def get(self, project_db, sort, reverse, page, items_per_page):
        table = change.Ch_sed_parms_sft
        list_name = 'parms'
        return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class ChsedParmsSftApi(BaseRestModel):
    def get(self, project_db, id):
        return self.base_get(project_db, id, change.Ch_sed_parms_sft, 'Parameter')

    def delete(self, project_db, id):
        return self.base_delete(project_db, id, change.Ch_sed_parms_sft, 'Parameter')

    def put(self, project_db, id):
        return self.base_put(project_db, id, change.Ch_sed_parms_sft, 'Parameter')


class ChsedParmsSftPostApi(BaseRestModel):
    def post(self, project_db):
        return self.base_post(project_db, change.Ch_sed_parms_sft, 'Parameter')


class PlantParmsSftListApi(BaseRestModel):
    def get(self, project_db, sort, reverse, page, items_per_page):
        table = change.Plant_parms_sft
        list_name = 'parms'
        return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class PlantParmsSftApi(BaseRestModel):
    def get(self, project_db, id):
        return self.base_get(project_db, id, change.Plant_parms_sft, 'Parameter')

    def delete(self, project_db, id):
        return self.base_delete(project_db, id, change.Plant_parms_sft, 'Parameter')

    def put(self, project_db, id):
        return self.base_put(project_db, id, change.Plant_parms_sft, 'Parameter')


class PlantParmsSftPostApi(BaseRestModel):
    def post(self, project_db):
        return self.base_post(project_db, change.Plant_parms_sft, 'Parameter')


class WaterBalanceSftListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = change.Water_balance_sft
		list_name = 'calibrations'

		SetupProjectDatabase.init(project_db)
		total = table.select().count()

		sort_val = SQL(sort)
		if reverse == 'true':
			sort_val = SQL(sort).desc()

		m = table.select().order_by(sort_val).paginate(int(page), int(items_per_page))
		ml = []
		for v in m:
			d = model_to_dict(v, recurse=True)
			d['items'] = len(v.items)
			ml.append(d)

		return {'total': total, list_name: ml}


class WaterBalanceSftApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, change.Water_balance_sft, 'Calibration', back_refs=True, max_depth=1)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, change.Water_balance_sft, 'Calibration')

	def put(self, project_db, id):
		table = change.Water_balance_sft
		item_table = change.Water_balance_sft_item
		description = 'Calibration'

		parser = reqparse.RequestParser()
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('name', type=str, required=True, location='json')
		parser.add_argument('items', type=list, required=False, location='json')
		args = parser.parse_args(strict=False)

		try:
			SetupProjectDatabase.init(project_db)
			result = self.save_args(table, args, id=id)

			if args['items'] is not None:
				items = []
				for c in args['items']:
					items.append({
						'water_balance_sft_id': id,
						'name': c['name'],
						'surq_rto': c['surq_rto'],
						'latq_rto': c['latq_rto'],
						'perc_rto': c['perc_rto'],
						'et_rto': c['et_rto'],
						'tileq_rto': c['tileq_rto'],
						'pet': c['pet'],
						'sed': c['sed'],
						'orgn': c['orgn'],
						'orgp': c['orgp'],
						'no3': c['no3'],
						'solp': c['solp']
					})
				
				item_table.delete().where(item_table.water_balance_sft_id == id).execute()
				lib.bulk_insert(project_base.db, item_table, items)

			return 200
		except IntegrityError as e:
			abort(400, message='{item} save error. '.format(item=description) + str(e))
		except table.DoesNotExist:
			abort(404, message='{item} {id} does not exist'.format(item=description, id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class WaterBalanceSftPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, change.Water_balance_sft, 'Calibration')


class ChsedBudgetSftListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = change.Ch_sed_budget_sft
		list_name = 'calibrations'

		SetupProjectDatabase.init(project_db)
		total = table.select().count()

		sort_val = SQL(sort)
		if reverse == 'true':
			sort_val = SQL(sort).desc()

		m = table.select().order_by(sort_val).paginate(int(page), int(items_per_page))
		ml = []
		for v in m:
			d = model_to_dict(v, recurse=True)
			d['items'] = len(v.items)
			ml.append(d)

		return {'total': total, list_name: ml}


class ChsedBudgetSftApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, change.Ch_sed_budget_sft, 'Calibration')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, change.Ch_sed_budget_sft, 'Calibration')

	def put(self, project_db, id):
		table = change.Ch_sed_budget_sft
		item_table = change.Ch_sed_budget_sft_item
		description = 'Calibration'

		parser = reqparse.RequestParser()
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('name', type=str, required=True, location='json')
		parser.add_argument('items', type=list, required=False, location='json')
		args = parser.parse_args(strict=False)

		try:
			SetupProjectDatabase.init(project_db)
			result = self.save_args(table, args, id=id)

			if args['items'] is not None:
				items = []
				for c in args['items']:
					items.append({
						'ch_sed_budget_sft_id': id,
						'name': c['name'],
						'cha_wide': c['cha_wide'],
						'cha_dc_accr': c['cha_dc_accr'],
						'head_cut': c['head_cut'],
						'fp_accr': c['fp_accr']
					})
				
				item_table.delete().where(item_table.ch_sed_budget_sft_id == id).execute()
				lib.bulk_insert(project_base.db, item_table, items)

			return 200
		except IntegrityError as e:
			abort(400, message='{item} save error. '.format(item=description) + str(e))
		except table.DoesNotExist:
			abort(404, message='{item} {id} does not exist'.format(item=description, id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class ChsedBudgetSftPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, change.Ch_sed_budget_sft, 'Calibration')


class PlantGroSftListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = change.Plant_gro_sft
		list_name = 'calibrations'

		SetupProjectDatabase.init(project_db)
		total = table.select().count()

		sort_val = SQL(sort)
		if reverse == 'true':
			sort_val = SQL(sort).desc()

		m = table.select().order_by(sort_val).paginate(int(page), int(items_per_page))
		ml = []
		for v in m:
			d = model_to_dict(v, recurse=True)
			d['items'] = len(v.items)
			ml.append(d)

		return {'total': total, list_name: ml}


class PlantGroSftApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, change.Plant_gro_sft, 'Calibration')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, change.Plant_gro_sft, 'Calibration')

	def put(self, project_db, id):
		table = change.Plant_gro_sft
		item_table = change.Plant_gro_sft_item
		description = 'Calibration'

		parser = reqparse.RequestParser()
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('name', type=str, required=True, location='json')
		parser.add_argument('items', type=list, required=False, location='json')
		args = parser.parse_args(strict=False)

		try:
			SetupProjectDatabase.init(project_db)
			result = self.save_args(table, args, id=id)

			if args['items'] is not None:
				items = []
				for c in args['items']:
					items.append({
						'plant_gro_sft_id': id,
						'name': c['name'],
						'yld': c['yld'],
						'npp': c['npp'],
						'lai_mx': c['lai_mx'],
						'wstress': c['wstress'],
						'astress': c['astress'],
						'tstress': c['tstress']
					})
				
				item_table.delete().where(item_table.plant_gro_sft_id == id).execute()
				lib.bulk_insert(project_base.db, item_table, items)

			return 200
		except IntegrityError as e:
			abort(400, message='{item} save error. '.format(item=description) + str(e))
		except table.DoesNotExist:
			abort(404, message='{item} {id} does not exist'.format(item=description, id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class PlantGroSftPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, change.Plant_gro_sft, 'Calibration')
