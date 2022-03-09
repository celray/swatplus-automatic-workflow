from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project.setup import SetupProjectDatabase
from database.project.connect import Reservoir_con, Reservoir_con_out
from database.project.reservoir import Reservoir_res, Initial_res, Hydrology_res, Sediment_res, Nutrients_res, Wetland_wet, Hydrology_wet
from database.project.climate import Weather_sta_cli
from database.project.init import Om_water_ini, Pest_water_ini, Path_water_ini, Hmet_water_ini, Salt_water_ini
from database.project.decision_table import D_table_dtl

invalid_name_msg = 'Invalid name {name}. Please ensure the value exists in your database.'


class ReservoirConApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Reservoir_con, 'Reservoir', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Reservoir_con, 'Reservoir', 'res', Reservoir_res)

	def put(self, project_db, id):
		return self.put_con(project_db, id, 'res', Reservoir_con, Reservoir_res)


class ReservoirConPostApi(BaseRestModel):
	def post(self, project_db):
		return self.post_con(project_db, 'res', Reservoir_con, Reservoir_res)


class ReservoirConListApi(BaseRestModel):
	def get(self, project_db):
		table = Reservoir_con
		prop_table = Reservoir_res
		filter_cols = [table.name, table.wst, prop_table.init, prop_table.hyd, prop_table.rel, prop_table.sed, prop_table.nut]
		table_lookups = {
			table.wst: Weather_sta_cli
		}
		props_lookups = {
			prop_table.init: Initial_res,
			prop_table.hyd: Hydrology_res,
			prop_table.rel: D_table_dtl,
			prop_table.sed: Sediment_res,
			prop_table.nut: Nutrients_res
		}

		items = self.base_connect_paged_items(project_db, table, prop_table, filter_cols, table_lookups, props_lookups)
		ml = []
		for v in items['model']:
			d = self.base_get_con_item_dict(v)
			d['init'] = self.base_get_prop_dict(v.res.init)
			d['hyd'] = self.base_get_prop_dict(v.res.hyd)
			d['rel'] = self.base_get_prop_dict(v.res.rel)
			d['sed'] = self.base_get_prop_dict(v.res.sed)
			d['nut'] = self.base_get_prop_dict(v.res.nut)
			ml.append(d)
		
		return {
			'total': items['total'],
			'matches': items['matches'],
			'items': ml
		}


class ReservoirConMapApi(BaseRestModel):
	def get(self, project_db):
		return self.get_con_map(project_db, Reservoir_con)


class ReservoirConOutApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Reservoir_con_out, 'Outflow', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Reservoir_con_out, 'Outflow')

	def put(self, project_db, id):
		return self.put_con_out(project_db, id, 'reservoir_con', Reservoir_con_out)


class ReservoirConOutPostApi(BaseRestModel):
	def post(self, project_db):
		return self.post_con_out(project_db, 'reservoir_con', Reservoir_con_out)


def get_res_args(get_selected_ids=False):
	parser = reqparse.RequestParser()
	
	if get_selected_ids:
		parser.add_argument('selected_ids', type=int, action='append', required=False, location='json')
		parser.add_argument('elev', type=float, required=False, location='json')
		parser.add_argument('wst_name', type=str, required=False, location='json')
	else:
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('name', type=str, required=True, location='json')
		parser.add_argument('description', type=str, required=False, location='json')
		
	parser.add_argument('init_name', type=str, required=False, location='json')
	parser.add_argument('rel_name', type=str, required=False, location='json')
	parser.add_argument('hyd_name', type=str, required=False, location='json')
	parser.add_argument('sed_name', type=str, required=False, location='json')
	parser.add_argument('nut_name', type=str, required=False, location='json')
	args = parser.parse_args(strict=False)
	return args


class ReservoirResListApi(BaseRestModel):
	def get(self, project_db):
		table = Reservoir_res
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols, True)


class ReservoirResApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Reservoir_res, 'Reservoir', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Reservoir_res, 'Reservoir')

	def put(self, project_db, id):
		args = get_res_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Reservoir_res.get(Reservoir_res.id == id)
			m.name = args['name']
			m.description = args['description']
			m.init_id = self.get_id_from_name(Initial_res, args['init_name'])
			m.rel_id = self.get_id_from_name(D_table_dtl, args['rel_name'])
			m.hyd_id = self.get_id_from_name(Hydrology_res, args['hyd_name'])
			m.sed_id = self.get_id_from_name(Sediment_res, args['sed_name'])
			m.nut_id = self.get_id_from_name(Nutrients_res, args['nut_name'])

			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update reservoir properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Reservoir properties name must be unique.')
		except Reservoir_res.DoesNotExist:
			abort(404, message='Reservoir properties {id} does not exist'.format(id=id))
		except Initial_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['init_name']))
		except D_table_dtl.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['rel_name']))
		except Hydrology_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hyd_name']))
		except Sediment_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['sed_name']))
		except Nutrients_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['nut_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))
			
			
class ReservoirResUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Reservoir_res)

	def put(self, project_db):
		SetupProjectDatabase.init(project_db)
		args = get_res_args(True)
		try:
			param_dict = {}

			if args['init_name'] is not None:
				param_dict['init_id'] = self.get_id_from_name(Initial_res, args['init_name'])
			if args['rel_name'] is not None:
				param_dict['rel_id'] = self.get_id_from_name(D_table_dtl, args['rel_name'])
			if args['hyd_name'] is not None:
				param_dict['hyd_id'] = self.get_id_from_name(Hydrology_res, args['hyd_name'])
			if args['sed_name'] is not None:
				param_dict['sed_id'] = self.get_id_from_name(Sediment_res, args['sed_name'])
			if args['nut_name'] is not None:
				param_dict['nut_id'] = self.get_id_from_name(Nutrients_res, args['nut_name'])

			con_table = Reservoir_con
			con_prop_field = Reservoir_con.res_id
			prop_table = Reservoir_res

			result = self.base_put_many_con(args, param_dict, con_table, con_prop_field, prop_table)
			if result > 0:
				return 200

			abort(400, message='Unable to update reservoir properties.')
		except Initial_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['init_name']))
		except D_table_dtl.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['rel_name']))
		except Hydrology_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hyd_name']))
		except Sediment_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['sed_name']))
		except Nutrients_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['nut_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class ReservoirResPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_res_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Reservoir_res()
			m.name = args['name']
			m.description = args['description']
			m.init_id = self.get_id_from_name(Initial_res, args['init_name'])
			m.rel_id = self.get_id_from_name(D_table_dtl, args['rel_name'])
			m.hyd_id = self.get_id_from_name(Hydrology_res, args['hyd_name'])
			m.sed_id = self.get_id_from_name(Sediment_res, args['sed_name'])
			m.nut_id = self.get_id_from_name(Nutrients_res, args['nut_name'])

			result = m.save()

			if result > 0:
				return {'id': m.id }, 200

			abort(400, message='Unable to update reservoir properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Reservoir properties name must be unique.')
		except Initial_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['init_name']))
		except D_table_dtl.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['rel_name']))
		except Hydrology_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hyd_name']))
		except Sediment_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['sed_name']))
		except Nutrients_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['nut_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class InitialResListApi(BaseRestModel):
	def get(self, project_db):
		table = Initial_res
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols, True)


def get_initial_args(get_selected_ids=False):
	parser = reqparse.RequestParser()

	if get_selected_ids:
		parser.add_argument('selected_ids', type=int, action='append', required=False, location='json')
	else:
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('name', type=str, required=True, location='json')
		parser.add_argument('description', type=str, required=False, location='json')

	parser.add_argument('org_min_name', type=str, required=True, location='json')
	parser.add_argument('pest_name', type=str, required=False, location='json')
	parser.add_argument('path_name', type=str, required=False, location='json')
	parser.add_argument('hmet_name', type=str, required=False, location='json')
	parser.add_argument('salt_name', type=str, required=False, location='json')
	args = parser.parse_args(strict=False)
	return args


class InitialResApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Initial_res, 'Reservoir', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Initial_res, 'Reservoir')

	def put(self, project_db, id):
		args = get_initial_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Initial_res.get(Initial_res.id == id)
			m.name = args['name']
			m.description = args['description']
			m.org_min_id = self.get_id_from_name(Om_water_ini, args['org_min_name'])
			if args['pest_name']:
				m.pest_id = self.get_id_from_name(Pest_water_ini, args['pest_name'])
			if args['path_name']:
				m.path_id = self.get_id_from_name(Path_water_ini, args['path_name'])
			if args['hmet_name']:
				m.hmet_id = self.get_id_from_name(Hmet_water_ini, args['hmet_name'])
			if args['salt_name']:
				m.salt_id = self.get_id_from_name(Salt_water_ini, args['salt_name'])
			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update initial reservoir properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Initial reservoir properties name must be unique.')
		except Initial_res.DoesNotExist:
			abort(404, message='Initial reservoir properties {id} does not exist'.format(id=id))
		except Om_water_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['org_min_name']))
		except Pest_water_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['pest_name']))
		except Path_water_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['path_name']))
		except Hmet_water_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hmet_name']))
		except Salt_water_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['salt_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class InitialResUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Initial_res)

	def put(self, project_db):
		SetupProjectDatabase.init(project_db)
		args = get_initial_args(True)

		try:
			param_dict = {}

			if args['org_min_name'] is not None:
				param_dict['org_min_id'] = self.get_id_from_name(Om_water_ini, args['org_min_name'])
			if args['pest_name'] is not None:
				param_dict['pest_id'] = self.get_id_from_name(Pest_water_ini, args['pest_name'])
			if args['path_name'] is not None:
				param_dict['path_id'] = self.get_id_from_name(Path_water_ini, args['path_name'])
			if args['hmet_name'] is not None:
				param_dict['hmet_id'] = self.get_id_from_name(Hmet_water_ini, args['hmet_name'])
			if args['salt_name'] is not None:
				param_dict['salt_id'] = self.get_id_from_name(Salt_water_ini, args['salt_name'])

			query = Initial_res.update(param_dict).where(Initial_res.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update reservoir initial properties.')
		except Om_water_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['org_min_name']))
		except Pest_water_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['pest_name']))
		except Path_water_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['path_name']))
		except Hmet_water_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hmet_name']))
		except Salt_water_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['salt_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class InitialResPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_initial_args()
		try:
			SetupProjectDatabase.init(project_db)
			
			m = Initial_res()
			m.name = args['name']
			m.description = args['description']
			m.org_min_id = self.get_id_from_name(Om_water_ini, args['org_min_name'])
			if args['pest_name']:
				m.pest_id = self.get_id_from_name(Pest_water_ini, args['pest_name'])
			if args['path_name']:
				m.path_id = self.get_id_from_name(Path_water_ini, args['path_name'])
			if args['hmet_name']:
				m.hmet_id = self.get_id_from_name(Hmet_water_ini, args['hmet_name'])
			if args['salt_name']:
				m.salt_id = self.get_id_from_name(Salt_water_ini, args['salt_name'])
			result = m.save()

			if result > 0:
				return model_to_dict(m), 201

			abort(400, message='Unable to update initial reservoir properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Initial reservoir properties name must be unique.')
		except Om_water_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['org_min_name']))
		except Pest_water_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['pest_name']))
		except Path_water_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['path_name']))
		except Hmet_water_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hmet_name']))
		except Salt_water_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['salt_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class HydrologyResListApi(BaseRestModel):
	def get(self, project_db):
		table = Hydrology_res
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols)


class HydrologyResApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Hydrology_res, 'Reservoir')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Hydrology_res, 'Reservoir')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Hydrology_res, 'Reservoir')


class HydrologyResUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Hydrology_res)

	def put(self, project_db):
		return self.base_put_many(project_db, Hydrology_res, 'Reservoir')


class HydrologyResPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Hydrology_res, 'Reservoir')


class SedimentResListApi(BaseRestModel):
	def get(self, project_db):
		table = Sediment_res
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols)


class SedimentResApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Sediment_res, 'Reservoir')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Sediment_res, 'Reservoir')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Sediment_res, 'Reservoir')


class SedimentResUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Sediment_res)

	def put(self, project_db):
		return self.base_put_many(project_db, Sediment_res, 'Reservoir')


class SedimentResPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Sediment_res, 'Reservoir')


class NutrientsResListApi(BaseRestModel):
	def get(self, project_db):
		table = Nutrients_res
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols)


class NutrientsResApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Nutrients_res, 'Reservoir')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Nutrients_res, 'Reservoir')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Nutrients_res, 'Reservoir')
			
			
class NutrientsResUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Nutrients_res)

	def put(self, project_db):
		return self.base_put_many(project_db, Nutrients_res, 'Reservoir')


class NutrientsResPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Nutrients_res, 'Reservoir')


