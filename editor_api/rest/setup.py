from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from playhouse.migrate import *

from database.project.config import Project_config
from database.project.setup import SetupProjectDatabase
from database.datasets.setup import SetupDatasetsDatabase
from database.datasets.definitions import Version
from database import lib

from database.project import gis, climate, connect, simulation, regions
from actions import import_gis, import_gis_legacy

from helpers import utils
from datetime import datetime

import os.path


def check_config(project_db):
	conn = lib.open_db(project_db)
	if lib.exists_table(conn, 'project_config'):
		config_cols = lib.get_column_names(conn, 'project_config')
		col_names = [v['name'] for v in config_cols]
		if 'output_last_imported' not in col_names:
			migrator = SqliteMigrator(SqliteDatabase(project_db))
			migrate(
				migrator.add_column('project_config', 'output_last_imported', DateTimeField(null=True)),
				migrator.add_column('project_config', 'imported_gis', BooleanField(default=False)),
				migrator.add_column('project_config', 'is_lte', BooleanField(default=False)),
			)

			if lib.exists_table(conn, 'plants_plt'):
				lib.delete_table(project_db, 'plants_plt')


def get_model_to_dict_dates(m, project_db):
	d = model_to_dict(m)
	d["reference_db"] = utils.full_path(project_db, m.reference_db)
	d["wgn_db"] = utils.full_path(project_db, m.wgn_db)
	d["weather_data_dir"] = utils.full_path(project_db, m.weather_data_dir)
	d["input_files_dir"] = utils.full_path(project_db, m.input_files_dir)
	d["input_files_last_written"] = utils.json_encode_datetime(m.input_files_last_written)
	d["swat_last_run"] = utils.json_encode_datetime(m.swat_last_run)
	d["output_last_imported"] = utils.json_encode_datetime(m.output_last_imported)
	return d


class SetupApi(Resource):
	def put(self):
		parser = reqparse.RequestParser()
		parser.add_argument('project_name', type=str, required=True, location='json')
		parser.add_argument('project_db', type=str, required=True, location='json')
		parser.add_argument('reference_db', type=str, required=True, location='json')
		args = parser.parse_args(strict=False)
		
		project_db = utils.sanitize(args['project_db'])
		reference_db = utils.sanitize(args['reference_db'])
		
		SetupProjectDatabase.init(project_db)
		try:
			m = Project_config.get()
			
			m.reference_db = utils.rel_path(project_db, args['reference_db'])
			m.project_name = args['project_name']
			result = m.save()
			
			if result > 0:
				return 200
			
			abort(400, message="Unable to update project configuration table.")
		except Project_config.DoesNotExist:
			abort(404, message="Could not retrieve project configuration data.")


class ConfigApi(Resource):
	def get(self, project_db):
		check_config(project_db)

		SetupProjectDatabase.init(project_db)
		try:
			m = Project_config.get()
			return get_model_to_dict_dates(m, project_db)
		except Project_config.DoesNotExist:
			abort(404, message="Could not retrieve project configuration data.")


class CheckImportConfigApi(Resource):
	def get(self, project_db):
		check_config(project_db)

		SetupProjectDatabase.init(project_db)
		try:
			m = Project_config.get()
			d = get_model_to_dict_dates(m, project_db)

			if not import_gis.is_supported_version(m.gis_version) and not import_gis_legacy.is_supported_version(m.gis_version):
				abort(400, message="This version of SWAT+ Editor does not support QSWAT+ {uv}.".format(uv=m.gis_version))

			d["has_ps"] = gis.Gis_points.select().where((gis.Gis_points.ptype == 'P') | (gis.Gis_points.ptype == 'I')).count() > 0
			d["has_res"] = gis.Gis_water.select().count() > 0

			return d
		except Project_config.DoesNotExist:
			abort(404, message="Could not retrieve project configuration data.")


