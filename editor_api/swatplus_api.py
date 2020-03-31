from helpers.executable_api import Unbuffered
from actions.setup_project import SetupProject
from actions.import_gis import GisImport
from actions.import_weather import WeatherImport, Swat2012WeatherImport, WgnImport
from actions.read_output import ReadOutput
from actions.write_files import WriteFiles
from actions.create_databases import CreateDatasetsDb, CreateOutputDb, CreateProjectDb
from actions.import_export_data import ImportExportData
from actions.update_project import UpdateProject
from actions.reimport_gis import ReimportGis
from actions.run_all import RunAll
from database import soils

import sys
import argparse

if __name__ == '__main__':
	sys.stdout = Unbuffered(sys.stdout)
	parser = argparse.ArgumentParser(description="SWAT+ Editor API")
	parser.add_argument("action", type=str, help="name of the API action: setup_project, import_gis, import_weather, read_output, write_files, import_csv, export_csv, update_project, reimport_gis, run")

	parser.add_argument("--project_db_file", type=str, help="full path of project SQLite database file", nargs="?")
	parser.add_argument("--delete_existing", type=str, help="y/n delete existing data first", nargs="?")

	# import weather
	parser.add_argument("--import_type", type=str, help="type of weather to import: observed, observed2012, wgn", nargs="?")
	parser.add_argument("--create_stations", type=str, help="y/n create stations for wgn", nargs="?")
	parser.add_argument("--source_dir", type=str, help="full path of SWAT2012 weather files", nargs="?")
	parser.add_argument("--import_method", type=str, help="import method for wgn (database, two_file, one_file)", nargs="?")
	parser.add_argument("--file1", type=str, help="full path of file", nargs="?")
	parser.add_argument("--file2", type=str, help="full path of file", nargs="?")

	# read output
	parser.add_argument("--output_files_dir", type=str, help="full path of output files directory", nargs="?")
	parser.add_argument("--output_db_file", type=str, help="full path of output SQLite database file", nargs="?")

	# create databases
	parser.add_argument("--db_type", type=str, help="which database: datasets, output, project", nargs="?")
	parser.add_argument("--db_file", type=str, help="full path of SQLite database file", nargs="?")
	parser.add_argument("--db_file2", type=str, help="full path of SQLite database file", nargs="?")
	parser.add_argument("--project_name", type=str, help="project name", nargs="?")
	parser.add_argument("--editor_version", type=str, help="editor version", nargs="?")

	# import / export csv files
	parser.add_argument("--file_name", type=str, help="full path of csv file", nargs="?")
	parser.add_argument("--table_name", type=str, help="database table", nargs="?")
	parser.add_argument("--related_id", type=int, help="database table", nargs="?")
	parser.add_argument("--ignore_id", type=str, help="y/n ignore id column", nargs="?")

	# setup project
	parser.add_argument("--datasets_db_file", type=str, help="full path of datasets SQLite database file", nargs="?")
	parser.add_argument("--settings_file", type=str, help="editor version", nargs="?")
	parser.add_argument("--constant_ps", type=str, help="y/n constant point source values (default y)", nargs="?")
	parser.add_argument("--is_lte", type=str, help="y/n use lte version of SWAT+ (default n)", nargs="?")
	parser.add_argument("--update_project_values", type=str, help="y/n update project values (default n)", nargs="?")
	parser.add_argument("--reimport_gis", type=str, help="y/n re-import GIS data (default n)", nargs="?")

	# run from command line
	parser.add_argument("--swat_exe_file", type=str, help="full path of the SWAT+ executable file", nargs="?")
	parser.add_argument("--weather_dir", type=str, help="full path of weather files location", nargs="?")
	parser.add_argument("--weather_import_format", type=str, help="weather files import format (plus or 2012)", nargs="?", default="plus")
	parser.add_argument("--weather_save_dir", type=str, help="if weather files import format is 2012, provide the path to save your plus weather files", nargs="?", default="")
	parser.add_argument("--wgn_import_method", type=str, help="weather generator import method (database or csv)", nargs="?", default="database")
	parser.add_argument("--wgn_db", type=str, help="full path of wgn database", nargs="?", default="C:/SWAT/SWATPlus/Databases/swatplus_wgn.sqlite")
	parser.add_argument("--wgn_table", type=str, help="table name in wgn database (default wgn_cfsr_world)", nargs="?", default="wgn_cfsr_world")
	parser.add_argument("--wgn_csv_sta_file", type=str, help="wgn stations csv file, if import method = csv", nargs="?")
	parser.add_argument("--wgn_csv_mon_file", type=str, help="wgn monthly values csv file, if import method = csv", nargs="?")
	parser.add_argument("--year_start", type=str, help="starting year of simulation (omit to use weather files dates)", nargs="?")
	parser.add_argument("--day_start", type=str, help="starting day of simulation (omit to use weather files dates)", nargs="?")
	parser.add_argument("--year_end", type=str, help="ending year of simulation (omit to use weather files dates)", nargs="?")
	parser.add_argument("--day_end", type=str, help="ending day of simulation (omit to use weather files dates)", nargs="?")
	parser.add_argument("--input_files_dir", type=str, help="full path of where to write input files, defaults to Scenarios/Default/TxtInOut", nargs="?")

	args = parser.parse_args()

	del_ex = True if args.delete_existing == "y" else False
	cre_sta = True if args.create_stations == "y" else False
	constant_ps = True if args.constant_ps == "y" else False
	is_lte = True if args.is_lte == "y" else False
	update_project_values = True if args.update_project_values == "y" else False
	reimport_gis = True if args.reimport_gis == "y" else False

	if args.action == "setup_project":
		api = SetupProject(args.project_db_file, args.editor_version, args.settings_file, args.project_name, args.datasets_db_file, constant_ps, is_lte)
	elif args.action == "update_project":
		api = UpdateProject(args.project_db_file, args.editor_version, args.datasets_db_file, update_project_values, reimport_gis)
	elif args.action == "reimport_gis":
		api = ReimportGis(args.project_db_file, args.editor_version, args.settings_file, args.project_name, args.datasets_db_file, constant_ps, is_lte)
	elif args.action == "import_gis":
		api = GisImport(args.project_db_file, del_ex)
		api.insert_default()
	elif args.action == "import_weather":
		cre_sta = True if args.create_stations == "y" else False

		if args.import_type == "observed":
			api = WeatherImport(args.project_db_file, del_ex, cre_sta)
			api.import_data()
		elif args.import_type == "observed2012":
			api = Swat2012WeatherImport(args.project_db_file, del_ex, cre_sta, args.source_dir)
			api.import_data()
		elif args.import_type == "wgn":
			api = WgnImport(args.project_db_file, del_ex, cre_sta, args.import_method, args.file1, args.file2)
			api.import_data()
	elif args.action == "read_output":
		api = ReadOutput(args.output_files_dir, args.output_db_file)
		api.read()
	elif args.action == "write_files":
		api = WriteFiles(args.project_db_file)
		api.write()
	elif args.action == "create_database":
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
	elif args.action == "import_csv" or args.action == "export_csv":
		related_id = 0 if args.related_id is None else args.related_id
		ignore_id = False if args.ignore_id == "n" else True
		api = ImportExportData(args.file_name, args.table_name, args.db_file, del_ex, related_id, ignore_id)
	
		if args.action == "import_csv":
			api.import_csv()
		elif args.action == "export_csv":
			api.export_csv()
	elif args.action == "run":
		api = RunAll(args.project_db_file, args.editor_version, args.swat_exe_file,
			args.weather_dir, args.weather_save_dir, args.weather_import_format,
			args.wgn_import_method, args.wgn_db, args.wgn_table, args.wgn_csv_sta_file, args.wgn_csv_mon_file,
			args.year_start, args.day_start, args.year_end, args.day_end,
			args.input_files_dir)