def get_wet_args(get_selected_ids=False):
	parser = reqparse.RequestParser()
	
	if get_selected_ids:
		parser.add_argument('selected_ids', type=int, action='append', required=False, location='json')
	else:
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('name', type=str, required=True, location='json')
		parser.add_argument('description', type=str, required=False, location='json')
		
	parser.add_argument('init_name', type=str, required=True, location='json')
	parser.add_argument('rel_name', type=str, required=True, location='json')
	parser.add_argument('hyd_name', type=str, required=True, location='json')
	parser.add_argument('sed_name', type=str, required=True, location='json')
	parser.add_argument('nut_name', type=str, required=True, location='json')
	args = parser.parse_args(strict=False)
	return args


class WetlandsWetListApi(BaseRestModel):
	def get(self, project_db):
		table = Wetland_wet
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols, True)


class WetlandsWetApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Wetland_wet, 'Wetlands', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Wetland_wet, 'Wetlands')

	def put(self, project_db, id):
		args = get_wet_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Wetland_wet.get(Wetland_wet.id == id)
			m.name = args['name']
			m.description = args['description']
			m.init_id = self.get_id_from_name(Initial_res, args['init_name'])
			m.rel_id = self.get_id_from_name(D_table_dtl, args['rel_name'])
			m.hyd_id = self.get_id_from_name(Hydrology_wet, args['hyd_name'])
			m.sed_id = self.get_id_from_name(Sediment_res, args['sed_name'])
			m.nut_id = self.get_id_from_name(Nutrients_res, args['nut_name'])

			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update wetland properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Wetland properties name must be unique.')
		except Wetland_wet.DoesNotExist:
			abort(404, message='Wetland properties {id} does not exist'.format(id=id))
		except Initial_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['init_name']))
		except D_table_dtl.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['rel_name']))
		except Hydrology_wet.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hyd_name']))
		except Sediment_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['sed_name']))
		except Nutrients_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['nut_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))
			
			
class WetlandsWetUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Wetland_wet)

	def put(self, project_db):
		SetupProjectDatabase.init(project_db)
		args = get_res_args(True)
		try:
			param_dict = {}

			if args['init_name'] is not None:
				param_dict['init_id'] = self.get_id_from_name(Initial_res, args['init_name'])
			if args['rel_name'] is not None:
				param_dict['rel_id'] = self.get_id_from_name(D_table_dtl, args['rel_name'])
			if args['hyd_name'] is not None:
				param_dict['hyd_id'] = self.get_id_from_name(Hydrology_wet, args['hyd_name'])
			if args['sed_name'] is not None:
				param_dict['sed_id'] = self.get_id_from_name(Sediment_res, args['sed_name'])
			if args['nut_name'] is not None:
				param_dict['nut_id'] = self.get_id_from_name(Nutrients_res, args['nut_name'])

			query = Wetland_wet.update(param_dict).where(Wetland_wet.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update wetland .')
		except Initial_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['init_name']))
		except D_table_dtl.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['rel_name']))
		except Hydrology_wet.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hyd_name']))
		except Sediment_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['sed_name']))
		except Nutrients_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['nut_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class WetlandsWetPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_wet_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Wetland_wet()
			m.name = args['name']
			m.description = args['description']
			m.init_id = self.get_id_from_name(Initial_res, args['init_name'])
			m.rel_id = self.get_id_from_name(D_table_dtl, args['rel_name'])
			m.hyd_id = self.get_id_from_name(Hydrology_wet, args['hyd_name'])
			m.sed_id = self.get_id_from_name(Sediment_res, args['sed_name'])
			m.nut_id = self.get_id_from_name(Nutrients_res, args['nut_name'])

			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update wetland  {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Wetland name must be unique.')
		except Initial_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['init_name']))
		except D_table_dtl.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['rel_name']))
		except Hydrology_wet.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hyd_name']))
		except Sediment_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['sed_name']))
		except Nutrients_res.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['nut_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class HydrologyWetListApi(BaseRestModel):
	def get(self, project_db):
		table = Hydrology_wet
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols)


class HydrologyWetApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Hydrology_wet, 'Reservoir')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Hydrology_wet, 'Reservoir')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Hydrology_wet, 'Reservoir')


class HydrologyWetUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Hydrology_wet)

	def put(self, project_db):
		return self.base_put_many(project_db, Hydrology_wet, 'Reservoir')


class HydrologyWetPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Hydrology_wet, 'Reservoir')