from helpers.executable_api import ExecutableApi, Unbuffered
from helpers import utils
from .setup_project import SetupProject
from .import_weather import WeatherImport, Swat2012WeatherImport, WgnImport
from .write_files import WriteFiles
from .read_output import ReadOutput
from database.project.config import Project_config
from database.project.simulation import Time_sim

import sys
import argparse
import os, os.path
from datetime import datetime


class RunAll(ExecutableApi):
	def __init__(self, project_db, editor_version, swat_exe, 
		weather_dir, weather_save_dir='', weather_import_format='plus',
		wgn_import_method='database', wgn_db='C:/SWAT/SWATPlus/Databases/swatplus_wgn.sqlite', wgn_table='wgn_cfsr_world', wgn_csv_sta_file=None, wgn_csv_mon_file=None,
		year_start=None, day_start=None, year_end=None, day_end=None,
		input_files_dir=None):
		# Setup project databases and import GIS data
		SetupProject(project_db, editor_version, project_db.replace('.sqlite', '.json', 1))

		rel_input_files = 'Scenarios/Default/TxtInOut' if input_files_dir is None else utils.rel_path(project_db, input_files_dir)
		input_files_path = utils.full_path(project_db, rel_input_files)

		if weather_import_format != 'plus' and weather_save_dir == '':
			weather_save_dir = rel_input_files

		# Set project config table arguments used by APIs
		m = Project_config.get()
		m.wgn_db = wgn_db
		m.wgn_table_name = wgn_table
		m.weather_data_dir = utils.rel_path(project_db, weather_dir) if weather_import_format == 'plus' else utils.rel_path(project_db, weather_save_dir)
		m.input_files_dir = rel_input_files
		result = m.save()

		# Import WGN
		wgn_api = WgnImport(project_db, True, False, wgn_import_method, wgn_csv_sta_file, wgn_csv_mon_file)
		wgn_api.import_data()
		
		# Import weather files
		if weather_import_format == 'plus':
			weather_api = WeatherImport(project_db, True, True)
			weather_api.import_data()
		else:
			weather_api = Swat2012WeatherImport(project_db, True, True, weather_dir)
			weather_api.import_data()

		# Set time_sim if parameters given
		if year_start is not None:
			Time_sim.update_and_exec(day_start, year_start, day_end, year_end, 0)

		# Write input files
		write_api = WriteFiles(project_db)
		write_api.write()

		# Run the model
		cwd = os.getcwd()
		os.chdir(input_files_path)
		run_result = os.system(swat_exe)
		print(run_result)

		# Import output files to db if successful run
		if run_result == 0:
			os.chdir(cwd)
			output_db_file = os.path.join(input_files_path, '../', 'Results', 'swatplus_output.sqlite')
			output_api = ReadOutput(input_files_path, output_db_file)
			output_api.read()

			m = Project_config.get()
			m.swat_last_run = datetime.now()
			m.output_last_imported = datetime.now()
			result = m.save()

if __name__ == '__main__':
	sys.stdout = Unbuffered(sys.stdout)
	parser = argparse.ArgumentParser(description="Run SWAT+ Editor from the command line (import from QSWAT+, WGN, and weather; run the mdoel)")
	parser.add_argument("--project_db_file", type=str, help="full path of project SQLite database file")
	parser.add_argument("--editor_version", type=str, help="editor version")
	parser.add_argument("--swat_exe_file", type=str, help="full path of the SWAT+ executable file")
	parser.add_argument("--weather_dir", type=str, help="full path of weather files location")
	parser.add_argument("--weather_import_format", type=str, help="weather files import format (plus or old)", nargs="?", default="plus")
	parser.add_argument("--weather_save_dir", type=str, help="if weather files import format is old, provide the path to save your plus weather files", nargs="?", default="")
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
	api = RunAll(args.project_db_file, args.editor_version, args.swat_exe_file,
		args.weather_dir, args.weather_save_dir, args.weather_import_format,
		args.wgn_import_method, args.wgn_db, args.wgn_table, args.wgn_csv_sta_file, args.wgn_csv_mon_file,
		args.year_start, args.day_start, args.year_end, args.day_end,
		args.input_files_dir)
