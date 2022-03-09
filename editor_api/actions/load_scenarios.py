from helpers.executable_api import ExecutableApi, Unbuffered
from helpers import utils

import sys
import argparse
import os, os.path
from shutil import copyfile, copytree, rmtree
import time

class LoadScenarios(ExecutableApi):
	def load(self, project_db, name):
		try:
			self.emit_progress(10, 'Removing default scenario files...')
			project_path = os.path.dirname(project_db)
			scenarios_path = os.path.join(project_path, 'Scenarios')
			new_scenario_path = os.path.join(scenarios_path, name)
			
			default_scenario_path = os.path.join(scenarios_path, 'Default')
			if not os.path.exists(default_scenario_path):
				default_scenario_path = os.path.join(scenarios_path, 'default')
			
			if os.path.exists(default_scenario_path):
				rmtree(default_scenario_path)

			self.emit_progress(60, 'Copying scenario files...')
			copytree(new_scenario_path, os.path.join(scenarios_path, 'Default'))

			self.emit_progress(90, 'Copying project database...')
			base_path = os.path.dirname(project_db)
			project_db_file = os.path.relpath(project_db, base_path)
			new_db_file = os.path.join(new_scenario_path, project_db_file)
			if not os.path.exists(new_db_file):
				raise IOError('Could not locate scenario database file. Your scenario might not be properly saved.')
			os.remove(project_db)
			copyfile(new_db_file, project_db)
		except Exception as ex:
			sys.exit(ex)

	def save(self, project_db, txtinout_path, results_path, new_name):
		try:
			self.emit_progress(2, 'Creating new directories...')
			project_path = os.path.dirname(project_db)
			scenarios_path = os.path.join(project_path, 'Scenarios')
			if not os.path.exists(scenarios_path):
				os.makedirs(scenarios_path)
			new_scenario_path = os.path.join(scenarios_path, new_name)
			if os.path.exists(new_scenario_path):
				raise IOError('A scenario with this name already exists. Please enter a unique name and try again.')
			os.makedirs(new_scenario_path)

			new_txtinout_path = os.path.join(new_scenario_path, 'TxtInOut')
			#os.makedirs(new_txtinout_path)
			self.emit_progress(30, 'Copying input files...')
			copytree(txtinout_path, new_txtinout_path)

			if txtinout_path != results_path:
				new_results_path = os.path.join(new_scenario_path, 'Results')
				#os.makedirs(new_results_path)
				self.emit_progress(60, 'Copying result files...')
				copytree(results_path, new_results_path)

			base_path = os.path.dirname(project_db)
			project_db_file = os.path.relpath(project_db, base_path)
			self.emit_progress(90, 'Copying project database...')
			copyfile(project_db, os.path.join(new_scenario_path, project_db_file))
		except Exception as ex:
			sys.exit(ex)


if __name__ == '__main__':
	sys.stdout = Unbuffered(sys.stdout)
	parser = argparse.ArgumentParser(description="Load or save a scenario")
	parser.add_argument("action", type=str, help="name of the API action: setup_project, import_gis, import_weather, read_output, write_files, import_csv, export_csv, update_project, reimport_gis, run")
	parser.add_argument("--project_db_file", type=str, help="full path of project SQLite database file", nargs="?")
	parser.add_argument("--input_files_dir", type=str, help="full path of where to write input files, defaults to Scenarios/Default/TxtInOut", nargs="?")
	parser.add_argument("--output_files_dir", type=str, help="full path of output files directory", nargs="?")
	parser.add_argument("--project_name", type=str, help="project name", nargs="?")

	args = parser.parse_args()

	api = LoadScenarios()
	if args.action == "save_scenario":
		api.save(args.project_db_file, args.input_files_dir, args.output_files_dir, args.project_name)
	elif args.action == "load_scenario":
		api.load(args.project_db_file, args.project_name)
