from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project import base as project_base
from database.project.setup import SetupProjectDatabase
from database.project.connect import Aquifer_con, Aquifer_con_out
from database.project.aquifer import Aquifer_aqu, Initial_aqu
from database.project.climate import Weather_sta_cli
from database.project.config import Project_config
from database.project.init import Om_water_ini, Pest_water_ini, Path_water_ini, Hmet_water_ini, Salt_water_ini

from database.datasets.setup import SetupDatasetsDatabase

import os.path
import ast


class AquiferConApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Aquifer_con, 'Aquifer', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Aquifer_con, 'Aquifer', 'aqu', Aquifer_aqu)

	def put(self, project_db, id):
		return self.put_con(project_db, id, 'aqu', Aquifer_con, Aquifer_aqu)


class AquiferConPostApi(BaseRestModel):
	def post(self, project_db):
		return self.post_con(project_db, 'aqu', Aquifer_con, Aquifer_aqu)


class AquiferConListApi(BaseRestModel):
	def get(self, project_db):
		table = Aquifer_con
		prop_table = Aquifer_aqu
		filter_cols = [table.name, table.wst, prop_table.init]
		table_lookups = {
			table.wst: Weather_sta_cli
		}
		props_lookups = {
			prop_table.init: Initial_aqu
		}

		items = self.base_connect_paged_items(project_db, table, prop_table, filter_cols, table_lookups, props_lookups)
		ml = []
		for v in items['model']:
			d = self.base_get_con_item_dict(v)
			d2 = model_to_dict(v.aqu, recurse=False)
			d3 = {**d, **d2}
			d3['init'] = self.base_get_prop_dict(v.aqu.init)
			ml.append(d3)
		
		return {
			'total': items['total'],
			'matches': items['matches'],
			'items': ml
		}


class AquiferConMapApi(BaseRestModel):
	def get(self, project_db):
		return self.get_con_map(project_db, Aquifer_con)


class AquiferConOutApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Aquifer_con_out, 'Outflow', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Aquifer_con_out, 'Outflow')

	def put(self, project_db, id):
		return self.put_con_out(project_db, id, 'aquifer_con', Aquifer_con_out)


class AquiferConOutPostApi(BaseRestModel):
	def post(self, project_db):
		return self.post_con_out(project_db, 'aquifer_con', Aquifer_con_out)


class AquiferAquListApi(BaseRestModel):
	def get(self, project_db):
		table = Aquifer_aqu
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols, True)


class AquiferAquApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Aquifer_aqu, 'Aquifer', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Aquifer_aqu, 'Aquifer')

	def put(self, project_db, id):
		try:
			SetupProjectDatabase.init(project_db)

			args = self.get_args('aquifer_aqu', project_db)
			result = self.save_args(Aquifer_aqu, args, id=id, lookup_fields=['init'])

			if result > 0:
				return 200

			abort(400, message='Unable to update aquifer properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Aquifer properties name must be unique.')
		except Aquifer_aqu.DoesNotExist:
			abort(404, message='Aquifer properties {id} does not exist'.format(id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class AquiferAquUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Aquifer_aqu)

	def put(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('aquifer_aqu', project_db, True)

			lookup_fields = ['init']

			param_dict = {}
			for key in args.keys():
				if args[key] is not None and key != 'selected_ids':
					if key in lookup_fields:
						d = ast.literal_eval(args[key])
						if int(d['id']) != 0:
							param_dict[key] = int(d['id'])
					else:
						param_dict[key] = args[key]

			con_table = Aquifer_con
			con_prop_field = Aquifer_con.aqu_id
			prop_table = Aquifer_aqu

			result = self.base_put_many_con(args, param_dict, con_table, con_prop_field, prop_table)
			if result > 0:
				return 200

			abort(400, message='Unable to update aquifer properties.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class AquiferAquPostApi(BaseRestModel):
	def post(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)

			args = self.get_args('aquifer_aqu', project_db)
			result = self.save_args(Aquifer_aqu, args, is_new=True, lookup_fields=['init'])

			if result > 0:
				return {'id': result }, 200

			abort(400, message='Unable to update aquifer properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Aquifer properties name must be unique.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class InitialAquListApi(BaseRestModel):
	def get(self, project_db):
		table = Initial_aqu
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


class InitialAquApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Initial_aqu, 'Aquifer', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Initial_aqu, 'Aquifer')

	def put(self, project_db, id):
		args = get_initial_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Initial_aqu.get(Initial_aqu.id == id)
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

			abort(400, message='Unable to update initial aquifer properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Initial aquifer properties name must be unique.')
		except Initial_aqu.DoesNotExist:
			abort(404, message='Initial aquifer properties {id} does not exist'.format(id=id))
		except Om_water_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['org_min_name']))
		except Pest_water_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['pest_name']))
		except Path_water_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['path_name']))
		except Hmet_water_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['hmet_name']))
		except Salt_water_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['salt_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class InitialAquUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Initial_aqu)

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

			query = Initial_aqu.update(param_dict).where(Initial_aqu.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update aquifer initial properties.')
		except Om_water_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['org_min_name']))
		except Pest_water_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['pest_name']))
		except Path_water_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['path_name']))
		except Hmet_water_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['hmet_name']))
		except Salt_water_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['salt_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class InitialAquPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_initial_args()
		try:
			SetupProjectDatabase.init(project_db)
			
			m = Initial_aqu()
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

			abort(400, message='Unable to update initial aquifer properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Initial aquifer properties name must be unique.')
		except Om_water_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['org_min_name']))
		except Pest_water_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['pest_name']))
		except Path_water_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['path_name']))
		except Hmet_water_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['hmet_name']))
		except Salt_water_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['salt_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))
