from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project import base as project_base
from database.project.setup import SetupProjectDatabase
from database.project.hydrology import Hydrology_hyd, Topography_hyd, Field_fld

from database.project.climate import Weather_sta_cli
from database.project.config import Project_config

from database.datasets.setup import SetupDatasetsDatabase
from database.datasets.definitions import Var_range

import os.path

invalid_name_msg = 'Invalid name {name}. Please ensure the value exists in your database.'


def get_hyd_args():
	parser = reqparse.RequestParser()
	parser.add_argument('id', type=int, required=False, location='json')
	parser.add_argument('name', type=str, required=True, location='json')
	parser.add_argument('lat_ttime', type=float, required=True, location='json')
	parser.add_argument('lat_sed', type=float, required=True, location='json')
	parser.add_argument('can_max', type=float, required=True, location='json')
	parser.add_argument('esco', type=float, required=True, location='json')
	parser.add_argument('epco', type=float, required=True, location='json')
	parser.add_argument('orgn_enrich', type=float, required=True, location='json')
	parser.add_argument('orgp_enrich', type=float, required=True, location='json')
	parser.add_argument('evap_pothole', type=float, required=True, location='json')
	parser.add_argument('bio_mix', type=float, required=True, location='json')
	parser.add_argument('lat_orgn', type=float, required=True, location='json')
	parser.add_argument('lat_orgp', type=float, required=True, location='json')
	parser.add_argument('harg_pet', type=float, required=True, location='json')
	parser.add_argument('cn_plntet', type=float, required=True, location='json')
	parser.add_argument('perco', type=float, required=True, location='json')
	args = parser.parse_args(strict=True)
	return args


def save_hyd(m, args):
	m.name = args['name']
	m.lat_ttime = args['lat_ttime']
	m.lat_sed = args['lat_sed']
	m.can_max = args['can_max']
	m.esco = args['esco']
	m.epco = args['epco']
	m.orgn_enrich = args['orgn_enrich']
	m.orgp_enrich = args['orgp_enrich']
	m.evap_pothole = args['evap_pothole']
	m.bio_mix = args['bio_mix']
	m.lat_orgn = args['lat_orgn']
	m.lat_orgp = args['lat_orgp']
	m.harg_pet = args['harg_pet']
	m.cn_plntet = args['cn_plntet']
	m.perco = args['perco']
	return m.save()


class HydrologyHydListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Hydrology_hyd
		list_name = 'hydrology'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class HydrologyHydApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Hydrology_hyd, 'Hydrology')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Hydrology_hyd, 'Hydrology')

	def put(self, project_db, id):
		try:
			SetupProjectDatabase.init(project_db)
			args = get_hyd_args()
			m = Hydrology_hyd.get(Hydrology_hyd.id == id)
			result = save_hyd(m, args)

			if result > 0:
				return 200

			abort(400, message='Unable to update hydrology properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Hydrology properties name must be unique.')
		except Hydrology_hyd.DoesNotExist:
			abort(404, message='Hydrology properties {id} does not exist'.format(id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class HydrologyHydUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Hydrology_hyd)

	def put(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('hydrology_hyd', project_db, True)

			param_dict = {}
			for key in args.keys():
				if args[key] is not None and key != 'selected_ids':
					param_dict[key] = args[key]

			query = Hydrology_hyd.update(param_dict).where(Hydrology_hyd.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update hydrology properties.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class HydrologyHydPostApi(BaseRestModel):
	def post(self, project_db):
		SetupProjectDatabase.init(project_db)
		args = get_hyd_args()

		try:
			e = Hydrology_hyd.get(Hydrology_hyd.name == args['name'])
			abort(400, message='Hydrology name must be unique. A hydrology with this name already exists.')
		except Hydrology_hyd.DoesNotExist:
			try:
				m = Hydrology_hyd()
				result = save_hyd(m, args)

				if result > 0:
					return model_to_dict(m), 201

				abort(400, message='Unable to update hydrology properties {id}.'.format(id=id))
			except IntegrityError as e:
				abort(400, message='Hydrology properties name must be unique.')
			except Exception as ex:
				abort(400, message="Unexpected error {ex}".format(ex=ex))


def get_topo_args():
	parser = reqparse.RequestParser()
	parser.add_argument('id', type=int, required=False, location='json')
	parser.add_argument('name', type=str, required=True, location='json')
	parser.add_argument('slp', type=float, required=True, location='json')
	parser.add_argument('slp_len', type=float, required=True, location='json')
	parser.add_argument('lat_len', type=float, required=True, location='json')
	parser.add_argument('dist_cha', type=float, required=True, location='json')
	parser.add_argument('depos', type=float, required=True, location='json')
	parser.add_argument('type', type=str, required=False, location='json')
	args = parser.parse_args(strict=True)
	return args


class TopographyHydListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Topography_hyd
		list_name = 'topography'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class TopographyHydApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Topography_hyd, 'Topography')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Topography_hyd, 'Topography')

	def put(self, project_db, id):
		try:
			SetupProjectDatabase.init(project_db)
			args = get_topo_args()
			m = Topography_hyd.get(Topography_hyd.id == id)
			m.name = args['name']
			m.slp = args['slp']
			m.slp_len = args['slp_len']
			m.lat_len = args['lat_len']
			m.dist_cha = args['dist_cha']
			m.depos = args['depos']
			#m.type = args['type']

			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update topography properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Topography properties name must be unique.')
		except Topography_hyd.DoesNotExist:
			abort(404, message='Topography properties {id} does not exist'.format(id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class TopographyHydUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Topography_hyd)

	def put(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('topography_hyd', project_db, True)

			param_dict = {}
			for key in args.keys():
				if args[key] is not None and key != 'selected_ids':
					param_dict[key] = args[key]

			query = Topography_hyd.update(param_dict).where(Topography_hyd.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update topography properties.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class TopographyHydPostApi(BaseRestModel):
	def post(self, project_db):
		SetupProjectDatabase.init(project_db)
		args = get_topo_args()

		try:
			e = Topography_hyd.get(Topography_hyd.name == args['name'])
			abort(400, message='Topography name must be unique. A topography with this name already exists.')
		except Topography_hyd.DoesNotExist:
			try:
				m = Topography_hyd()
				m.name = args['name']
				m.slp = args['slp']
				m.slp_len = args['slp_len']
				m.lat_len = args['lat_len']
				m.dist_cha = args['dist_cha']
				m.depos = args['depos']
				m.type = ''

				result = m.save()

				if result > 0:
					return model_to_dict(m), 201

				abort(400, message='Unable to update topography properties {id}.'.format(id=id))
			except IntegrityError as e:
				abort(400, message='Topography properties name must be unique.')
			except Exception as ex:
				abort(400, message="Unexpected error {ex}".format(ex=ex))


def get_fld_args():
	parser = reqparse.RequestParser()
	parser.add_argument('id', type=int, required=False, location='json')
	parser.add_argument('name', type=str, required=True, location='json')
	parser.add_argument('len', type=float, required=True, location='json')
	parser.add_argument('wd', type=float, required=True, location='json')
	parser.add_argument('ang', type=float, required=True, location='json')
	args = parser.parse_args(strict=True)
	return args


class FieldFldListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = Field_fld
		list_name = 'fields'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class FieldFldApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Field_fld, 'Fields')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Field_fld, 'Fields')

	def put(self, project_db, id):
		try:
			SetupProjectDatabase.init(project_db)
			args = get_fld_args()
			m = Field_fld.get(Field_fld.id == id)
			m.name = args['name']
			m.len = args['len']
			m.wd = args['wd']
			m.ang = args['ang']

			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update field properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Field properties name must be unique.')
		except Field_fld.DoesNotExist:
			abort(404, message='Field properties {id} does not exist'.format(id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class FieldFldUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Field_fld)

	def put(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('field_fld', project_db, True)

			param_dict = {}
			for key in args.keys():
				if args[key] is not None and key != 'selected_ids':
					param_dict[key] = args[key]

			query = Field_fld.update(param_dict).where(Field_fld.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update field properties.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class FieldFldPostApi(BaseRestModel):
	def post(self, project_db):
		SetupProjectDatabase.init(project_db)
		args = get_fld_args()

		try:
			e = Field_fld.get(Field_fld.name == args['name'])
			abort(400, message='Field name must be unique. A field with this name already exists.')
		except Field_fld.DoesNotExist:
			try:
				m = Field_fld()
				m.name = args['name']
				m.len = args['len']
				m.wd = args['wd']
				m.ang = args['ang']

				result = m.save()

				if result > 0:
					return model_to_dict(m), 201

				abort(400, message='Unable to update field properties {id}.'.format(id=id))
			except IntegrityError as e:
				abort(400, message='Field properties name must be unique.')
			except Exception as ex:
				abort(400, message="Unexpected error {ex}".format(ex=ex))