class InputFilesSettingsApi(Resource):
	def get(self, project_db):
		SetupProjectDatabase.init(project_db)
		try:
			m = Project_config.get()
			return {
				"has_weather": climate.Weather_sta_cli.select().count() > 0 and climate.Weather_wgn_cli.select().count() > 0,
				"input_files_dir": utils.full_path(project_db, m.input_files_dir),
				"input_files_last_written": utils.json_encode_datetime(m.input_files_last_written),
				"swat_last_run": utils.json_encode_datetime(m.swat_last_run)
			}
		except Project_config.DoesNotExist:
			abort(404, message="Could not retrieve project configuration data.")

	def put(self, project_db):
		parser = reqparse.RequestParser()
		parser.add_argument('input_files_dir', type=str, required=False, location='json')
		parser.add_argument('input_files_last_written', type=str, required=False, location='json')
		args = parser.parse_args(strict=True)

		SetupProjectDatabase.init(project_db)
		try:
			m = Project_config.get()
			
			m.input_files_dir = utils.rel_path(project_db, args['input_files_dir'])
			m.input_files_last_written = args['input_files_last_written']
			result = m.save()

			if result > 0:
				return 200

			abort(400, message="Unable to update project configuration table.")
		except Project_config.DoesNotExist:
			abort(404, message="Could not retrieve project configuration data.")


class SwatRunSettingsApi(Resource):
	def put(self, project_db):
		SetupProjectDatabase.init(project_db)
		try:
			m = Project_config.get()
			m.swat_last_run = datetime.now()
			m.output_last_imported = None
			result = m.save()

			if result > 0:
				return 200

			abort(400, message="Unable to update project configuration table.")
		except Project_config.DoesNotExist:
			abort(404, message="Could not retrieve project configuration data.")


class SaveOutputReadSettingsApi(Resource):
	def put(self, project_db):
		SetupProjectDatabase.init(project_db)
		try:
			m = Project_config.get()
			m.output_last_imported = datetime.now()
			result = m.save()

			if result > 0:
				return 200

			abort(400, message="Unable to update project configuration table.")
		except Project_config.DoesNotExist:
			abort(404, message="Could not retrieve project configuration data.")


class InfoApi(Resource):
	def get(self, project_db):
		SetupProjectDatabase.init(project_db)
		try:
			m = Project_config.get()

			gis_type = 'QSWAT+ ' if m.gis_type == 'qgis' else 'GIS '

			info = {
				'name': m.project_name,
				'is_lte': m.is_lte,
				'status': {
					'imported_weather': climate.Weather_sta_cli.select().count() > 0 and climate.Weather_wgn_cli.select().count() > 0,
					'wrote_inputs': m.input_files_last_written is not None,
					'ran_swat': m.swat_last_run is not None,
					'imported_output': m.output_last_imported is not None
				},
				'simulation': model_to_dict(simulation.Time_sim.get_or_none()),
				'total_area': gis.Gis_subbasins.select(fn.Sum(gis.Gis_subbasins.area)).scalar(),
				'totals': {
					'hru': connect.Hru_con.select().count(),
					'lhru': connect.Hru_lte_con.select().count(),
					'rtu': connect.Rout_unit_con.select().count(),
					'mfl': connect.Modflow_con.select().count(),
					'aqu': connect.Aquifer_con.select().count(),
					'cha': connect.Channel_con.select().count(),
					'res': connect.Reservoir_con.select().count(),
					'rec': connect.Recall_con.select().count(),
					'exco': connect.Exco_con.select().count(),
					'dlr': connect.Delratio_con.select().count(),
					'out': connect.Outlet_con.select().count(),
					'lcha': connect.Chandeg_con.select().count(),
					'aqu2d': connect.Aquifer2d_con.select().count(),
					'lsus': regions.Ls_unit_def.select().count(),
					'subs': gis.Gis_subbasins.select().count()
				},
				'editor_version': m.editor_version,
				'gis_version': gis_type + m.gis_version
			}

			return info
		except Project_config.DoesNotExist:
			abort(404, message="Could not retrieve project configuration data.")
