from helpers.executable_api import ExecutableApi, Unbuffered
from database.datasets.setup import SetupDatasetsDatabase
from database.output.setup import SetupOutputDatabase
from database.project.setup import SetupProjectDatabase
from database.project.config import Project_config
from database import soils

import sys
import argparse
import os.path


class CreateDatasetsDb(ExecutableApi):
	def __init__(self, db_file):
		self.__abort = False
		SetupDatasetsDatabase.init(db_file)

	def create(self, version):
		SetupDatasetsDatabase.create_tables()
		SetupDatasetsDatabase.initialize_data(version)


class CreateOutputDb(ExecutableApi):
	def __init__(self, db_file):
		self.__abort = False
		SetupOutputDatabase.init(db_file)

	def create(self):
		SetupOutputDatabase.create_tables()


class CreateProjectDb(ExecutableApi):
	def __init__(self, db_file, datasets_db_file, project_name, editor_version):
		self.__abort = False
		self.project_db = db_file
		self.reference_db = datasets_db_file
		self.project_name = project_name
		self.editor_version = editor_version
		SetupProjectDatabase.init(db_file, datasets_db_file)

	def create(self):
		SetupProjectDatabase.create_tables()
		SetupProjectDatabase.initialize_data("demo")
		
		base_path = os.path.dirname(self.project_db)
		rel_project_db = os.path.relpath(self.project_db, base_path)
		rel_reference_db = os.path.relpath(self.reference_db, base_path)
		print("project_db {}".format(self.project_db))
		print("base_path {}".format(base_path))
		print("rel_project_db {}".format(rel_project_db))
		print("rel_reference_db {}".format(rel_reference_db))
		
		Project_config.get_or_create_default(
			editor_version=self.editor_version,
			project_name=self.project_name,
			#project_db=rel_project_db,
			reference_db=rel_reference_db
		)


if __name__ == '__main__':
	sys.stdout = Unbuffered(sys.stdout)
	parser = argparse.ArgumentParser(description="Create the SWAT+ datasets database")
	parser.add_argument("db_type", type=str, help="which database: datasets, output, project")
	parser.add_argument("db_file", type=str, help="full path of SQLite database file")
	parser.add_argument("db_file2", type=str, help="full path of SQLite database file", nargs="?")
	parser.add_argument("project_name", type=str, help="project name", nargs="?")
	parser.add_argument("editor_version", type=str, help="editor version", nargs="?")
	args = parser.parse_args()

	if args.db_type == "datasets":
		api = CreateDatasetsDb(args.db_file)
		api.create(args.editor_version)
	elif args.db_type == "output":
		api = CreateOutputDb(args.db_file)
		api.create()
	elif args.db_type == "project":
		project_name = "demo" if args.project_name is None else args.project_name
		editor_version = "api" if args.editor_version is None else args.editor_version
		
		api = CreateProjectDb(args.db_file, args.db_file2, project_name, editor_version)
		api.create()
	elif args.db_type == "ssurgo_soils":
		soils.db.init(args.db_file)
		api = soils.ImportSoils()
		api.ssurgo(args.db_file2)
