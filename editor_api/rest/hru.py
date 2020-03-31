from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project.setup import SetupProjectDatabase
from database.project.climate import Weather_sta_cli
from database.project.connect import Hru_con, Hru_con_out, Hru_lte_con, Hru_lte_con_out
from database.project.hru import Hru_data_hru, Hru_lte_hru
from database.project.hydrology import Hydrology_hyd, Topography_hyd, Field_fld
from database.project.soils import Nutrients_sol, Soils_sol
from database.project.lum import Landuse_lum
from database.project.hru_parm_db import Snow_sno
from database.project.init import Soil_plant_ini
from database.project.decision_table import D_table_dtl
from database.project.reservoir import Wetland_wet

import ast


class HruConApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Hru_con, 'Hru', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Hru_con, 'Hru')

	def put(self, project_db, id):
		return self.put_con(project_db, id, 'hru', Hru_con, Hru_data_hru)


class HruConPostApi(BaseRestModel):
	def post(self, project_db):
		return self.post_con(project_db, 'hru', Hru_con, Hru_data_hru)


class HruConListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Hru_con
		list_name = 'hrus'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name, True)


class HruConMapApi(BaseRestModel):
	def get(self, project_db):
		return self.get_con_map(project_db, Hru_con)


class HruConOutApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Hru_con_out, 'Outflow', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Hru_con_out, 'Outflow')

	def put(self, project_db, id):
		return self.put_con_out(project_db, id, 'hru_con', Hru_con_out)


class HruConOutPostApi(BaseRestModel):
	def post(self, project_db):
		return self.post_con_out(project_db, 'hru_con', Hru_con_out)


def get_hru_args(get_selected_ids=False):
	parser = reqparse.RequestParser()

	if get_selected_ids:
		parser.add_argument('selected_ids', type=int, action='append', required=False, location='json')
	else:
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('name', type=str, required=True, location='json')
		parser.add_argument('description', type=str, required=False, location='json')

	parser.add_argument('topo_name', type=str, required=True, location='json')
	parser.add_argument('hyd_name', type=str, required=True, location='json')
	parser.add_argument('soil_name', type=str, required=True, location='json')
	parser.add_argument('lu_mgt_name', type=str, required=True, location='json')
	parser.add_argument('soil_plant_init_name', type=str, required=True, location='json')
	parser.add_argument('surf_stor', type=str, required=False, location='json')
	parser.add_argument('snow_name', type=str, required=True, location='json')
	parser.add_argument('field_name', type=str, required=True, location='json')
	args = parser.parse_args(strict=True)
	return args


class HruDataHruListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Hru_data_hru
		list_name = 'hrus'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name, True)


class HruDataHruApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Hru_data_hru, 'Hru', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Hru_data_hru, 'Hru')

	def put(self, project_db, id):
		args = get_hru_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Hru_data_hru.get(Hru_data_hru.id == id)
			m.name = args['name']
			m.description = args['description']
			
			if args['topo_name']:
				m.topo_id = self.get_id_from_name(Topography_hyd, args['topo_name'])
			if args['hyd_name']:
				m.hydro_id = self.get_id_from_name(Hydrology_hyd, args['hyd_name'])
			if args['soil_name']:
				m.soil_id = self.get_id_from_name(Soils_sol, args['soil_name'])
			if args['lu_mgt_name']:
				m.lu_mgt_id = self.get_id_from_name(Landuse_lum, args['lu_mgt_name'])
			if args['soil_plant_init_name']:
				m.soil_plant_init_id = self.get_id_from_name(Soil_plant_ini, args['soil_plant_init_name'])
			if args['surf_stor']:
				m.surf_stor_id = self.get_id_from_name(Wetland_wet, args['surf_stor'])
			if args['snow_name']:
				m.snow_id = self.get_id_from_name(Snow_sno, args['snow_name'])
			if args['field_name']:
				m.field_id = self.get_id_from_name(Field_fld, args['field_name'])
			
			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update hru properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Hru properties name must be unique.')
		except Hru_data_hru.DoesNotExist:
			abort(404, message='Hru properties {id} does not exist'.format(id=id))
		except Topography_hyd.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['topo_name']))
		except Hydrology_hyd.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['hyd_name']))
		except Soils_sol.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['soil_name']))
		except Landuse_lum.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['lu_mgt_name']))
		except Soil_plant_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['soil_plant_init_name']))
		except Wetland_wet.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['surf_stor']))
		except Snow_sno.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['snow_name']))
		except Field_fld.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['field_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class HruDataHruUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Hru_data_hru)

	def put(self, project_db):
		SetupProjectDatabase.init(project_db)
		args = get_hru_args(True)

		try:
			param_dict = {}

			if args['topo_name'] is not None:
				param_dict['topo_id'] = self.get_id_from_name(Topography_hyd, args['topo_name'])
			if args['hyd_name'] is not None:
				param_dict['hydro_id'] = self.get_id_from_name(Hydrology_hyd, args['hyd_name'])
			if args['soil_name'] is not None:
				param_dict['soil_id'] = self.get_id_from_name(Soils_sol, args['soil_name'])
			if args['lu_mgt_name'] is not None:
				param_dict['lu_mgt_id'] = self.get_id_from_name(Landuse_lum, args['lu_mgt_name'])
			if args['soil_plant_init_name'] is not None:
				param_dict['soil_plant_init_id'] = self.get_id_from_name(Soil_plant_ini, args['soil_plant_init_name'])
			if args['surf_stor'] is not None:
				param_dict['surf_stor_id'] = self.get_id_from_name(Wetland_wet, args['surf_stor'])
			if args['snow_name'] is not None:
				param_dict['snow_id'] = self.get_id_from_name(Snow_sno, args['snow_name'])
			if args['field_name'] is not None:
				param_dict['field_id'] = self.get_id_from_name(Field_fld, args['field_name'])

			query = Hru_data_hru.update(param_dict).where(Hru_data_hru.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update hru properties.')
		except Topography_hyd.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['topo_name']))
		except Hydrology_hyd.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['hyd_name']))
		except Soils_sol.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['soil_name']))
		except Landuse_lum.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['lu_mgt_name']))
		except Soil_plant_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['soil_plant_init_name']))
		except Wetland_wet.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['surf_stor']))
		except Snow_sno.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['snow_name']))
		except Field_fld.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['field_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class HruDataHruPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_hru_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Hru_data_hru()
			m.name = args['name']
			m.description = args['description']
			m.topo_id = self.get_id_from_name(Topography_hyd, args['topo_name'])
			m.hydro_id = self.get_id_from_name(Hydrology_hyd, args['hyd_name'])
			m.soil_id = self.get_id_from_name(Soils_sol, args['soil_name'])
			m.lu_mgt_id = self.get_id_from_name(Landuse_lum, args['lu_mgt_name'])
			m.soil_plant_init_id = self.get_id_from_name(Soil_plant_ini, args['soil_plant_init_name'])
			m.surf_stor_id = self.get_id_from_name(Wetland_wet, args['surf_stor'])
			m.snow_id = self.get_id_from_name(Snow_sno, args['snow_name'])
			m.field_id = self.get_id_from_name(Field_fld, args['field_name'])

			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update hru properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Hru properties name must be unique.')
		except Topography_hyd.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['topo_name']))
		except Hydrology_hyd.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['hyd_name']))
		except Soils_sol.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['soil_name']))
		except Landuse_lum.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['lu_mgt_name']))
		except Soil_plant_ini.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['soil_plant_init_name']))
		except Wetland_wet.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['surf_stor']))
		except Snow_sno.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['snow_name']))
		except Field_fld.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['field_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


""" HRU-lte section"""
class HruLteConApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Hru_lte_con, 'Hru', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Hru_lte_con, 'Hru')

	def put(self, project_db, id):
		return self.put_con(project_db, id, 'lhru', Hru_lte_con, Hru_lte_hru)


class HruLteConPostApi(BaseRestModel):
	def post(self, project_db):
		return self.post_con(project_db, 'lhru', Hru_lte_con, Hru_lte_hru)


class HruLteConListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Hru_lte_con
		list_name = 'hrus-lte'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name, True)


