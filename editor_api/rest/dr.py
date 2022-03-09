from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project.setup import SetupProjectDatabase
from database.project.connect import Delratio_con, Delratio_con_out
from database.project.dr import Delratio_del, Dr_om_del, Dr_pest_del, Dr_path_del, Dr_hmet_del, Dr_salt_del
from database.project.climate import Weather_sta_cli

invalid_name_msg = 'Invalid name {name}. Please ensure the value exists in your database.'

class DelratioConApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Delratio_con, 'Delratio', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Delratio_con, 'Delratio', 'dlr', Delratio_del)

	def put(self, project_db, id):
		return self.put_con(project_db, id, 'dlr', Delratio_con, Delratio_del)


class DelratioConPostApi(BaseRestModel):
	def post(self, project_db):
		return self.post_con(project_db, 'dlr', Delratio_con, Delratio_del)


class DelratioConListApi(BaseRestModel):
	def get(self, project_db):
		table = Delratio_con
		prop_table = Delratio_del
		filter_cols = [table.name, table.wst, prop_table.om, prop_table.pest, prop_table.path, prop_table.hmet, prop_table.salt]
		table_lookups = {
			table.wst: Weather_sta_cli
		}
		props_lookups = {
			prop_table.om: Dr_om_del,
			prop_table.pest: Dr_pest_del,
			prop_table.path: Dr_path_del,
			prop_table.hmet: Dr_hmet_del,
			prop_table.salt: Dr_salt_del
		}

		items = self.base_connect_paged_items(project_db, table, prop_table, filter_cols, table_lookups, props_lookups)
		ml = []
		for v in items['model']:
			d = self.base_get_con_item_dict(v)
			d['om'] = self.base_get_prop_dict(v.dlr.om)
			d['pest'] = self.base_get_prop_dict(v.dlr.pest)
			d['path'] = self.base_get_prop_dict(v.dlr.path)
			d['hmet'] = self.base_get_prop_dict(v.dlr.hmet)
			d['salt'] = self.base_get_prop_dict(v.dlr.salt)
			ml.append(d)
		
		return {
			'total': items['total'],
			'matches': items['matches'],
			'items': ml
		}


class DelratioConMapApi(BaseRestModel):
	def get(self, project_db):
		return self.get_con_map(project_db, Delratio_con)


class DelratioConOutApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Delratio_con_out, 'Outflow', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Delratio_con_out, 'Outflow')

	def put(self, project_db, id):
		return self.put_con_out(project_db, id, 'delratio_con', Delratio_con_out)


class DelratioConOutPostApi(BaseRestModel):
	def post(self, project_db):
		return self.post_con_out(project_db, 'delratio_con', Delratio_con_out)


def get_dr_args(get_selected_ids=False):
	parser = reqparse.RequestParser()

	if get_selected_ids:
		parser.add_argument('selected_ids', type=int, action='append', required=False, location='json')
		parser.add_argument('elev', type=float, required=False, location='json')
		parser.add_argument('wst_name', type=str, required=False, location='json')
	else:
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('name', type=str, required=True, location='json')

	parser.add_argument('om_name', type=str, required=False, location='json')
	parser.add_argument('pest_name', type=str, required=False, location='json')
	parser.add_argument('path_name', type=str, required=False, location='json')
	parser.add_argument('hmet_name', type=str, required=False, location='json')
	parser.add_argument('salt_name', type=str, required=False, location='json')
	args = parser.parse_args(strict=False)
	return args


class DelratioDelListApi(BaseRestModel):
	def get(self, project_db):
		table = Delratio_del
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols, True)


class DelratioDelApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Delratio_del, 'Delratio', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Delratio_del, 'Delratio')

	def put(self, project_db, id):
		args = get_dr_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Delratio_del.get(Delratio_del.id == id)
			m.name = args['name']
			m.om_id = self.get_id_from_name(Dr_om_del, args['om_name'])
			m.pest_id = self.get_id_from_name(Dr_pest_del, args['pest_name'])
			m.path_id = self.get_id_from_name(Dr_path_del, args['path_name'])
			m.hmet_id = self.get_id_from_name(Dr_hmet_del, args['hmet_name'])
			m.salt_id = self.get_id_from_name(Dr_salt_del, args['salt_name'])

			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update delratio properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Delratio properties name must be unique.')
		except Delratio_del.DoesNotExist:
			abort(404, message='Delratio properties {id} does not exist'.format(id=id))
		except Dr_om_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['om_name']))
		except Dr_pest_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['pest_name']))
		except Dr_path_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['path_name']))
		except Dr_hmet_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hmet_name']))
		except Dr_salt_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['salt_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class DelratioDelUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Delratio_del)

	def put(self, project_db):
		SetupProjectDatabase.init(project_db)
		args = get_dr_args(True)
		try:
			param_dict = {}

			if args['om_name'] is not None:
				param_dict['om_id'] = self.get_id_from_name(Dr_om_del, args['om_name'])
			if args['pest_name'] is not None:
				param_dict['pest_id'] = self.get_id_from_name(Dr_pest_del, args['pest_name'])
			if args['path_name'] is not None:
				param_dict['path_id'] = self.get_id_from_name(Dr_path_del, args['path_name'])
			if args['hmet_name'] is not None:
				param_dict['hmet_id'] = self.get_id_from_name(Dr_hmet_del, args['hmet_name'])
			if args['salt_name'] is not None:
				param_dict['salt_id'] = self.get_id_from_name(Dr_salt_del, args['salt_name'])

			con_table = Delratio_con
			con_prop_field = Delratio_con.dlr_id
			prop_table = Delratio_del

			result = self.base_put_many_con(args, param_dict, con_table, con_prop_field, prop_table)
			if result > 0:
				return 200

			abort(400, message='Unable to update delratio properties.')
		except Dr_om_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['om_name']))
		except Dr_pest_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['pest_name']))
		except Dr_path_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['path_name']))
		except Dr_hmet_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hmet_name']))
		except Dr_salt_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['salt_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class DelratioDelPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_dr_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Delratio_del()
			m.name = args['name']
			m.om_id = self.get_id_from_name(Dr_om_del, args['om_name'])
			m.pest_id = self.get_id_from_name(Dr_pest_del, args['pest_name'])
			m.path_id = self.get_id_from_name(Dr_path_del, args['path_name'])
			m.hmet_id = self.get_id_from_name(Dr_hmet_del, args['hmet_name'])
			m.salt_id = self.get_id_from_name(Dr_salt_del, args['salt_name'])

			result = m.save()

			if result > 0:
				return {'id': m.id }, 200

			abort(400, message='Unable to update delratio properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Delratio properties name must be unique.')
		except Dr_om_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['om_name']))
		except Dr_pest_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['pest_name']))
		except Dr_path_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['path_name']))
		except Dr_hmet_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['hmet_name']))
		except Dr_salt_del.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['salt_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class DelratioOMListApi(BaseRestModel):
	def get(self, project_db):
		table = Dr_om_del
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols)


def save_dr_om_del(m, args):
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


class DelratioOMApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Dr_om_del, 'Delratio')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Dr_om_del, 'Delratio')

	def put(self, project_db, id):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('dr_om_del', project_db)

			m = Dr_om_del.get(Dr_om_del.id == id)
			result = save_dr_om_del(m, args)

			if result > 0:
				return 200

			abort(400, message='Unable to update om delratio properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Delratio om properties name must be unique.')
		except Dr_om_del.DoesNotExist:
			abort(404, message='Delratio om properties {id} does not exist'.format(id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class DelratioOMUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Dr_om_del)

	def put(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('dr_om_del', project_db, True)

			param_dict = {}
			for key in args.keys():
				if args[key] is not None and key != 'selected_ids':
					param_dict[key] = args[key]

			query = Dr_om_del.update(param_dict).where(Dr_om_del.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update delratio om properties.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class DelratioOMPostApi(BaseRestModel):
	def post(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('dr_om_del', project_db)

			m = Dr_om_del()
			result = save_dr_om_del(m, args)

			if result > 0:
				return model_to_dict(m), 201

			abort(400, message='Unable to update delratio om properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Delratio om properties name must be unique.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))
