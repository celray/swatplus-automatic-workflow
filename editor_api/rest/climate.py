from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project import base as project_base
from database.project.setup import SetupProjectDatabase
from database.project.config import Project_config
from database.project.climate import Weather_sta_cli, Weather_file, Weather_wgn_cli, Weather_wgn_cli_mon
from database import lib as db_lib
from helpers import utils

import os.path
import sqlite3
import traceback


def get_station_args():
	parser = reqparse.RequestParser()
	parser.add_argument('id', type=int, required=False, location='json')
	parser.add_argument('name', type=str, required=True, location='json')
	parser.add_argument('wgn_id', type=int, required=False, location='json')
	parser.add_argument('wgn', type=int, required=False, location='json')
	parser.add_argument('wgn_name', type=str, required=False, location='json')
	parser.add_argument('pcp', type=str, required=True, location='json')
	parser.add_argument('tmp', type=str, required=True, location='json')
	parser.add_argument('slr', type=str, required=True, location='json')
	parser.add_argument('hmd', type=str, required=True, location='json')
	parser.add_argument('wnd', type=str, required=True, location='json')
	parser.add_argument('wnd_dir', type=str, required=True, location='json')
	parser.add_argument('atmo_dep', type=str, required=True, location='json')
	parser.add_argument('lat', type=float, required=False, location='json')
	parser.add_argument('lon', type=float, required=False, location='json')
	args = parser.parse_args(strict=True)
	return args


def get_wgn_args():
	parser = reqparse.RequestParser()
	parser.add_argument('id', type=int, required=False, location='json')
	parser.add_argument('name', type=str, required=True, location='json')
	parser.add_argument('lat', type=float, required=True, location='json')
	parser.add_argument('lon', type=float, required=True, location='json')
	parser.add_argument('elev', type=float, required=True, location='json')
	parser.add_argument('rain_yrs', type=int, required=True, location='json')
	args = parser.parse_args(strict=True)
	return args


def get_wgn_mon_args():
	parser = reqparse.RequestParser()
	parser.add_argument('id', type=int, required=False, location='json')
	parser.add_argument('weather_wgn_cli_id', type=int, required=False, location='json')
	parser.add_argument('weather_wgn_cli', type=int, required=False, location='json')
	parser.add_argument('month', type=int, required=True, location='json')
	parser.add_argument('tmp_max_ave', type=float, required=True, location='json')
	parser.add_argument('tmp_min_ave', type=float, required=True, location='json')
	parser.add_argument('tmp_max_sd', type=float, required=True, location='json')
	parser.add_argument('tmp_min_sd', type=float, required=True, location='json')
	parser.add_argument('pcp_ave', type=float, required=True, location='json')
	parser.add_argument('pcp_sd', type=float, required=True, location='json')
	parser.add_argument('pcp_skew', type=float, required=True, location='json')
	parser.add_argument('wet_dry', type=float, required=True, location='json')
	parser.add_argument('wet_wet', type=float, required=True, location='json')
	parser.add_argument('pcp_days', type=float, required=True, location='json')
	parser.add_argument('pcp_hhr', type=float, required=True, location='json')
	parser.add_argument('slr_ave', type=float, required=True, location='json')
	parser.add_argument('dew_ave', type=float, required=True, location='json')
	parser.add_argument('wnd_ave', type=float, required=True, location='json')
	args = parser.parse_args(strict=True)
	return args


