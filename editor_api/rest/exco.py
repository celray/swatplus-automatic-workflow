from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project.setup import SetupProjectDatabase
from database.project.connect import Exco_con, Exco_con_out
from database.project.exco import Exco_exc, Exco_om_exc, Exco_pest_exc, Exco_path_exc, Exco_hmet_exc, Exco_salt_exc
from database.project.climate import Weather_sta_cli

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
	parser.add_argument('exco', type=int, required=False, location='json')
	parser.add_argument('exco_name', type=str, required=False, location='json')
	args = parser.parse_args(strict=True)
	return args


class ExcoConApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Exco_con, 'Exco', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Exco_con, 'Exco')

	def put(self, project_db, id):
		args = get_con_args()
		try:
			SetupProjectDatabase.init(project_db)
			m = Exco_con.get(Exco_con.id == id)
			m.name = args['name']
			m.area = args['area']
			m.lat = args['lat']
			m.lon = args['lon']
			m.elev = args['elev']

			if args['exco_name'] is not None:
				m.exco_id = self.get_id_from_name(Exco_exc, args['exco_name'])

			if args['wst_name'] is not None:
				m.wst_id = self.get_id_from_name(Weather_sta_cli, args['wst_name'])

			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update Exco {id}.'.format(id=id))
		except IntegrityError:
			abort(400, message='Exco name must be unique.')
		except Exco_con.DoesNotExist:
			abort(404, message='Exco {id} does not exist'.format(id=id))
		except Exco_exc.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['exco_name']))
		except Weather_sta_cli.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['wst_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class ExcoConPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_con_args()
		SetupProjectDatabase.init(project_db)

		try:
			e = Exco_con.get(Exco_con.name == args['name'])
			abort(400, message='Exco name must be unique.  Exco with this name already exists.')
		except Exco_con.DoesNotExist:
			try:
				m = Exco_con()
				m.name = args['name']
				m.area = args['area']
				m.lat = args['lat']
				m.lon = args['lon']
				m.elev = args['elev']
				m.ovfl = 0
				m.rule = 0

				if args['exco_name'] is not None:
					m.exco_id = self.get_id_from_name(Exco_exc, args['exco_name'])

				if args['wst_name'] is not None:
					m.wst_id = self.get_id_from_name(Weather_sta_cli, args['wst_name'])

				result = m.save()

				if result > 0:
					return model_to_dict(m), 201

				abort(400, message='Unable to create Exco.')
			except IntegrityError:
				abort(400, message='Exco name must be unique.')
			except Exco_exc.DoesNotExist:
				abort(400, message=invalid_name_msg.format(name=args['exco_name']))
			except Weather_sta_cli.DoesNotExist:
				abort(400, message=invalid_name_msg.format(name=args['wst_name']))
			except Exception as ex:
				abort(400, message="Unexpected error {ex}".format(ex=ex))


class ExcoConListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Exco_con
		list_name = 'exco'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name, True)


class ExcoConMapApi(BaseRestModel):
	def get(self, project_db):
		return self.get_con_map(project_db, Exco_con)


def get_con_out_args():
	parser = reqparse.RequestParser()
	parser.add_argument('id', type=int, required=False, location='json')
	parser.add_argument('order', type=int, required=True, location='json')
	parser.add_argument('obj_typ', type=str, required=True, location='json')
	parser.add_argument('obj_id', type=int, required=True, location='json')
	parser.add_argument('hyd_typ', type=str, required=True, location='json')
	parser.add_argument('frac', type=float, required=True, location='json')
	parser.add_argument('exco_con_id', type=int, required=False, location='json')
	args = parser.parse_args(strict=True)
	return args


class ExcoConOutApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Exco_con_out, 'Outflow', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Exco_con_out, 'Outflow')

	def put(self, project_db, id):
		try:
			args = get_con_out_args()
			SetupProjectDatabase.init(project_db)

			m = Exco_con_out.get(Exco_con_out.id == id)
			m.order = args['order']
			m.obj_typ = args['obj_typ']
			m.obj_id = args['obj_id']
			m.hyd_typ = args['hyd_typ']
			m.frac = args['frac']

			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update exco outflow {id}.'.format(id=id))
		except Exco_con_out.DoesNotExist:
			abort(404, message='Exco outflow {id} does not exist'.format(id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class ExcoConOutPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_con_out_args()
		SetupProjectDatabase.init(project_db)

		try:
			m = Exco_con_out()
			m.order = args['order']
			m.obj_typ = args['obj_typ']
			m.obj_id = args['obj_id']
			m.hyd_typ = args['hyd_typ']
			m.frac = args['frac']
			m.exco_con_id = args['exco_con_id']

			result = m.save()

			if result > 0:
				return model_to_dict(m), 201

			abort(400, message='Unable to create exco outflow.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


def get_exco_args(get_selected_ids=False):
	parser = reqparse.RequestParser()

	if get_selected_ids:
		parser.add_argument('selected_ids', type=int, action='append', required=False, location='json')
	else:
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('name', type=str, required=True, location='json')

	parser.add_argument('om_name', type=str, required=True, location='json')
	parser.add_argument('pest_name', type=str, required=True, location='json')
	parser.add_argument('path_name', type=str, required=True, location='json')
	parser.add_argument('hmet_name', type=str, required=True, location='json')
	parser.add_argument('salt_name', type=str, required=True, location='json')
	args = parser.parse_args(strict=True)
	return args


class ExcoExcListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Exco_exc
		list_name = 'exco'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name, True)


class ExcoExcApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Exco_exc, 'Exco', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Exco_exc, 'Exco')

	def put(self, project_db, id):
		args = get_exco_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Exco_exc.get(Exco_exc.id == id)
			m.name = args['name']
			m.om_id = self.get_id_from_name(Exco_om_exc, args['om_name'])
			m.pest_id = self.get_id_from_name(Exco_pest_exc, args['pest_name'])
			m.path_id = self.get_id_from_name(Exco_path_exc, args['path_name'])
			m.hmet_id = self.get_id_from_name(Exco_hmet_exc, args['hmet_name'])
			m.salt_id = self.get_id_from_name(Exco_salt_exc, args['salt_name'])

			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update exco properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Exco properties name must be unique.')
		except Exco_exc.DoesNotExist:
			abort(404, message='Exco properties {id} does not exist'.format(id=id))
		except Exco_om_exc.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['om_name']))
		except Exco_pest_exc.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['pest_name']))
		except Exco_path_exc.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['path_name']))
		except Exco_hmet_exc.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hmet_name']))
		except Exco_salt_exc.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['salt_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class ExcoExcUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Exco_exc)

	def put(self, project_db):
		SetupProjectDatabase.init(project_db)
		args = get_exco_args(True)
		try:
			param_dict = {}

			if args['om_name'] is not None:
				param_dict['om_id'] = self.get_id_from_name(Exco_om_exc, args['om_name'])
			if args['pest_name'] is not None:
				param_dict['pest_id'] = self.get_id_from_name(Exco_pest_exc, args['pest_name'])
			if args['path_name'] is not None:
				param_dict['path_id'] = self.get_id_from_name(Exco_path_exc, args['path_name'])
			if args['hmet_name'] is not None:
				param_dict['hmet_id'] = self.get_id_from_name(Exco_hmet_exc, args['hmet_name'])
			if args['salt_name'] is not None:
				param_dict['salt_id'] = self.get_id_from_name(Exco_salt_exc, args['salt_name'])

			query = Exco_exc.update(param_dict).where(Exco_exc.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update exco properties.')
		except Exco_om_exc.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['om_name']))
		except Exco_pest_exc.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['pest_name']))
		except Exco_path_exc.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['path_name']))
		except Exco_hmet_exc.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hmet_name']))
		except Exco_salt_exc.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['salt_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class ExcoExcPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_exco_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Exco_exc()
			m.name = args['name']
			m.om_id = self.get_id_from_name(Exco_om_exc, args['om_name'])
			m.pest_id = self.get_id_from_name(Exco_pest_exc, args['pest_name'])
			m.path_id = self.get_id_from_name(Exco_path_exc, args['path_name'])
			m.hmet_id = self.get_id_from_name(Exco_hmet_exc, args['hmet_name'])
			m.salt_id = self.get_id_from_name(Exco_salt_exc, args['salt_name'])

			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update exco properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Exco properties name must be unique.')
		except Exco_om_exc.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['om_name']))
		except Exco_pest_exc.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['pest_name']))
		except Exco_path_exc.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['path_name']))
		except Exco_hmet_exc.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hmet_name']))
		except Exco_salt_exc.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['salt_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class ExcoOMListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Exco_om_exc
		list_name = 'exco'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


def save_exco_om_exc(m, args):
	m.name = args['name']
	m.flo = args['flo']
	m.sed = args['sed']
	m.orgn = args['orgn']
	m.sedp = args['sedp']
	m.no3 = args['no3']
	m.solp = args['solp']
	m.chla = args['chla']
	m.nh3 = args['nh3']
	m.no2 = args['no2']
	m.cbod = args['cbod']
	m.dox = args['dox']
	m.sand = args['sand']
	m.silt = args['silt']
	m.clay = args['clay']
	m.sag = args['sag']
	m.lag = args['lag']
	m.gravel = args['gravel']
	m.tmp = args['tmp']
	return m.save()


class ExcoOMApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Exco_om_exc, 'Exco')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Exco_om_exc, 'Exco')

	def put(self, project_db, id):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('exco_om_exc', project_db)

			m = Exco_om_exc.get(Exco_om_exc.id == id)
			result = save_exco_om_exc(m, args)

			if result > 0:
				return 200

			abort(400, message='Unable to update om exco properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Exco om properties name must be unique.')
		except Exco_om_exc.DoesNotExist:
			abort(404, message='Exco om properties {id} does not exist'.format(id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class ExcoOMUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Exco_om_exc)

	def put(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('exco_om_exc', project_db, True)

			param_dict = {}
			for key in args.keys():
				if args[key] is not None and key != 'selected_ids':
					param_dict[key] = args[key]

			query = Exco_om_exc.update(param_dict).where(Exco_om_exc.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update exco om properties.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class ExcoOMPostApi(BaseRestModel):
	def post(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)		
			args = self.get_args('exco_om_exc', project_db)	

			m = Exco_om_exc()
			result = save_exco_om_exc(m, args)

			if result > 0:
				return model_to_dict(m), 201

			abort(400, message='Unable to update exco om properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Exco om properties name must be unique.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))

