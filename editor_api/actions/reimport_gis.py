from helpers.executable_api import ExecutableApi, Unbuffered
from helpers import utils
from database import lib
from database.project import base as project_base
from database.project.config import Project_config
from database.project.setup import SetupProjectDatabase
from database.datasets.setup import SetupDatasetsDatabase
from database.datasets.definitions import Version
from .import_gis import GisImport
from . import update_project

import sys
import argparse
import os, os.path
import json
from shutil import copyfile
import time

class ReimportGis(ExecutableApi):
	def __init__(self, project_db, editor_version, project_name=None, datasets_db=None, constant_ps=True, is_lte=False):
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

		# Run updates if needed
		SetupProjectDatabase.init(project_db, datasets_db)
		config = Project_config.get()
		if config.editor_version in update_project.available_to_update:
			update_project.UpdateProject(project_db, editor_version, update_project_values=True)

		# Backup original db before beginning
		try:
			self.emit_progress(2, 'Backing up project database...')
			filename, file_extension = os.path.splitext(rel_project_db)
			bak_filename = filename + '_bak_' + time.strftime('%Y%m%d-%H%M%S') + file_extension
			bak_dir = os.path.join(base_path, 'DatabaseBackups')
			if not os.path.exists(bak_dir):
				os.makedirs(bak_dir)
			backup_db_file = os.path.join(bak_dir, bak_filename)
			copyfile(project_db, backup_db_file)
		except IOError as err:
			sys.exit(err)

		self.emit_progress(5, 'Updating project settings...')
		config = Project_config.get() # Get again due to modification when updating
		config.imported_gis = False
		config.is_lte = is_lte
		config.save()

		api = GisImport(project_db, True, constant_ps, backup_db_file)
		api.insert_default()


if __name__ == '__main__':
	sys.stdout = Unbuffered(sys.stdout)
	parser = argparse.ArgumentParser(description="Update and re-import a SWAT+ project database from GIS")
	parser.add_argument("--project_db_file", type=str, help="full path of project SQLite database file", nargs="?")
	parser.add_argument("--project_name", type=str, help="project name", nargs="?")
	parser.add_argument("--editor_version", type=str, help="editor version", nargs="?")
	parser.add_argument("--datasets_db_file", type=str, help="full path of datasets SQLite database file", nargs="?")
	parser.add_argument("--constant_ps", type=str, help="y/n constant point source values (default n)", nargs="?")
	parser.add_argument("--is_lte", type=str, help="y/n use lte version of SWAT+ (default n)", nargs="?")

	args = parser.parse_args()

	constant_ps = True if args.constant_ps == "y" else False
	is_lte = True if args.is_lte == "y" else False

	api = ReimportGis(args.project_db_file, args.editor_version, args.project_name, args.datasets_db_file, constant_ps, is_lte)
