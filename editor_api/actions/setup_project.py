from helpers.executable_api import ExecutableApi, Unbuffered
from helpers import utils
from database import lib
from database.project import base as project_base
from database.project.config import Project_config
from database.project.setup import SetupProjectDatabase
from database.datasets.setup import SetupDatasetsDatabase
from database.datasets.definitions import Version
from database.project.hru_parm_db import Plants_plt as project_plants
from database.datasets.hru_parm_db import Plants_plt as dataset_plants
from .import_gis import GisImport

import sys
import argparse
import os, os.path
import json
from shutil import copyfile
import time
from playhouse.migrate import *

OVERWRITE_PLANTS = False

class SetupProject(ExecutableApi):
	def __init__(self, project_db, editor_version, settings_file=None, project_name=None, datasets_db=None, constant_ps=True, is_lte=False):
		self.__abort = False

		base_path = os.path.dirname(project_db)
		rel_project_db = os.path.relpath(project_db, base_path)

		if datasets_db is None:
			conn = lib.open_db(project_db)
			if not lib.exists_table(conn, 'project_config'):
				sys.exit('No datasets database provided and the project_config table in your project database does not exist. Please provide either a datasets database file or an existing project database.')

			SetupProjectDatabase.init(project_db)
			try:
				config = Project_config.get()
				datasets_db = utils.full_path(project_db, config.reference_db)
				project_name = config.project_name
			except Project_config.DoesNotExist:
				sys.exit('Could not retrieve project configuration data.')

		rel_datasets_db = os.path.relpath(datasets_db, base_path)

		ver_check = SetupDatasetsDatabase.check_version(datasets_db, editor_version)
		if ver_check is not None:
			sys.exit(ver_check)

		# Backup original db before beginning
		try:
			self.emit_progress(2, 'Backing up GIS database...')
			filename, file_extension = os.path.splitext(rel_project_db)
			bak_filename = filename + '_bak_' + time.strftime('%Y%m%d-%H%M%S') + file_extension
			bak_dir = os.path.join(base_path, 'DatabaseBackups')
			if not os.path.exists(bak_dir):
				os.makedirs(bak_dir)
			backup_db_file = os.path.join(bak_dir, bak_filename)
			copyfile(project_db, backup_db_file)
		except IOError as err:
			sys.exit(err)

		try:
			SetupProjectDatabase.init(project_db, datasets_db)
			self.emit_progress(10, 'Creating database tables...')
			SetupProjectDatabase.create_tables()
			self.emit_progress(50, 'Copying data from SWAT+ datasets database...')
			SetupProjectDatabase.initialize_data(project_name, is_lte, overwrite_plants=OVERWRITE_PLANTS)

			config = Project_config.get_or_create_default(
				editor_version=editor_version,
				project_name=project_name,
				project_db=rel_project_db,
				reference_db=rel_datasets_db,
				project_directory='',
				is_lte=is_lte
			)

			conn = lib.open_db(project_db)
			plant_cols = lib.get_column_names(conn, 'plants_plt')
			plant_col_names = [v['name'] for v in plant_cols]
			if 'days_mat' not in plant_col_names:
				migrator = SqliteMigrator(SqliteDatabase(project_db))
				migrate(
					migrator.rename_column('plants_plt', 'plnt_hu', 'days_mat')
				)
				for p in project_plants:
					dp = dataset_plants.get_or_none(dataset_plants.name == p.name)
					if dp is not None:
						p.days_mat = dp.days_mat
					else:
						p.days_mat = 0
					p.save()
		except Exception as ex:
			if backup_db_file is not None:
				self.emit_progress(50, "Error occurred. Rolling back database...")
				SetupProjectDatabase.rollback(project_db, backup_db_file)
				self.emit_progress(100, "Error occurred.")
			sys.exit(str(ex))

		api = GisImport(project_db, True, constant_ps, backup_db_file)
		api.insert_default()

		settings_data = {
			'swatplus-project': {
				'version': editor_version,
				'name': project_name,
				'databases': {
					'project': rel_project_db,
					'datasets': rel_datasets_db
				},
				'model': 'SWAT+' if not is_lte else 'SWAT+ lte'
			}
		}

		with open(settings_file, 'w') as file:
			json.dump(settings_data, file, indent='\t')


if __name__ == '__main__':
	sys.stdout = Unbuffered(sys.stdout)
	parser = argparse.ArgumentParser(description="Set up SWAT+ project database")
	parser.add_argument("--project_db_file", type=str, help="full path of project SQLite database file", nargs="?")
	parser.add_argument("--project_name", type=str, help="project name", nargs="?")
	parser.add_argument("--editor_version", type=str, help="editor version", nargs="?")
	parser.add_argument("--datasets_db_file", type=str, help="full path of datasets SQLite database file", nargs="?")
	parser.add_argument("--settings_file", type=str, help="editor version", nargs="?")
	parser.add_argument("--constant_ps", type=str, help="y/n constant point source values (default y)", nargs="?")
	parser.add_argument("--is_lte", type=str, help="y/n use lte version of SWAT+ (default n)", nargs="?")

	args = parser.parse_args()

	constant_ps = True if args.constant_ps == "y" else False
	is_lte = True if args.is_lte == "y" else False

	api = SetupProject(args.project_db_file, args.editor_version, args.settings_file, args.project_name, args.datasets_db_file, constant_ps, is_lte)
