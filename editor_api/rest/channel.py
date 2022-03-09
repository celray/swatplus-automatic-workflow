from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project.setup import SetupProjectDatabase
from database.project.connect import Channel_con, Channel_con_out, Chandeg_con, Chandeg_con_out
from database.project.channel import Channel_cha, Initial_cha, Hydrology_cha, Sediment_cha, Nutrients_cha, Channel_lte_cha, Hyd_sed_lte_cha
from database.project.climate import Weather_sta_cli
from database.project.init import Om_water_ini, Pest_water_ini, Path_water_ini, Hmet_water_ini, Salt_water_ini

"""
New: As of rev.58, channel-lte is the default for channels, even in non-lte projects.
Still retain functionality of full channels.
"""


class ChannelTypeApi(BaseRestModel):
	def get(self, project_db):
		SetupProjectDatabase.init(project_db)
		cha_type = 'lte'
		if Channel_con.select().count() > 0:
			cha_type = 'regular'

		return {'type': cha_type}


class ChandegConApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Chandeg_con, 'Channel', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Chandeg_con, 'Channel', 'lcha', Channel_lte_cha)

	def put(self, project_db, id):
		return self.put_con(project_db, id, 'lcha', Chandeg_con, Channel_lte_cha)


class ChandegConPostApi(BaseRestModel):
	def post(self, project_db):
		return self.post_con(project_db, 'lcha', Chandeg_con, Channel_lte_cha)


class ChandegConListApi(BaseRestModel):
	def get(self, project_db):
		table = Chandeg_con
		prop_table = Channel_lte_cha
		filter_cols = [table.name, table.wst, prop_table.init, prop_table.hyd, prop_table.nut]
		table_lookups = {
			table.wst: Weather_sta_cli
		}
		props_lookups = {
			prop_table.init: Initial_cha,
			prop_table.hyd: Hyd_sed_lte_cha,
			prop_table.nut: Nutrients_cha
		}

		items = self.base_connect_paged_items(project_db, table, prop_table, filter_cols, table_lookups, props_lookups)
		ml = []
		for v in items['model']:
			d = self.base_get_con_item_dict(v)
			d['init'] = self.base_get_prop_dict(v.lcha.init)
			d['hyd'] = self.base_get_prop_dict(v.lcha.hyd)
			d['nut'] = self.base_get_prop_dict(v.lcha.nut)
			ml.append(d)
		
		return {
			'total': items['total'],
			'matches': items['matches'],
			'items': ml
		}


class ChandegConMapApi(BaseRestModel):
	def get(self, project_db):
		return self.get_con_map(project_db, Chandeg_con)


class ChandegConOutApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Chandeg_con_out, 'Outflow', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Chandeg_con_out, 'Outflow')

	def put(self, project_db, id):
		return self.put_con_out(project_db, id, 'chandeg_con', Chandeg_con_out)


class ChandegConOutPostApi(BaseRestModel):
	def post(self, project_db):
		return self.post_con_out(project_db, 'chandeg_con', Chandeg_con_out)


class InitialChaListApi(BaseRestModel):
	def get(self, project_db):
		table = Initial_cha
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
	args = parser.parse_args(strict=True)
	return args


class InitialChaApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Initial_cha, 'Channel', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Initial_cha, 'Channel')

	def put(self, project_db, id):
		args = get_initial_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Initial_cha.get(Initial_cha.id == id)
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

			abort(400, message='Unable to update initial channel properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Initial channel properties name must be unique.')
		except Initial_cha.DoesNotExist:
			abort(404, message='Initial channel properties {id} does not exist'.format(id=id))
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


class InitialChaUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Initial_cha)

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

			query = Initial_cha.update(param_dict).where(Initial_cha.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update channel initial properties.')
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


class InitialChaPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_initial_args()
		try:
			SetupProjectDatabase.init(project_db)
			
			m = Initial_cha()
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

			abort(400, message='Unable to update initial channel properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Initial channel properties name must be unique.')
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


class NutrientsChaListApi(BaseRestModel):
	def get(self, project_db):
		table = Nutrients_cha
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols)


class NutrientsChaApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Nutrients_cha, 'Channel')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Nutrients_cha, 'Channel')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Nutrients_cha, 'Channel')


class NutrientsChaUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Nutrients_cha)

	def put(self, project_db):
		return self.base_put_many(project_db, Nutrients_cha, 'Channel')


class NutrientsChaPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Nutrients_cha, 'Channel')


""" Channel lte """

def get_cha_lte_args(get_selected_ids=False):
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
	parser.add_argument('hyd_name', type=str, required=False, location='json')
	parser.add_argument('nut_name', type=str, required=False, location='json')
	args = parser.parse_args(strict=False)
	return args


class ChannelLteChaListApi(BaseRestModel):
	def get(self, project_db):
		table = Channel_lte_cha
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols, True)


class ChannelLteChaApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Channel_lte_cha, 'Channel', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Channel_lte_cha, 'Channel')

	def put(self, project_db, id):
		args = get_cha_lte_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Channel_lte_cha.get(Channel_lte_cha.id == id)
			m.name = args['name']
			m.description = args['description']
			m.init_id = self.get_id_from_name(Initial_cha, args['init_name'])
			m.hyd_id = self.get_id_from_name(Hyd_sed_lte_cha, args['hyd_name'])
			m.nut_id = self.get_id_from_name(Nutrients_cha, args['nut_name'])

			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update channel properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Channel properties name must be unique.')
		except Channel_lte_cha.DoesNotExist:
			abort(404, message='Channel properties {id} does not exist'.format(id=id))
		except Initial_cha.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['init_name']))
		except Hyd_sed_lte_cha.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['hyd_name']))
		except Nutrients_cha.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['nut_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class ChannelLteChaUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Channel_lte_cha)

	def put(self, project_db):
		SetupProjectDatabase.init(project_db)
		args = get_cha_lte_args(True)
		
		try:
			param_dict = {}

			if args['init_name'] is not None:
				param_dict['init_id'] = self.get_id_from_name(Initial_cha, args['init_name'])
			if args['hyd_name'] is not None:
				param_dict['hyd_id'] = self.get_id_from_name(Hyd_sed_lte_cha, args['hyd_name'])
			if args['nut_name'] is not None:
				param_dict['nut_id'] = self.get_id_from_name(Nutrients_cha, args['nut_name'])

			con_table = Chandeg_con
			con_prop_field = Chandeg_con.lcha_id
			prop_table = Channel_lte_cha

			result = self.base_put_many_con(args, param_dict, con_table, con_prop_field, prop_table)
			if result > 0:
				return 200

			abort(400, message='Unable to update channel properties.')
		except Initial_cha.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['init_name']))
		except Hyd_sed_lte_cha.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['hyd_name']))
		except Nutrients_cha.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['nut_name']))
		except Weather_sta_cli.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['wst_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class ChannelLteChaPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_cha_lte_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Channel_lte_cha()
			m.name = args['name']
			m.description = args['description']
			m.init_id = self.get_id_from_name(Initial_cha, args['init_name'])
			m.hyd_id = self.get_id_from_name(Hyd_sed_lte_cha, args['hyd_name'])
			m.nut_id = self.get_id_from_name(Nutrients_cha, args['nut_name'])

			result = m.save()

			if result > 0:
				return {'id': m.id }, 200

			abort(400, message='Unable to update channel properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Channel properties name must be unique.')
		except Initial_cha.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['init_name']))
		except Hyd_sed_lte_cha.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['hyd_name']))
		except Nutrients_cha.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['nut_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class HydSedLteChaListApi(BaseRestModel):
	def get(self, project_db):
		table = Hyd_sed_lte_cha
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols)


class HydSedLteChaApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Hyd_sed_lte_cha, 'Channel')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Hyd_sed_lte_cha, 'Channel')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Hyd_sed_lte_cha, 'Channel')


class HydSedLteChaUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Hyd_sed_lte_cha)

	def put(self, project_db):
		return self.base_put_many(project_db, Hyd_sed_lte_cha, 'Channel')


class HydSedLteChaPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Hyd_sed_lte_cha, 'Channel')
