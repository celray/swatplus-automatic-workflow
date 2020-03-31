from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project.setup import SetupProjectDatabase

from database.project.init import Soil_plant_ini, Salt_hru_ini, Hmet_hru_ini, Path_hru_ini, Pest_hru_ini, Om_water_ini, Plant_ini, Plant_ini_item
from database.project.soils import Nutrients_sol

invalid_name_msg = 'Invalid name {name}. Please ensure the value exists in your database.'

""" Soil Plant """
def get_soil_plant_args(get_selected_ids=False):
	parser = reqparse.RequestParser()

	if get_selected_ids:
		parser.add_argument('selected_ids', type=int, action='append', required=False, location='json')
	else: 
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('name', type=str, required=True, location='json')
    
	parser.add_argument('sw_frac', type=float, required=True, location='json')
	parser.add_argument('nutrients_name', type=str, required=False, location='json')
	parser.add_argument('pest_name', type=str, required=False, location='json')
	parser.add_argument('path_name', type=str, required=False, location='json')
	parser.add_argument('hmet_name', type=str, required=False, location='json')
	parser.add_argument('salt_name', type=str, required=False, location='json')
	args = parser.parse_args(strict=True)
	return args


class SoilPlantListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Soil_plant_ini
		list_name = 'soil_plant'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name, True)


class SoilPlantApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Soil_plant_ini, 'SoilPlant', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Soil_plant_ini, 'SoilPlant')

	def put(self, project_db, id):
		args = get_soil_plant_args()		
		try:
			SetupProjectDatabase.init(project_db)

			m = Soil_plant_ini.get(Soil_plant_ini.id == id)
			m.name = args['name']
			m.sw_frac = args['sw_frac']
			m.nutrients_id = self.get_id_from_name(Nutrients_sol, args['nutrients_name'])
			m.pest_id = self.get_id_from_name(Pest_hru_ini, args['pest_name'])
			m.path_id = self.get_id_from_name(Path_hru_ini, args['path_name'])
			m.hmet_id = self.get_id_from_name(Hmet_hru_ini, args['hmet_name'])
			m.salt_id = self.get_id_from_name(Salt_hru_ini, args['salt_name'])

			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update soil plant  {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Soil plant properties name must be unique.')
		except Soil_plant_ini.DoesNotExist:
			abort(404, message='Soil plant properties {id} does not exist'.format(id=id))
		except Nutrients_sol.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['nutrients_name']))
		except Pest_hru_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['pest_name']))
		except Path_hru_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['path_name']))
		except Hmet_hru_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hmet_name']))
		except Salt_hru_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['salt_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class SoilPlantUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Soil_plant_ini)

	def put(self, project_db):
		SetupProjectDatabase.init(project_db)
		args = get_soil_plant_args(True)
		try:
			param_dict = {}

			if args['sw_frac'] is not None:
				param_dict['sw_frac'] = args['sw_frac']
			if args['nutrients_name'] is not None:
				param_dict['nutrients_id'] = self.get_id_from_name(Nutrients_sol, args['nutrients_name'])
			if args['pest_name'] is not None:
				param_dict['pest_id'] = self.get_id_from_name(Pest_hru_ini, args['pest_name'])
			if args['path_name'] is not None:
				param_dict['path_id'] = self.get_id_from_name(Path_hru_ini, args['path_name'])
			if args['hmet_name'] is not None:
				param_dict['hmet_id'] = self.get_id_from_name(Hmet_hru_ini, args['hmet_name'])
			if args['salt_name'] is not None:
				param_dict['salt_id'] = self.get_id_from_name(Salt_hru_ini, args['salt_name'])

			query = Soil_plant_ini.update(param_dict).where(Soil_plant_ini.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update soil plant.')
		except Nutrients_sol.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['nutrients_name']))
		except Pest_hru_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['pest_name']))
		except Path_hru_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['path_name']))
		except Hmet_hru_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hmet_name']))
		except Salt_hru_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['salt_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class SoilPlantPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_soil_plant_args()

		try:
			SetupProjectDatabase.init(project_db)

			m = Soil_plant_ini()
			m.name = args['name']
			m.sw_frac = args['sw_frac']
			m.nutrients_id = self.get_id_from_name(Nutrients_sol, args['nutrients_name'])
			m.pest_id = self.get_id_from_name(Pest_hru_ini, args['pest_name'])
			m.path_id = self.get_id_from_name(Path_hru_ini, args['path_name'])
			m.hmet_id = self.get_id_from_name(Hmet_hru_ini, args['hmet_name'])
			m.salt_id = self.get_id_from_name(Salt_hru_ini, args['salt_name'])
			
			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update soil plant {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Soil Plant name must be unique.')
		except Nutrients_sol.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['nutrients_name']))
		except Pest_hru_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['pest_name']))
		except Path_hru_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['path_name']))
		except Hmet_hru_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hmet_name']))
		except Salt_hru_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['salt_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))
""" Soil Plant """

""" Organic mineral water """

class OMWaterListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Om_water_ini
		list_name = 'om_water'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


def save_om_water(m, args):
	m.name = args['name']
	m.flo = args['flo']
	m.sed = args['sed']
	m.orgn = args['orgn']
	m.sedp = args['sedp']
	m.no3 = args['no3']
	m.solp = args['solp']
	m.chl_a = args['chl_a']
	m.nh3 = args['nh3']
	m.no2 = args['no2']
	m.cbn_bod = args['cbn_bod']
	m.dis_ox = args['dis_ox']
	m.san = args['san']
	m.sil = args['sil']
	m.cla = args['cla']
	m.sag = args['sag']
	m.lag = args['lag']
	m.grv = args['grv']
	m.tmp = args['tmp']
	m.c = args['c']
	return m.save()


class OMWaterApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Om_water_ini, 'OMWater')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Om_water_ini, 'OMWater')

	def put(self, project_db, id):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('om_water_ini', project_db)

			m = Om_water_ini.get(Om_water_ini.id == id)
			result = save_om_water(m, args)

			if result > 0:
				return 200

			abort(400, message='Unable to update organic mineral water {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Organic mineral water name must be unique.')
		except Om_water_ini.DoesNotExist:
			abort(404, message='Organic mineral water {id} does not exist'.format(id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class OMWaterUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Om_water_ini)

	def put(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('om_water_ini', project_db, True)

			param_dict = {}
			for key in args.keys():
				if args[key] is not None and key != 'selected_ids':
					param_dict[key] = args[key]

			query = Om_water_ini.update(param_dict).where(Om_water_ini.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update organic mineral water.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class OMWaterPostApi(BaseRestModel):
	def post(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('om_water_ini', project_db)

			m = Om_water_ini()
			result = save_om_water(m, args)

			if result > 0:
				return model_to_dict(m), 201

			abort(400, message='Unable to update organic mineral water {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Organic mineral water name must be unique.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))

""" Organic mineral water """


""" Plant Communities """
class PlantIniListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Plant_ini
		list_name = 'plants'
		SetupProjectDatabase.init(project_db)
		total = table.select().count()

		sort_val = SQL(sort)
		if reverse == 'true':
			sort_val = SQL(sort).desc()

		m = table.select().order_by(sort_val).paginate(int(page), int(items_per_page))
		ml = [{'id': v.id, 'name': v.name, 'rot_yr_ini': v.rot_yr_ini, 'description': v.description, 'num_plants': len(v.plants)} for v in m]

		return {'total': total, list_name: ml}


class PlantIniApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Plant_ini, 'Plant community', back_refs=True, max_depth=2)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Plant_ini, 'Plant community')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Plant_ini, 'Plant community')


class PlantIniPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Plant_ini, 'Plant community')


class PlantIniItemApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Plant_ini_item, 'Plant')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Plant_ini_item, 'Plant')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Plant_ini_item, 'Plant')


class PlantIniItemPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Plant_ini_item, 'Plant')
""" Plant Communities """
