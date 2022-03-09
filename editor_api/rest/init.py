from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database import lib as db_lib
from database.project.setup import SetupProjectDatabase

from database.project.init import Soil_plant_ini, Salt_hru_ini, Salt_hru_ini_item, Hmet_hru_ini, Hmet_hru_ini_item, Path_hru_ini, Pest_hru_ini, Path_hru_ini_item, Pest_hru_ini_item, Om_water_ini, Plant_ini, Plant_ini_item, Salt_water_ini, Hmet_water_ini, Path_water_ini, Pest_water_ini, Salt_water_ini_item, Hmet_water_ini_item, Path_water_ini_item, Pest_water_ini_item
from database.project.soils import Nutrients_sol
from database.project.simulation import Constituents_cs
from database.project.hru_parm_db import Pesticide_pst, Pathogens_pth, Metals_mtl, Salts_slt
from database.project import base as project_base

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
	def get(self, project_db):
		table = Soil_plant_ini
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols, back_refs=True)


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
	def get(self, project_db):
		table = Om_water_ini
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols)


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
	def get(self, project_db):
		SetupProjectDatabase.init(project_db)
		args = self.get_table_args()

		table = Plant_ini
		filter_cols = [table.name, table.rot_yr_ini, table.description]
		total = table.select().count()
		sort = self.get_arg(args, 'sort', 'name')
		reverse = self.get_arg(args, 'reverse', 'n')
		page = self.get_arg(args, 'page', 1)
		per_page = self.get_arg(args, 'per_page', 50)
		filter_val = self.get_arg(args, 'filter', None)

		if filter_val is not None:
			w = None
			for f in filter_cols:
				w = w | (f.contains(filter_val))
			s = table.select().where(w)
		else:
			s = table.select()

		matches = s.count()

		sort_val = SQL('[{}]'.format(sort))
		if reverse == 'y':
			sort_val = SQL('[{}]'.format(sort)).desc()

		m = s.order_by(sort_val).paginate(int(page), int(per_page))
		ml = [{'id': v.id, 'name': v.name, 'rot_yr_ini': v.rot_yr_ini, 'description': v.description, 'num_plants': len(v.plants)} for v in m]

		return {
			'total': total,
			'matches': matches,
			'items': ml
		}


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


def create_constit_ini_tables():
	project_base.db.create_tables([Pest_hru_ini, Pest_hru_ini_item, Pest_water_ini, Pest_water_ini_item, 
		Path_hru_ini, Path_hru_ini_item, Path_water_ini, Path_water_ini_item, 
		Hmet_hru_ini, Hmet_hru_ini_item, Hmet_water_ini, Hmet_water_ini_item, 
		Salt_hru_ini, Salt_hru_ini_item, Salt_water_ini, Salt_water_ini_item])


