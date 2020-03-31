from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project.setup import SetupProjectDatabase
from database.project.climate import Weather_sta_cli
from database.project.routing_unit import Rout_unit_rtu
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
			abort(404, message='No routing unit connections in database.')


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
	parser.add_argument('rtu', type=int, required=False, location='json')
	parser.add_argument('rtu_name', type=str, required=False, location='json')
	args = parser.parse_args(strict=True)
	return args


class RoutingUnitConApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Rout_unit_con, 'Rout_unit', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Rout_unit_con, 'Rout_unit')

	def put(self, project_db, id):
		args = get_con_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Rout_unit_con.get(Rout_unit_con.id == id)
			m.name = args['name']
			m.area = args['area']
			m.lat = args['lat']
			m.lon = args['lon']
			m.elev = args['elev']

			m.rtu_id = self.get_id_from_name(Rout_unit_rtu, args['rtu_name'])

			if args['wst_name'] is not None:
				m.wst_id = self.get_id_from_name(Weather_sta_cli, args['wst_name'])

			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update Routing Unit {id}.'.format(id=id))
		except IntegrityError:
			abort(400, message='Routing unit name must be unique.')
		except Rout_unit_con.DoesNotExist:
			abort(404, message='Rout_unit {id} does not exist'.format(id=id))
		except Rout_unit_rtu.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['rtu_name']))
		except Weather_sta_cli.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['wst_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class RoutingUnitConPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_con_args()
		SetupProjectDatabase.init(project_db)

		try:
			e = Rout_unit_con.get(Rout_unit_con.name == args['name'])
			abort(400, message='Routing unit name must be unique. Routing unit with this name already exists.')
		except Rout_unit_con.DoesNotExist:
			try:
				m = Rout_unit_con()
				m.name = args['name']
				m.area = args['area']
				m.lat = args['lat']
				m.lon = args['lon']
				m.elev = args['elev']
				m.ovfl = 0
				m.rule = 0

				m.rtu_id = self.get_id_from_name(Rout_unit_rtu, args['rtu_name'])

				if args['wst_name'] is not None:
					m.wst_id = self.get_id_from_name(Weather_sta_cli, args['wst_name'])

				result = m.save()

				if result > 0:
					return model_to_dict(m), 201

				abort(400, message='Unable to create Routingunit.')
			except IntegrityError:
				abort(400, message='Routing unit name must be unique.')
			except Rout_unit_rtu.DoesNotExist:
				abort(400, message=invalid_name_msg.format(name=args['rtu_name']))
			except Weather_sta_cli.DoesNotExist:
				abort(400, message=invalid_name_msg.format(name=args['wst_name']))
			except Exception as ex:
				abort(400, message="Unexpected error {ex}".format(ex=ex))


class RoutingUnitConListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Rout_unit_con
		list_name = 'routing_unit'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name, True)


class RoutingUnitConMapApi(BaseRestModel):
	def get(self, project_db):
		return self.get_con_map(project_db, Rout_unit_con)


def get_con_out_args():
	parser = reqparse.RequestParser()
	parser.add_argument('id', type=int, required=False, location='json')
	parser.add_argument('order', type=int, required=True, location='json')
	parser.add_argument('obj_typ', type=str, required=True, location='json')
	parser.add_argument('obj_id', type=int, required=True, location='json')
	parser.add_argument('hyd_typ', type=str, required=True, location='json')
	parser.add_argument('frac', type=float, required=True, location='json')
	parser.add_argument('rtu_con_id', type=int, required=False, location='json')
	args = parser.parse_args(strict=True)
	return args


class RoutingUnitConOutApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Rout_unit_con_out, 'Outflow', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Rout_unit_con_out, 'Outflow')

	def put(self, project_db, id):
		try:
			args = get_con_out_args()
			SetupProjectDatabase.init(project_db)

			m = Rout_unit_con_out.get(Rout_unit_con_out.id == id)
			m.order = args['order']
			m.obj_typ = args['obj_typ']
			m.obj_id = args['obj_id']
			m.hyd_typ = args['hyd_typ']
			m.frac = args['frac']

			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update Routing unit outflow {id}.'.format(id=id))
		except Rout_unit_con_out.DoesNotExist:
			abort(404, message='Routing Unit outflow {id} does not exist'.format(id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class RoutingUnitConOutPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_con_out_args()
		SetupProjectDatabase.init(project_db)

		try:
			m = Rout_unit_con_out()
			m.order = args['order']
			m.obj_typ = args['obj_typ']
			m.obj_id = args['obj_id']
			m.hyd_typ = args['hyd_typ']
			m.frac = args['frac']
			m.rtu_con_id = args['rtu_con_id']

			result = m.save()

			if result > 0:
				return model_to_dict(m), 201

			abort(400, message='Unable to create routingunit outflow.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


def get_routingunit_args(get_selected_ids=False):
	parser = reqparse.RequestParser()

	if get_selected_ids:
		parser.add_argument('selected_ids', type=int, action='append', required=False, location='json')
	else:
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('name', type=str, required=True, location='json')
		parser.add_argument('description', type=str, required=False, location='json')

	parser.add_argument('dlr_name', type=str, required=False, location='json')
	parser.add_argument('topo_name', type=str, required=False, location='json')
	parser.add_argument('field_name', type=str, required=False, location='json')
	args = parser.parse_args(strict=True)
	return args


class RoutingUnitRtuListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Rout_unit_rtu
		list_name = 'routing_unit'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name, True)


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

			query = Rout_unit_rtu.update(param_dict).where(Rout_unit_rtu.id.in_(args['selected_ids']))
			result = query.execute()

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
				return 200

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
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Rout_unit_ele
		list_name = 'rout_unit_eles'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name, back_refs=True)


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