class HruLteConMapApi(BaseRestModel):
	def get(self, project_db):
		return self.get_con_map(project_db, Hru_lte_con)


class HruLteConOutApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Hru_lte_con_out, 'Outflow', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Hru_lte_con_out, 'Outflow')

	def put(self, project_db, id):
		return self.put_con_out(project_db, id, 'hru_lte_con', Hru_lte_con_out)


class HruLteConOutPostApi(BaseRestModel):
	def post(self, project_db):
		return self.post_con_out(project_db, 'hru_lte_con', Hru_lte_con_out)


class HruLteListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Hru_lte_hru
		list_name = 'hrus-lte'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name, back_refs=True)


class HruLteApi(BaseRestModel):
	def get(self, project_db, id):
		table = Hru_lte_hru
		description = 'Hru'

		SetupProjectDatabase.init(project_db)
		try:
			m = table.get(table.id == id)
			d = model_to_dict(m, backrefs=True, max_depth=1)
			d['grow_start'] = m.grow_start.name
			d['grow_end'] = m.grow_end.name
			return d
		except table.DoesNotExist:
			abort(404, message='{description} {id} does not exist'.format(description=description, id=id))

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Hru_lte_hru, 'Hru')

	def put(self, project_db, id):
		try:
			SetupProjectDatabase.init(project_db)

			lookup_args = [
				{'name': 'grow_start', 'type': str},
				{'name': 'grow_end', 'type': str}
			]
			args = self.get_args('hru_lte_hru', project_db, extra_args=lookup_args)

			args['grow_start_id'] = self.get_id_from_name(D_table_dtl, args['grow_start'])
			args['grow_end_id'] = self.get_id_from_name(D_table_dtl, args['grow_end'])

			args.pop('grow_start', None)
			args.pop('grow_end', None)

			result = self.save_args(Hru_lte_hru, args, id=id, lookup_fields=['soil_text', 'plnt_typ'])

			if result > 0:
				return 200

			abort(400, message='Unable to update hru {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Graze operation name must be unique.')
		except Hru_lte_hru.DoesNotExist:
			abort(404, message='Hru-lte {id} does not exist'.format(id=id))
		except Exception as ex:
			abort(400, message='Unexpected error {ex}'.format(ex=ex))


class HruLtePostApi(BaseRestModel):
	def post(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			lookup_args = [
				{'name': 'grow_start', 'type': str},
				{'name': 'grow_end', 'type': str}
			]
			args = self.get_args('hru_lte_hru', project_db, extra_args=lookup_args)

			args['grow_start_id'] = self.get_id_from_name(D_table_dtl, args['grow_start'])
			args['grow_end_id'] = self.get_id_from_name(D_table_dtl, args['grow_end'])

			args.pop('grow_start', None)
			args.pop('grow_end', None)

			result = self.save_args(Hru_lte_hru, args, is_new=True, lookup_fields=['soil_text', 'plnt_typ'])

			if result > 0:
				return 201

			abort(400, message='Unable to update HRU {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Name must be unique. ' + str(e))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class HruLteUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Hru_lte_hru)

	def put(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			lookup_args = [
				{'name': 'grow_start', 'type': str},
				{'name': 'grow_end', 'type': str}
			]
			args = self.get_args('hru_lte_hru', project_db, True, extra_args=lookup_args)

			if args['grow_start'] is not None:
				args['grow_start_id'] = self.get_id_from_name(D_table_dtl, args['grow_start'])
				args.pop('grow_start', None)

			if args['grow_end'] is not None:
				args['grow_end_id'] = self.get_id_from_name(D_table_dtl, args['grow_end'])
				args.pop('grow_end', None)

			lookup_fields = ['soil_text', 'plnt_typ']

			param_dict = {}
			for key in args.keys():
				if args[key] is not None and key != 'selected_ids':
					if key in lookup_fields:
						d = ast.literal_eval(args[key])
						if int(d['id']) != 0:
							param_dict[key] = int(d['id'])
					else:
						param_dict[key] = args[key]

			query = Hru_lte_hru.update(param_dict).where(Hru_lte_hru.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update HRUs.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))
