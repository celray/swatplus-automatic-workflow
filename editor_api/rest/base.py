from abc import ABCMeta, abstractmethod
from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *
from helpers import utils, table_mapper
from database.project import base as project_base, climate
from database.project.setup import SetupProjectDatabase
from database.project.config import Project_config

from database.datasets.setup import SetupDatasetsDatabase
from database.vardefs import Var_range
import os.path
import ast
from pprint import pprint


class BaseRestModel(Resource):
	__metaclass__ = ABCMeta
	__invalid_name_msg = 'Invalid name {name}. Please ensure the value exists in your database.'

	def base_get(self, project_db, id, table, description, back_refs=False, max_depth=1):
		SetupProjectDatabase.init(project_db)
		try:
			m = table.get(table.id == id)
			if back_refs:
				d = model_to_dict(m, backrefs=True, max_depth=max_depth)
				self.get_obj_name(d)
				return d
			else:
				return model_to_dict(m, recurse=False)
		except table.DoesNotExist:
			abort(404, message='{description} {id} does not exist'.format(description=description, id=id))

	def get_obj_name(self, d):
		if 'con_outs' in d:
			for o in d['con_outs']:
				c_table = table_mapper.obj_typs.get(o['obj_typ'], None)
				o['obj_name'] = c_table.get(c_table.id == o['obj_id']).name
		if 'elements' in d:
			for o in d['elements']:
				c_table = table_mapper.obj_typs.get(o['obj_typ'], None)
				key = 'obj_id' if 'obj_id' in o else 'obj_typ_no'
				o['obj_name'] = c_table.get(c_table.id == o[key]).name
		if 'obj_typ' in d and ('obj_id' in d or 'obj_typ_no' in d):
			c_table = table_mapper.obj_typs.get(d['obj_typ'], None)
			key = 'obj_id' if 'obj_id' in d else 'obj_typ_no'
			d['obj_name'] = c_table.get(c_table.id == d[key]).name

	def base_get_datasets_name(self, datasets_db, name, table, description, back_refs=False):
		SetupDatasetsDatabase.init(datasets_db)
		try:
			m = table.get(table.name == name)
			if back_refs:
				return model_to_dict(m, backrefs=True, max_depth=1)
			else:
				return model_to_dict(m, recurse=False)
		except table.DoesNotExist:
			abort(404, message='{description} {name} does not exist'.format(description=description, name=name))

	def base_delete(self, project_db, id, table, description):
		SetupProjectDatabase.init(project_db)
		try:
			project_base.db.execute_sql("PRAGMA foreign_keys = ON")
			m = table.get(table.id == id)
			result = m.delete_instance()

			if result > 0:
				return 204

			abort(400, message='Unable to delete {description} {id}.'.format(description=description, id=id))
		except table.DoesNotExist:
			abort(404, message='{description} {id} does not exist'.format(description=description, id=id))

	def base_paged_list(self, project_db, sort, reverse, page, items_per_page, table, list_name, back_refs=False):
		SetupProjectDatabase.init(project_db)
		total = table.select().count()

		sort_val = SQL('[{}]'.format(sort))
		if reverse == 'true':
			sort_val = SQL('[{}]'.format(sort)).desc()

		m = table.select().order_by(sort_val).paginate(int(page), int(items_per_page))

		if back_refs:
			ml = [model_to_dict(v, backrefs=True, max_depth=1) for v in m]
			for d in ml:
				self.get_obj_name(d)
		else:
			ml = [model_to_dict(v, recurse=False) for v in m]

		return {'total': total, list_name: ml}

	def base_list(self, project_db, table):
		SetupProjectDatabase.init(project_db)
		m = table.select()
		return [model_to_dict(v, recurse=False) for v in m]

	def base_put(self, project_db, id, table, item_description):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args_reflect(table, project_db)

			result = self.save_args(table, args, id=id)

			if result > 0:
				return 201

			abort(400, message='Unable to update {item} {id}.'.format(item=item_description.lower(), id=id))
		except IntegrityError as e:
			abort(400, message='{item} name must be unique. '.format(item=item_description) + str(e))
		except table.DoesNotExist:
			abort(404, message='{item} {id} does not exist'.format(item=item_description, id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))

	def base_post(self, project_db, table, item_description, extra_args=[]):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args_reflect(table, project_db, extra_args=extra_args)

			result = self.save_args(table, args, is_new=True, extra_args=extra_args)

			if result > 0:
				return {'id': result }, 201

			abort(400, message='Unable to create {item}.'.format(item=item_description.lower()))
		except IntegrityError as e:
			abort(400, message='{item} name must be unique. {ex}'.format(item=item_description, ex=str(e)))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))

	def base_put_many(self, project_db, table, item_description):
		try:
			table_name = table._meta.name.lower()
			SetupProjectDatabase.init(project_db)
			args = self.get_args(table_name, project_db, True)

			param_dict = {}
			for key in args.keys():
				if args[key] is not None and key != 'selected_ids':
					param_dict[key] = args[key]

			query = table.update(param_dict).where(table.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update {item}.'.format(item=item_description.lower()))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))

	def get_id_from_name(self, table, value):
		if value is None or value == '':
			return None
			
		i = table.get(table.name == value)
		return i.id

	def base_name_id_list(self, project_db, table):
		SetupProjectDatabase.init(project_db)
		m = table.select(table.id, table.name).order_by(table.name)
		return [{'id': v.id, 'name': v.name} for v in m]
	
	def get_args(self, table_name, project_db, get_selected_ids=False, extra_args=[]):
		parser = reqparse.RequestParser()
		
		if get_selected_ids:
			parser.add_argument('selected_ids', type=int, action='append', required=False, location='json')
		else:
			parser.add_argument('id', type=int, required=False, location='json')
			parser.add_argument('name', type=str, required=False, location='json')
			parser.add_argument('description', type=str, required=False, location='json')

		for extra in extra_args:
			parser.add_argument(extra['name'], type=extra['type'], required=False, location='json')
		
		try:
			c = Project_config.get()
			
			datasets_db = c.reference_db
			if not os.path.exists(c.reference_db):
				datasets_db = os.path.normpath(os.path.join(os.path.dirname(project_db), c.reference_db))
			
			SetupDatasetsDatabase.init(datasets_db)
			m = Var_range.select().where(Var_range.table == table_name)
			
			types = {
				'float': float,
				'int': int,
				'text': str,
				'string': str,
				'select': str,
				'lookup': str
			}
			
			for v in m:
				parser.add_argument(v.variable, type=types.get(v.type, str), required=False, location='json')
		except Project_config.DoesNotExist:
			abort(404, message="Could not retrieve project configuration data.")
		
		args = parser.parse_args(strict=False)
		return args

	def get_args_reflect(self, table, project_db, get_selected_ids=False, extra_args=[]):
		parser = reqparse.RequestParser()
		
		if get_selected_ids:
			parser.add_argument('selected_ids', type=int, action='append', required=False, location='json')

		for extra in extra_args:
			parser.add_argument(extra['name'], type=extra['type'], required=False, location='json')

		type_map = {
			DoubleField: float,
			IntegerField: int,
			AutoField: int,
			TextField: str,
			CharField: str,
			ForeignKeyField: int,
			BooleanField: bool
		}
		
		for field in table._meta.sorted_fields:
			parser.add_argument(field.column_name, type=type_map.get(type(field), str), required=False, location='json')
		
		args = parser.parse_args(strict=False)
		return args
	
	def save_args(self, table, args, id=0, is_new=False, lookup_fields=[], extra_args=[]):
		params = {}
		for field in table._meta.sorted_fields:
			if field.column_name in args or field.name in args:
				if field.name in lookup_fields:
					d = ast.literal_eval(args[field.name])
					params[field.name] = int(d['id'])
				elif field.column_name in lookup_fields:
					d = ast.literal_eval(args[field.column_name])
					params[field.column_name] = int(d['id'])
				else:
					params[field.column_name] = args[field.column_name]

		for extra in extra_args:
			params[extra['name']] = args[extra['name']]

		if is_new:
			query = table.insert(params)
		else:
			query = table.update(params).where(table.id == id)
		
		return query.execute()

	def get_con_args(self, prop_name):
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
		parser.add_argument(prop_name, type=int, required=False, location='json')
		parser.add_argument('{prop}_name'.format(prop=prop_name), type=str, required=False, location='json')
		args = parser.parse_args(strict=True)
		return args
	
	def get_con_out_args(self, con_table):
		parser = reqparse.RequestParser()
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('order', type=int, required=True, location='json')
		parser.add_argument('obj_typ', type=str, required=True, location='json')
		parser.add_argument('obj_id', type=int, required=True, location='json')
		parser.add_argument('hyd_typ', type=str, required=True, location='json')
		parser.add_argument('frac', type=float, required=True, location='json')
		parser.add_argument('{con}_id'.format(con=con_table), type=int, required=False, location='json')
		args = parser.parse_args(strict=True)
		return args

	def get_con_map(self, project_db, table):
		SetupProjectDatabase.init(project_db)
		t = table
		limit = 500

		bounds = t.select(fn.Max(t.lat).alias("max_lat"),
						  fn.Min(t.lat).alias("min_lat"),
						  fn.Max(t.lon).alias("max_lon"),
						  fn.Min(t.lon).alias("min_lon")).get()

		m = t.select().limit(limit)
		features = []
		for v in m:
			feature = {
				"geometry": {
					"type": "Point",
					"coordinates": [v.lon, v.lat]
				},
				"type": "Feature",
				"properties": {
					"name": v.name,
					"area": v.area,
					"lat": v.lat,
					"lon": v.lon,
					"elevation": v.elev
				},
				"id": v.id
			}
			features.append(feature)

		return {
			"bounds": {
				"max_lat": bounds.max_lat,
				"max_lon": bounds.max_lon,
				"min_lat": bounds.min_lat,
				"min_lon": bounds.min_lon
			},
			"geojson": {
				"type": "FeatureCollection",
				"features": features
			},
			"display": {
				"limit": limit,
				"total": t.select().count()
			}
		}

	def put_con(self, project_db, id, prop_name, con_table, prop_table):
		args = self.get_con_args(prop_name)
		try:
			SetupProjectDatabase.init(project_db)

			params = {
				'name': args['name'],
				'area': args['area'],
				'lat': args['lat'],
				'lon': args['lon'],
				'elev': args['elev'],
			}

			params['{}_id'.format(prop_name)] = self.get_id_from_name(prop_table, args['{}_name'.format(prop_name)])

			if args['wst_name'] is not None:
				params['wst_id'] = self.get_id_from_name(climate.Weather_sta_cli, args['wst_name'])

			result = con_table.update(params).where(con_table.id == id).execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update Hru {id}.'.format(id=id))
		except IntegrityError:
			abort(400, message='Name must be unique.')
		except con_table.DoesNotExist:
			abort(404, message='Object {id} does not exist'.format(id=id))
		except prop_table.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['{}_name'.format(prop_name)]))
		except climate.Weather_sta_cli.DoesNotExist:
			abort(400, message=self.__invalid_name_msg.format(name=args['wst_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))

	def post_con(self, project_db, prop_name, con_table, prop_table):
		args = self.get_con_args(prop_name)
		SetupProjectDatabase.init(project_db)

		try:
			e = con_table.get(con_table.name == args['name'])
			abort(400, message='Name must be unique. Object with this name already exists.')
		except con_table.DoesNotExist:
			try:
				params = {
					'name': args['name'],
					'area': args['area'],
					'lat': args['lat'],
					'lon': args['lon'],
					'elev': args['elev'],
					'ovfl': 0,
					'rule': 0
				}

				params['{}_id'.format(prop_name)] = self.get_id_from_name(prop_table, args['{}_name'.format(prop_name)])

				if args['wst_name'] is not None:
					params['wst_id'] = self.get_id_from_name(climate.Weather_sta_cli, args['wst_name'])

				result = con_table.insert(params).execute()

				if result > 0:
					return 201

				abort(400, message='Unable to create object.')
			except IntegrityError:
				abort(400, message='Name must be unique.')
			except prop_table.DoesNotExist:
				abort(400, message=self.__invalid_name_msg.format(name=args['{}_name'.format(prop_name)]))
			except climate.Weather_sta_cli.DoesNotExist:
				abort(400, message=self.__invalid_name_msg.format(name=args['wst_name']))
			except Exception as ex:
				abort(400, message="Unexpected error {ex}".format(ex=ex))

	def put_con_out(self, project_db, id, prop_name, con_out_table):
		try:
			args = self.get_con_out_args(prop_name)
			SetupProjectDatabase.init(project_db)

			params = {
				'order': args['order'],
				'obj_typ': args['obj_typ'],
				'obj_id': args['obj_id'],
				'hyd_typ': args['hyd_typ'],
				'frac': args['frac']
			}

			result = con_out_table.update(params).where(con_out_table.id == id).execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update outflow {id}.'.format(id=id))
		except con_out_table.DoesNotExist:
			abort(404, message='Outflow {id} does not exist'.format(id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))

	def post_con_out(self, project_db, prop_name, con_out_table):
		args = self.get_con_out_args(prop_name)
		SetupProjectDatabase.init(project_db)

		try:
			params = {
				'order': args['order'],
				'obj_typ': args['obj_typ'],
				'obj_id': args['obj_id'],
				'hyd_typ': args['hyd_typ'],
				'frac': args['frac']
			}
			params['{}_id'.format(prop_name)] = args['{}_id'.format(prop_name)]

			result = con_out_table.insert(params).execute()

			if result > 0:
				return 201

			abort(400, message='Unable to create outflow.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))
