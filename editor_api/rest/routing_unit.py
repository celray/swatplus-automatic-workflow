from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project.setup import SetupProjectDatabase
from database.project.climate import Weather_sta_cli
from database.project.routing_unit import Rout_unit_rtu, Rout_unit_dr
from database.project.connect import Rout_unit_con, Rout_unit_con_out, Rout_unit_ele, Chandeg_con
from database.project.dr import Delratio_del
from database.project.hydrology import Topography_hyd, Field_fld

invalid_name_msg = 'Invalid name {name}. Please ensure the value exists in your database.'

class RoutUnitBoundariesApi(Resource):
	def get(self, project_db):
		SetupProjectDatabase.init(project_db)
		if Rout_unit_con.select().count() > 0:
			m = Rout_unit_con.select(
				fn.Max(Rout_unit_con.lat).alias('n'),
				fn.Min(Rout_unit_con.lat).alias('s'),
				fn.Max(Rout_unit_con.lon).alias('e'),
				fn.Min(Rout_unit_con.lon).alias('w')
			).scalar(as_tuple=True)
			return {
				'n': m[0],
				's': m[1],
				'e': m[2],
				'w': m[3]
			}
		elif Chandeg_con.select().count() > 0: # Quick fix for lte
			m = Chandeg_con.select(
				fn.Max(Chandeg_con.lat).alias('n'),
				fn.Min(Chandeg_con.lat).alias('s'),
				fn.Max(Chandeg_con.lon).alias('e'),
				fn.Min(Chandeg_con.lon).alias('w')
			).scalar(as_tuple=True)
			return {
				'n': m[0],
				's': m[1],
				'e': m[2],
				'w': m[3]
			}
		else:
			return {
				'n': 0,
				's': 0,
				'e': 0,
				'w': 0
			}


class RoutingUnitConApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Rout_unit_con, 'Rout_unit', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Rout_unit_con, 'Rout_unit', 'rtu', Rout_unit_rtu)

	def put(self, project_db, id):
		return self.put_con(project_db, id, 'rtu', Rout_unit_con, Rout_unit_rtu)


class RoutingUnitConPostApi(BaseRestModel):
	def post(self, project_db):
		return self.post_con(project_db, 'rtu', Rout_unit_con, Rout_unit_rtu)


class RoutingUnitConListApi(BaseRestModel):
	def get(self, project_db):
		table = Rout_unit_con
		prop_table = Rout_unit_rtu
		filter_cols = [table.name, table.wst, prop_table.dlr, prop_table.topo, prop_table.field]
		table_lookups = {
			table.wst: Weather_sta_cli
		}
		props_lookups = {
			prop_table.dlr: Rout_unit_dr,
			prop_table.topo: Topography_hyd,
			prop_table.field: Field_fld
		}

		items = self.base_connect_paged_items(project_db, table, prop_table, filter_cols, table_lookups, props_lookups)
		ml = []
		for v in items['model']:
			d = self.base_get_con_item_dict(v)
			d['dlr'] = self.base_get_prop_dict(v.rtu.dlr)
			d['topo'] = self.base_get_prop_dict(v.rtu.topo)
			d['field'] = self.base_get_prop_dict(v.rtu.field)
			ml.append(d)
		
		return {
			'total': items['total'],
			'matches': items['matches'],
			'items': ml
		}


class RoutingUnitConMapApi(BaseRestModel):
	def get(self, project_db):
		return self.get_con_map(project_db, Rout_unit_con)


class RoutingUnitConOutApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Rout_unit_con_out, 'Outflow', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Rout_unit_con_out, 'Outflow')

	def put(self, project_db, id):
		return self.put_con_out(project_db, id, 'rtu_con', Rout_unit_con_out)


class RoutingUnitConOutPostApi(BaseRestModel):
	def post(self, project_db):
		return self.post_con_out(project_db, 'rtu_con', Rout_unit_con_out)