class WeatherStationSingleApi(Resource):
	def get(self, project_db, id):
		SetupProjectDatabase.init(project_db)
		try:
			m = Weather_sta_cli.get(Weather_sta_cli.id == id)
			d = model_to_dict(m, recurse=False)
			if m.wgn is not None:
				d["wgn_name"] = m.wgn.name
			return d
		except Weather_sta_cli.DoesNotExist:
			abort(404, message='Weather station {id} does not exist'.format(id=id))

	def delete(self, project_db, id):
		SetupProjectDatabase.init(project_db)
		try:
			project_base.db.execute_sql("PRAGMA foreign_keys = ON")
			m = Weather_sta_cli.get(Weather_sta_cli.id == id)
			result = m.delete_instance()

			if result > 0:
				return 204

			abort(400, message='Unable to delete weather station {id}.'.format(id=id))
		except Weather_sta_cli.DoesNotExist:
			abort(404, message='Weather station {id} does not exist'.format(id=id))

	def put(self, project_db, id):
		args = get_station_args()

		SetupProjectDatabase.init(project_db)
		try:
			m = Weather_sta_cli.get(Weather_sta_cli.id == id)
			m.name = args['name']

			if args['wgn_name'] is not None:
				try:
					w = Weather_wgn_cli.get(Weather_wgn_cli.name == args['wgn_name'])
					m.wgn_id = w.id
				except Weather_wgn_cli.DoesNotExist:
					abort(400, message='Invalid weather generator name {name}. Please ensure the value exists in your database.'.format(name=args['wgn_name']))
			else:
				m.wgn_id = args['wgn'] if args['wgn_id'] is None else args['wgn_id']

			m.pcp = args['pcp']
			m.tmp = args['tmp']
			m.slr = args['slr']
			m.hmd = args['hmd']
			m.wnd = args['wnd']
			m.wnd_dir = args['wnd_dir']
			m.atmo_dep = args['atmo_dep']
			m.lat = args['lat']
			m.lon = args['lon']
			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update weather station {id}.'.format(id=id))
		except Weather_sta_cli.DoesNotExist:
			abort(404, message='Weather station {id} does not exist'.format(id=id))


class WeatherStationPostApi(Resource):
	def post(self, project_db):
		args = get_station_args()

		SetupProjectDatabase.init(project_db)

		try:
			e = Weather_sta_cli.get(Weather_sta_cli.name == args['name'])
			abort(400, message='Weather station name must be unique. A station with this name already exists.')
		except Weather_sta_cli.DoesNotExist:
			m = Weather_sta_cli()
			m.name = args['name']

			if args['wgn_name'] is not None:
				try:
					w = Weather_wgn_cli.get(Weather_wgn_cli.name == args['wgn_name'])
					m.wgn_id = w.id
				except Weather_wgn_cli.DoesNotExist:
					abort(404, message='Invalid weather generator name {name}. Please ensure the value exists in your database.'.format(name=args['wgn_name']))
			else:
				m.wgn_id = args['wgn_id']

			m.pcp = args['pcp']
			m.tmp = args['tmp']
			m.slr = args['slr']
			m.hmd = args['hmd']
			m.wnd = args['wnd']
			m.wnd_dir = args['wnd_dir']
			m.atmo_dep = args['atmo_dep']
			m.lat = args['lat']
			m.lon = args['lon']
			result = m.save()

			if result > 0:
				return model_to_dict(m), 201

			abort(400, message='Unable to create weather station.')


class WeatherStationListApi(BaseRestModel):
	def get(self, project_db):
		SetupProjectDatabase.init(project_db)
		args = self.get_table_args()

		try:
			t = Weather_sta_cli

			total = t.select().count()
			sort = self.get_arg(args, 'sort', 'name')
			reverse = self.get_arg(args, 'reverse', 'n')
			page = self.get_arg(args, 'page', 1)
			per_page = self.get_arg(args, 'per_page', 50)
			filter_val = self.get_arg(args, 'filter', None)

			if filter_val is not None:
				wgns = Weather_wgn_cli.select().where(Weather_wgn_cli.name.contains(filter_val))
				s = t.select().where((t.name.contains(filter_val)) | 
						(t.lat.contains(filter_val)) | 
						(t.lon.contains(filter_val)) | 
						(t.pcp.contains(filter_val)) | 
						(t.tmp.contains(filter_val)) | 
						(t.slr.contains(filter_val)) | 
						(t.hmd.contains(filter_val)) | 
						(t.wnd.contains(filter_val)) | 
						(t.wnd_dir.contains(filter_val)) | 
						(t.atmo_dep.contains(filter_val)) |
						(t.wgn.in_(wgns)))
			else:
				s = t.select()

			matches = s.count()

			sort_val = SQL(sort)
			if reverse == 'y':
				sort_val = SQL(sort).desc()

			m = s.order_by(sort_val).paginate(int(page), int(per_page))

			return {
				'total': total,
				'matches': matches,
				'items': [model_to_dict(v, recurse=True, max_depth=1) for v in m]
			}
		except Project_config.DoesNotExist:
			abort(400, message='Error selecting weather stations.')