class ConstituentsApi(BaseRestModel):
	def get(self, project_db):
		SetupProjectDatabase.init(project_db)
		create_constit_ini_tables()

		if Constituents_cs.select().count() > 0:
			m = Constituents_cs.get()
			return {
				'using': True,
				'pests': [] if m.pest_coms is None else sorted(m.pest_coms.split(',')),
				'paths': [] if m.path_coms is None else sorted(m.path_coms.split(',')),
				'hmets': [] if m.hmet_coms is None else sorted(m.hmet_coms.split(',')),
				'salts': [] if m.salt_coms is None else sorted(m.salt_coms.split(','))
			}

		return {
			'using': False,
			'pests': [],
			'paths': [],
			'hmets': [],
			'salts': []
		}

	def delete(self, project_db):
		SetupProjectDatabase.init(project_db)
		if Constituents_cs.select().count() > 0:
			project_base.db.execute_sql("PRAGMA foreign_keys = ON")
			Pest_hru_ini.delete().execute()
			Pest_water_ini.delete().execute()
			Path_hru_ini.delete().execute()
			Path_water_ini.delete().execute()
			Hmet_hru_ini.delete().execute()
			Hmet_water_ini.delete().execute()
			Salt_hru_ini.delete().execute()
			Salt_water_ini.delete().execute()
			return self.base_delete(project_db, 1, Constituents_cs, 'Constituents')

		return 204

	def put(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			parser = reqparse.RequestParser()
			parser.add_argument('pests', type=list, location='json')
			parser.add_argument('paths', type=list, location='json')
			parser.add_argument('hmets', type=list, location='json')
			parser.add_argument('salts', type=list, location='json')
			args = parser.parse_args(strict=False)

			pest_coms = None if args['pests'] is None or len(args['pests']) < 1 else ','.join(args['pests'])
			path_coms = None if args['paths'] is None or len(args['paths']) < 1 else ','.join(args['paths'])
			hmet_coms = None if args['hmets'] is None or len(args['hmets']) < 1 else ','.join(args['hmets'])
			salt_coms = None if args['salts'] is None or len(args['salts']) < 1 else ','.join(args['salts'])

			pest_ids = Pesticide_pst.select().where(Pesticide_pst.name.in_(args['pests']))
			Pest_hru_ini_item.delete().where(Pest_hru_ini_item.name.not_in(pest_ids)).execute()
			Pest_water_ini_item.delete().where(Pest_water_ini_item.name.not_in(pest_ids)).execute()

			path_ids = Pathogens_pth.select().where(Pathogens_pth.name.in_(args['paths']))
			Path_hru_ini_item.delete().where(Path_hru_ini_item.name.not_in(path_ids)).execute()
			Path_water_ini_item.delete().where(Path_water_ini_item.name.not_in(path_ids)).execute()

			"""hmet_ids = Metals_mtl.select().where(Metals_mtl.name.in_(args['hmets']))
			Hmet_hru_ini_item.delete().where(Hmet_hru_ini_item.name.not_in(hmet_ids)).execute()
			Hmet_water_ini_item.delete().where(Hmet_water_ini_item.name.not_in(hmet_ids)).execute()

			salt_ids = Salts_slt.select().where(Salts_slt.name.in_(args['salts']))
			Salt_hru_ini_item.delete().where(Salt_hru_ini_item.name.not_in(path_ids)).execute()
			Salt_water_ini_item.delete().where(Salt_water_ini_item.name.not_in(path_ids)).execute()"""

			if Constituents_cs.select().count() > 0:
				q = Constituents_cs.update(pest_coms=pest_coms, path_coms=path_coms, hmet_coms=hmet_coms, salt_coms=salt_coms)
				result = q.execute()
			else:
				v = Constituents_cs.create(id=1, name='Constituents', pest_coms=pest_coms, path_coms=path_coms, hmet_coms=hmet_coms, salt_coms=salt_coms)
				result = 1 if v is not None else 0

			if result > 0:
				return 200

			abort(400, message='Unable to update save changes to constituents.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


def get_constituents_ini(project_db, ini_table, db_table, col_name):
	SetupProjectDatabase.init(project_db)
	items = [model_to_dict(v, backrefs=True, max_depth=1) for v in ini_table.select()]
	constituents = []
	if Constituents_cs.select().count() > 0:
		c = model_to_dict(Constituents_cs.get())[col_name]
		names = [] if c is None else sorted(c.split(','))
		constituents = [{'id': v.id, 'name': v.name} for v in db_table.select().where(db_table.name.in_(names))]

	return {
		'items': items,
		'constituents': constituents
	}

def save_constituents_ini(project_db, ini_table, ini_item_table, rel_col_name, row1='plant', row2='soil'):
	SetupProjectDatabase.init(project_db)
	parser = reqparse.RequestParser()
	parser.add_argument('items', type=list, location='json')
	args = parser.parse_args(strict=False)
	
	ini_item_table.delete().execute()
	ini_table.delete().execute()

	for item in args['items']:
		m = ini_table(name = item['name'])
		m.save()

		rows = []
		for row in item['rows']:
			rows.append({
				rel_col_name: m.id,
				'name_id': row['name_id'],
				row1: row[row1],
				row2: row[row2]
			})

		db_lib.bulk_insert(project_base.db, ini_item_table, rows)

class PestHruIniApi(BaseRestModel):
	def get(self, project_db):
		create_constit_ini_tables()
		return get_constituents_ini(project_db, Pest_hru_ini, Pesticide_pst, 'pest_coms')

	def put(self, project_db):
		try:
			save_constituents_ini(project_db, Pest_hru_ini, Pest_hru_ini_item, 'pest_hru_ini_id')
			return 200
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class PestWaterIniApi(BaseRestModel):
	def get(self, project_db):
		create_constit_ini_tables()
		return get_constituents_ini(project_db, Pest_water_ini, Pesticide_pst, 'pest_coms')

	def put(self, project_db):
		try:
			save_constituents_ini(project_db, Pest_water_ini, Pest_water_ini_item, 'pest_water_ini_id', row1='water', row2='benthic')
			return 200
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class PathHruIniApi(BaseRestModel):
	def get(self, project_db):
		create_constit_ini_tables()
		return get_constituents_ini(project_db, Path_hru_ini, Pathogens_pth, 'path_coms')

	def put(self, project_db):
		try:
			save_constituents_ini(project_db, Path_hru_ini, Path_hru_ini_item, 'path_hru_ini_id')
			return 200
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class PathWaterIniApi(BaseRestModel):
	def get(self, project_db):
		create_constit_ini_tables()
		return get_constituents_ini(project_db, Path_water_ini, Pathogens_pth, 'path_coms')

	def put(self, project_db):
		try:
			save_constituents_ini(project_db, Path_water_ini, Path_water_ini_item, 'path_water_ini_id', row1='water', row2='benthic')
			return 200
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))