def get_routingunit_args(get_selected_ids=False):
	parser = reqparse.RequestParser()

	if get_selected_ids:
		parser.add_argument('selected_ids', type=int, action='append', required=False, location='json')
		parser.add_argument('elev', type=float, required=False, location='json')
		parser.add_argument('wst_name', type=str, required=False, location='json')
	else:
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('name', type=str, required=True, location='json')
		parser.add_argument('description', type=str, required=False, location='json')

	parser.add_argument('dlr_name', type=str, required=False, location='json')
	parser.add_argument('topo_name', type=str, required=False, location='json')
	parser.add_argument('field_name', type=str, required=False, location='json')
	args = parser.parse_args(strict=False)
	return args


class RoutingUnitRtuListApi(BaseRestModel):
	def get(self, project_db):
		table = Rout_unit_rtu
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols, True)


class RoutingUnitRtuApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Rout_unit_rtu, 'Rout_unit', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Rout_unit_rtu, 'Rout_unit')

	def put(self, project_db, id):
		args = get_routingunit_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Rout_unit_rtu.get(Rout_unit_rtu.id == id)
			m.name = args['name']
			m.description = args['description']
			if args['dlr_name']:
				m.dlr_id = self.get_id_from_name(Delratio_del, args['dlr_name'])
			if args['topo_name']:
				m.topo_id = self.get_id_from_name(Topography_hyd, args['topo_name'])
			if args['field_name']:
				m.field_id = self.get_id_from_name(Field_fld, args['field_name'])
			
			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update routing unit properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Routing unit properties name must be unique.')
		except Rout_unit_rtu.DoesNotExist:
			abort(404, message='Routing unit properties {id} does not exist'.format(id=id))
		except Topography_hyd.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['topo_name']))
		except Delratio_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['dlr_name']))
		except Field_fld.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['field_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class RoutingUnitRtuUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Rout_unit_rtu)

	def put(self, project_db):
		SetupProjectDatabase.init(project_db)
		args = get_routingunit_args(True)

		try:
			param_dict = {}

			if args['dlr_name'] is not None:
				param_dict['dlr_id'] = self.get_id_from_name(Delratio_del, args['dlr_name'])
			if args['topo_name'] is not None:
				param_dict['topo_id'] = self.get_id_from_name(Topography_hyd, args['topo_name'])			
			if args['field_name'] is not None:
				param_dict['field_id'] = self.get_id_from_name(Field_fld, args['field_name'])

			con_table = Rout_unit_con
			con_prop_field = Rout_unit_con.rtu_id
			prop_table = Rout_unit_rtu

			result = self.base_put_many_con(args, param_dict, con_table, con_prop_field, prop_table)
			if result > 0:
				return 200

			abort(400, message='Unable to update routing unit properties.')
		except Delratio_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['dlr_name']))
		except Topography_hyd.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['topo_name']))
		except Field_fld.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['field_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class RoutingUnitRtuPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_routingunit_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Rout_unit_rtu()
			m.name = args['name']
			m.description = args['description']
			if args['dlr_name']:
				m.dlr_id = self.get_id_from_name(Delratio_del, args['dlr_name'])

			m.topo_id = self.get_id_from_name(Topography_hyd, args['topo_name'])
			m.field_id = self.get_id_from_name(Field_fld, args['field_name'])

			result = m.save()

			if result > 0:
				return {'id': m.id }, 200

			abort(400, message='Unable to update routing unit properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Routing unit properties name must be unique.')
		except Delratio_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['dlr_name']))
		except Topography_hyd.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['topo_name']))
		except Field_fld.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['field_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex)) 


class RoutingUnitEleListApi(BaseRestModel):
	def get(self, project_db):
		table = Rout_unit_ele
		filter_cols = [table.name, table.rtu, table.obj_typ, table.dlr]
		return self.base_paged_list(project_db, table, filter_cols, True)


class RoutingUnitEleApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Rout_unit_ele, 'Routing unit element', back_refs=True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Rout_unit_ele, 'Routing unit element')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Rout_unit_ele, 'Routing unit element')


class RoutingUnitElePostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Rout_unit_ele, 'Routing unit element')