class WeatherStationDirectoryApi(Resource):
	def get(self, project_db):
		SetupProjectDatabase.init(project_db)

		try:
			config = Project_config.get()
			return {
				'weather_data_dir': utils.full_path(project_db, config.weather_data_dir)
			}
		except Project_config.DoesNotExist:
			abort(400, message='Could not retrieve project configuration data.')

	def put(self, project_db):
		parser = reqparse.RequestParser()
		parser.add_argument('weather_data_dir', type=str, required=True, location='json')
		args = parser.parse_args(strict=True)

		SetupProjectDatabase.init(project_db)
		try:
			m = Project_config.get()
			m.weather_data_dir = utils.rel_path(project_db, args['weather_data_dir'])
			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update project configuration.')
		except Project_config.DoesNotExist:
			abort(404, message='Could not retrieve project configuration data.')


class WeatherFileAutoCompleteApi(Resource):
	def get(self, project_db, type, partial_name):
		SetupProjectDatabase.init(project_db)

		m = Weather_file.select().where((Weather_file.type == type) & (Weather_file.filename.startswith(partial_name)))

		return [v.filename for v in m]


class WgnSingleApi(Resource):
	def get(self, project_db, id):
		SetupProjectDatabase.init(project_db)
		try:
			m = Weather_wgn_cli.get(Weather_wgn_cli.id == id)
			return model_to_dict(m, backrefs=True, max_depth=1)
		except Weather_wgn_cli.DoesNotExist:
			abort(404, message='Weather generator {id} does not exist'.format(id=id))

	def delete(self, project_db, id):
		SetupProjectDatabase.init(project_db)
		try:
			project_base.db.execute_sql("PRAGMA foreign_keys = ON")
			m = Weather_wgn_cli.get(Weather_wgn_cli.id == id)
			result = m.delete_instance()

			if result > 0:
				return 204

			abort(400, message='Unable to delete weather generator {id}.'.format(id=id))
		except Weather_wgn_cli.DoesNotExist:
			abort(404, message='Weather generator {id} does not exist'.format(id=id))

	def put(self, project_db, id):
		args = get_wgn_args()

		SetupProjectDatabase.init(project_db)
		try:
			m = Weather_wgn_cli.get(Weather_wgn_cli.id == id)
			m.name = args['name']
			m.lat = args['lat']
			m.lon = args['lon']
			m.elev = args['elev']
			m.rain_yrs = args['rain_yrs']
			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update weather generator {id}.'.format(id=id))
		except Weather_wgn_cli.DoesNotExist:
			abort(404, message='Weather generator {id} does not exist'.format(id=id))


class WgnPostApi(Resource):
	def post(self, project_db):
		args = get_wgn_args()

		SetupProjectDatabase.init(project_db)

		try:
			e = Weather_wgn_cli.get(Weather_wgn_cli.name == args['name'])
			abort(400, message='Weather generator name must be unique. A generator with this name already exists.')
		except Weather_wgn_cli.DoesNotExist:
			m = Weather_wgn_cli()
			m.name = args['name']
			m.lat = args['lat']
			m.lon = args['lon']
			m.elev = args['elev']
			m.rain_yrs = args['rain_yrs']
			result = m.save()

			if result > 0:
				return model_to_dict(m), 201

			abort(400, message='Unable to create weather generator.')


class WgnListApi(BaseRestModel):
	def get(self, project_db):
		SetupProjectDatabase.init(project_db)
		args = self.get_table_args()

		try:
			t = Weather_wgn_cli

			total = t.select().count()
			sort = self.get_arg(args, 'sort', 'name')
			reverse = self.get_arg(args, 'reverse', 'n')
			page = self.get_arg(args, 'page', 1)
			per_page = self.get_arg(args, 'per_page', 50)
			filter_val = self.get_arg(args, 'filter', None)

			if filter_val is not None:
				s = t.select().where((t.name.contains(filter_val)) | 
						(t.lat.contains(filter_val)) | 
						(t.lon.contains(filter_val)) | 
						(t.elev.contains(filter_val)) | 
						(t.rain_yrs.contains(filter_val)))
			else:
				s = t.select()

			matches = s.count()

			sort_val = SQL(sort)
			if reverse == 'y':
				sort_val = SQL(sort).desc()

			m = s.order_by(sort_val).paginate(int(page), int(per_page))

			return {
				'total': total,
				'matches': matches,
				'items': [model_to_dict(v, backrefs=True, max_depth=1) for v in m]
			}
		except Project_config.DoesNotExist:
			abort(400, message='Error selecting wgns.')


class WgnTablesAutoCompleteApi(Resource):
	def get(self, wgn_db, partial_name):
		conn = sqlite3.connect(wgn_db)
		conn.row_factory = sqlite3.Row

		m = db_lib.get_matching_table_names_wgn(conn, partial_name)
		matches = [v[0] for v in m]

		nm = db_lib.get_table_names(conn)
		non_matches = [v[0] for v in nm if v[0] not in matches and '_mon' not in v[0]]

		return matches + non_matches


class WgnSaveImportDbApi(Resource):
	def get(self, project_db):
		SetupProjectDatabase.init(project_db)
		config = Project_config.get()
		wgn_db = None if config.wgn_db is None or config.wgn_db == '' else utils.full_path(project_db, config.wgn_db)
		return {
			'wgn_db': wgn_db,
			'wgn_table_name': config.wgn_table_name
		}

	def put(self, project_db):
		parser = reqparse.RequestParser()
		parser.add_argument('wgn_db', type=str, required=False, location='json')
		parser.add_argument('wgn_table_name', type=str, required=False, location='json')
		args = parser.parse_args(strict=False)

		if 'wgn_db' not in args or args['wgn_db'] is None or args['wgn_db'] == '':
			return 200

		SetupProjectDatabase.init(project_db)
		try:
			conn = sqlite3.connect(args['wgn_db'])
			conn.row_factory = sqlite3.Row

			monthly_table = "{}_mon".format(args['wgn_table_name'])

			if not db_lib.exists_table(conn, args['wgn_table_name']):
				abort(400, message="Table {table} does not exist in {file}.".format(table=args['wgn_table_name'], file=args['wgn_db']))

			if not db_lib.exists_table(conn, monthly_table):
				abort(400, message="Table {table} does not exist in {file}.".format(table=monthly_table, file=args['wgn_db']))
				
			default_wgn_db = 'C:/SWAT/SWATPlus/Databases/swatplus_wgn.sqlite'
			wgn_db_path = default_wgn_db
			
			if not utils.are_paths_equal(default_wgn_db, args['wgn_db']):
				wgn_db_path = utils.rel_path(project_db, args['wgn_db'])

			m = Project_config.get()
			m.wgn_db = wgn_db_path
			m.wgn_table_name = args['wgn_table_name']
			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update project configuration.')
		except Project_config.DoesNotExist:
			abort(404, message='Could not retrieve project configuration data.')


class WgnMonthApi(Resource):
	def get(self, project_db, id):
		SetupProjectDatabase.init(project_db)
		try:
			m = Weather_wgn_cli_mon.get(Weather_wgn_cli_mon.id == id)
			return model_to_dict(m, recurse=False)
		except Weather_wgn_cli_mon.DoesNotExist:
			abort(404, message='Weather generator monthly value {id} does not exist'.format(id=id))

	def delete(self, project_db, id):
		SetupProjectDatabase.init(project_db)
		try:
			m = Weather_wgn_cli_mon.get(Weather_wgn_cli_mon.id == id)
			result = m.delete_instance()

			if result > 0:
				return 204

			abort(400, message='Unable to delete weather generator monthly value {id}.'.format(id=id))
		except Weather_wgn_cli_mon.DoesNotExist:
			abort(404, message='Weather generator monthly value {id} does not exist'.format(id=id))

	def put(self, project_db, id):
		args = get_wgn_mon_args()

		SetupProjectDatabase.init(project_db)
		try:
			m = Weather_wgn_cli_mon.get(Weather_wgn_cli_mon.id == id)
			m.month = args['month']
			m.tmp_max_ave = args['tmp_max_ave']
			m.tmp_min_ave = args['tmp_min_ave']
			m.tmp_max_sd = args['tmp_max_sd']
			m.tmp_min_sd = args['tmp_min_sd']
			m.pcp_ave = args['pcp_ave']
			m.pcp_sd = args['pcp_sd']
			m.pcp_skew = args['pcp_skew']
			m.wet_dry = args['wet_dry']
			m.wet_wet = args['wet_wet']
			m.pcp_days = args['pcp_days']
			m.pcp_hhr = args['pcp_hhr']
			m.slr_ave = args['slr_ave']
			m.dew_ave = args['dew_ave']
			m.wnd_ave = args['wnd_ave']
			result = m.save()

			if result > 0:
				return 200

			abort(400, message='Unable to update weather generator monthly value {id}.'.format(id=id))
		except Weather_wgn_cli.DoesNotExist:
			abort(404, message='Weather generator monthly value {id} does not exist'.format(id=id))


class WgnMonthListApi(Resource):
	def get(self, project_db, wgn_id):
		SetupProjectDatabase.init(project_db)
		m = Weather_wgn_cli_mon.select(Weather_wgn_cli_mon.weather_wgn_cli_id == wgn_id).order_by(Weather_wgn_cli_mon.month)
		return [model_to_dict(v, recurse=False) for v in m]

	def post(self, project_db, wgn_id):
		args = get_wgn_mon_args()

		SetupProjectDatabase.init(project_db)

		try:
			e = Weather_wgn_cli_mon.get((Weather_wgn_cli_mon.weather_wgn_cli_id == wgn_id) & (Weather_wgn_cli_mon.month == args['month']))
			abort(400, message='Weather generator already has data for month {month}.'.format(month=args['month']))
		except Weather_wgn_cli_mon.DoesNotExist:
			m = Weather_wgn_cli_mon()
			m.weather_wgn_cli = wgn_id
			m.month = args['month']
			m.tmp_max_ave = args['tmp_max_ave']
			m.tmp_min_ave = args['tmp_min_ave']
			m.tmp_max_sd = args['tmp_max_sd']
			m.tmp_min_sd = args['tmp_min_sd']
			m.pcp_ave = args['pcp_ave']
			m.pcp_sd = args['pcp_sd']
			m.pcp_skew = args['pcp_skew']
			m.wet_dry = args['wet_dry']
			m.wet_wet = args['wet_wet']
			m.pcp_days = args['pcp_days']
			m.pcp_hhr = args['pcp_hhr']
			m.slr_ave = args['slr_ave']
			m.dew_ave = args['dew_ave']
			m.wnd_ave = args['wnd_ave']
			result = m.save()

			if result > 0:
				return model_to_dict(m, recurse=False), 201

			abort(400, message='Unable to create weather generator monthly value.')
