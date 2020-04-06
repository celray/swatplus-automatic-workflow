from helpers.executable_api import ExecutableApi, Unbuffered
from database import lib as db_lib
from database.project import base as project_base
from database.project.setup import SetupProjectDatabase
from database.project.config import Project_config
from database.project.config import File_cio as project_file_cio, File_cio_classification
from database.project.climate import Weather_file

from fileio import connect, exco, dr, recall, climate, channel, aquifer, hydrology, reservoir, hru, lum, soils, init, routing_unit, regions, simulation, hru_parm_db, config, ops, structural, decision_table, basin, change
from helpers import utils

import sys
import argparse
import os.path
from datetime import datetime
from shutil import copyfile

NULL_FILE = "null"


class WriteFiles(ExecutableApi):
	def __init__(self, project_db_file):
		self.__abort = False
		SetupProjectDatabase.init(project_db_file)
		self.project_db = project_base.db

		try:
			config = Project_config.get()
			
			input_files_dir = utils.full_path(project_db_file, config.input_files_dir).replace("\\","/")
			if not os.path.exists(input_files_dir):
				sys.exit('The input files directory {dir} does not exist. Please select a valid path and try again.'.format(dir=input_files_dir))
			
			weather_data_dir = None
			if config.weather_data_dir is not None:
				weather_data_dir = utils.full_path(project_db_file, config.weather_data_dir).replace("\\","/")
				if not os.path.exists(weather_data_dir):
					sys.exit('Weather data directory {dir} does not exist.'.format(dir=weather_data_dir))

			self.__dir = input_files_dir
			self.__weather_dir = weather_data_dir
			self.__version = config.editor_version
			self.__current_progress = 0
			self.__is_lte = config.is_lte
		except Project_config.DoesNotExist:
			sys.exit('Could not retrieve project configuration from database')

	def write(self):
		try:
			step = 3
			small_step = 1
			big_step = 5
			bigger_step = 10
			total = 0

			self.write_simulation(total, step)
			total += step

			self.write_climate(total, bigger_step)
			total += bigger_step

			self.copy_weather_files(total, step)
			total += step

			self.write_connect(total, step)
			total += step

			self.write_channel(total, step)
			total += step

			self.write_reservoir(total, step)
			total += step

			self.write_routing_unit(total, step)
			total += step

			self.write_hru(total, bigger_step)
			total += bigger_step

			self.write_dr(total, small_step)
			total += small_step

			self.write_aquifer(total, small_step)
			total += small_step

			self.write_herd(total, small_step)
			total += small_step

			self.write_water_rights(total, small_step)
			total += small_step

			self.write_link(total, small_step)
			total += small_step

			self.write_basin(total, small_step)
			total += small_step

			self.write_hydrology(total, step)
			total += step

			self.write_exco(total, step)
			total += step

			self.write_recall(total, step)
			total += step

			self.write_structural(total, step)
			total += step

			self.write_parm_db(total, step)
			total += step

			self.write_ops(total, step)
			total += step

			self.write_lum(total, step)
			total += step

			self.write_chg(total, step)
			total += step

			self.write_init(total, step)
			total += step

			self.write_soils(total, bigger_step)
			total += bigger_step

			self.write_decision_table(total, step)
			total += step

			self.write_regions(total, step)
			total += step

			self.update_file_status(total, "file.cio")
			config.File_cio(os.path.join(self.__dir, "file.cio"), self.__version).write()

			Project_config.update(input_files_last_written=datetime.now(), swat_last_run=None, output_last_imported=None).execute()
		except ValueError as err:
			sys.exit(err)

	def get_file_names(self, section, num_required):
		file_names = []

		try:
			c = File_cio_classification.get(File_cio_classification.name == section)
			m = project_file_cio.select().where(project_file_cio.classification == c).order_by(project_file_cio.order_in_class)
			file_names = [v.file_name for v in m]
		except File_cio_classification.DoesNotExist:
			pass
		except project_file_cio.DoesNotExist:
			pass

		if len(file_names) < num_required:
			raise ValueError(
				"{section} file names not available in the project database nor the SWAT+ datasets database.".format(
					section=section))

		return file_names

	def copy_weather_files(self, start_prog, allocated_prog):
		if self.__weather_dir is not None and self.__dir != self.__weather_dir:
			self.copy_weather_file("hmd.cli", start_prog)
			self.copy_weather_file("pcp.cli", start_prog)
			self.copy_weather_file("slr.cli", start_prog)
			self.copy_weather_file("tmp.cli", start_prog)
			self.copy_weather_file("wnd.cli", start_prog)

			query = Weather_file.select()
			num_files = query.count()
			if num_files > 0:
				prog_step = round((allocated_prog) / num_files)
				prog = start_prog

				for wf in query:
					self.copy_weather_file(wf.filename, prog)
					prog += prog_step

	def copy_weather_file(self, file_name, prog):
		try:
			self.emit_progress(prog, "Copying weather file {}...".format(file_name))
			copyfile(os.path.join(self.__weather_dir, file_name), os.path.join(self.__dir, file_name))
		except IOError as err:
			print("\n\t   ! {0} was not copied\n\t     was {1}.txt in the data?".format(
				os.path.basename(file_name), os.path.basename(file_name).split(".")[0]))
			# print(err)

	def write_simulation(self, start_prog, allocated_prog):
		num_files = 4
		files = self.get_file_names("simulation", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		time_sim_file = files[0].strip()
		if time_sim_file != NULL_FILE:
			self.update_file_status(start_prog, time_sim_file)
			simulation.Time_sim(os.path.join(self.__dir, time_sim_file), self.__version).write()

		prog += prog_step
		print_prt_file = files[1].strip()
		if print_prt_file != NULL_FILE:
			self.update_file_status(start_prog, print_prt_file)
			simulation.Print_prt(os.path.join(self.__dir, print_prt_file), self.__version).write()

		prog += prog_step
		object_prt_file = files[2].strip()
		if object_prt_file != NULL_FILE:
			self.update_file_status(start_prog, object_prt_file)
			simulation.Object_prt(os.path.join(self.__dir, object_prt_file), self.__version).write()

		prog += prog_step
		object_cnt_file = files[3].strip()
		if object_cnt_file != NULL_FILE:
			self.update_file_status(start_prog, object_cnt_file)
			simulation.Object_cnt(os.path.join(self.__dir, object_cnt_file), self.__version).write()

	def write_climate(self, start_prog, allocated_prog):
		num_files = 8
		files = self.get_file_names("climate", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		weather_sta_file = files[0].strip()
		if weather_sta_file != NULL_FILE:
			self.update_file_status(prog, weather_sta_file)
			climate.Weather_sta_cli(os.path.join(self.__dir, weather_sta_file), self.__version).write()

		prog += prog_step
		weather_wgn_file = files[1].strip()
		if weather_wgn_file != NULL_FILE:
			self.update_file_status(prog, weather_wgn_file)
			climate.Weather_wgn_cli(os.path.join(self.__dir, weather_wgn_file), self.__version).write()

	def write_connect(self, start_prog, allocated_prog):
		num_files = 13
		files = self.get_file_names("connect", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		hru_con_file = files[0].strip()
		if hru_con_file != NULL_FILE:
			self.update_file_status(prog, hru_con_file)
			connect.Hru_con(os.path.join(self.__dir, hru_con_file), self.__version).write()

		prog += prog_step
		hru_lte_con_file = files[1].strip()
		if hru_lte_con_file != NULL_FILE:
			self.update_file_status(prog, hru_lte_con_file)
			connect.Hru_lte_con(os.path.join(self.__dir, hru_lte_con_file), self.__version).write()

		prog += prog_step
		rout_unit_con_file = files[2].strip()
		if rout_unit_con_file != NULL_FILE:
			self.update_file_status(prog, rout_unit_con_file)
			connect.Rout_unit_con(os.path.join(self.__dir, rout_unit_con_file), self.__version).write()

		prog += prog_step
		aquifer_con_file = files[4].strip()
		if aquifer_con_file != NULL_FILE:
			self.update_file_status(prog, aquifer_con_file)
			connect.Aquifer_con(os.path.join(self.__dir, aquifer_con_file), self.__version).write()

		prog += prog_step
		channel_con_file = files[6].strip()
		if channel_con_file != NULL_FILE:
			self.update_file_status(prog, channel_con_file)
			connect.Channel_con(os.path.join(self.__dir, channel_con_file), self.__version).write()

		prog += prog_step
		reservoir_con_file = files[7].strip()
		if reservoir_con_file != NULL_FILE:
			self.update_file_status(prog, reservoir_con_file)
			connect.Reservoir_con(os.path.join(self.__dir, reservoir_con_file), self.__version).write()

		prog += prog_step
		recall_con_file = files[8].strip()
		if recall_con_file != NULL_FILE:
			self.update_file_status(prog, recall_con_file)
			connect.Recall_con(os.path.join(self.__dir, recall_con_file), self.__version).write()

		prog += prog_step
		exco_con_file = files[9].strip()
		if exco_con_file != NULL_FILE:
			self.update_file_status(prog, exco_con_file)
			connect.Exco_con(os.path.join(self.__dir, exco_con_file), self.__version).write()

		prog += prog_step
		delratio_con_file = files[10].strip()
		if delratio_con_file != NULL_FILE:
			self.update_file_status(prog, delratio_con_file)
			connect.Delratio_con(os.path.join(self.__dir, delratio_con_file), self.__version).write()

		prog += prog_step
		chandeg_con_file = files[12].strip()
		if chandeg_con_file != NULL_FILE:
			self.update_file_status(prog, chandeg_con_file)
			connect.Chandeg_con(os.path.join(self.__dir, chandeg_con_file), self.__version).write()

	def write_channel(self, start_prog, allocated_prog):
		num_files = 7
		files = self.get_file_names("channel", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		channel_cha_file = files[1].strip()
		if channel_cha_file != NULL_FILE:
			self.update_file_status(start_prog, channel_cha_file)
			channel.Channel_cha(os.path.join(self.__dir, channel_cha_file), self.__version).write()

		prog += prog_step
		initial_cha_file = files[0].strip()
		if initial_cha_file != NULL_FILE:
			self.update_file_status(prog, initial_cha_file)
			channel.Initial_cha(os.path.join(self.__dir, initial_cha_file), self.__version).write()

		prog += prog_step
		hydrology_cha_file = files[2].strip()
		if hydrology_cha_file != NULL_FILE:
			self.update_file_status(prog, hydrology_cha_file)
			channel.Hydrology_cha(os.path.join(self.__dir, hydrology_cha_file), self.__version).write()

		prog += prog_step
		sediment_cha_file = files[3].strip()
		if sediment_cha_file != NULL_FILE:
			self.update_file_status(prog, sediment_cha_file)
			channel.Sediment_cha(os.path.join(self.__dir, sediment_cha_file), self.__version).write()

		prog += prog_step
		nutrients_cha_file = files[4].strip()
		if nutrients_cha_file != NULL_FILE:
			self.update_file_status(prog, nutrients_cha_file)
			channel.Nutrients_cha(os.path.join(self.__dir, nutrients_cha_file), self.__version).write()

		prog += prog_step
		channel_lte_cha_file = files[5].strip()
		if channel_lte_cha_file != NULL_FILE:
			self.update_file_status(prog, channel_lte_cha_file)
			channel.Channel_lte_cha(os.path.join(self.__dir, channel_lte_cha_file), self.__version).write()

		prog += prog_step
		hyd_sed_lte_cha_file = files[6].strip()
		if hyd_sed_lte_cha_file != NULL_FILE:
			self.update_file_status(prog, hyd_sed_lte_cha_file)
			channel.Hyd_sed_lte_cha(os.path.join(self.__dir, hyd_sed_lte_cha_file), self.__version).write()

	def write_reservoir(self, start_prog, allocated_prog):
		num_files = 8
		files = self.get_file_names("reservoir", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		initial_res_file = files[0].strip()
		if initial_res_file != NULL_FILE:
			self.update_file_status(prog, initial_res_file)
			reservoir.Initial_res(os.path.join(self.__dir, initial_res_file), self.__version).write()

		prog += prog_step
		reservoir_res_file = files[1].strip()
		if reservoir_res_file != NULL_FILE:
			self.update_file_status(prog, reservoir_res_file)
			reservoir.Reservoir_res(os.path.join(self.__dir, reservoir_res_file), self.__version).write()

		prog += prog_step
		hydrology_res_file = files[2].strip()
		if hydrology_res_file != NULL_FILE:
			self.update_file_status(prog, hydrology_res_file)
			reservoir.Hydrology_res(os.path.join(self.__dir, hydrology_res_file), self.__version).write()

		prog += prog_step
		sediment_res_file = files[3].strip()
		if sediment_res_file != NULL_FILE:
			self.update_file_status(prog, sediment_res_file)
			reservoir.Sediment_res(os.path.join(self.__dir, sediment_res_file), self.__version).write()

		prog += prog_step
		nutrients_res_file = files[4].strip()
		if nutrients_res_file != NULL_FILE:
			self.update_file_status(prog, nutrients_res_file)
			reservoir.Nutrients_res(os.path.join(self.__dir, nutrients_res_file), self.__version).write()

		prog += prog_step
		weir_res_file = files[5].strip()
		if weir_res_file != NULL_FILE:
			self.update_file_status(prog, weir_res_file)
			reservoir.Weir_res(os.path.join(self.__dir, weir_res_file), self.__version).write()

		prog += prog_step
		wetland_wet_file = files[6].strip()
		if wetland_wet_file != NULL_FILE:
			self.update_file_status(prog, wetland_wet_file)
			reservoir.Wetland_wet(os.path.join(self.__dir, wetland_wet_file), self.__version).write()

		prog += prog_step
		hydrology_wet_file = files[7].strip()
		if hydrology_wet_file != NULL_FILE:
			self.update_file_status(prog, hydrology_wet_file)
			reservoir.Hydrology_wet(os.path.join(self.__dir, hydrology_wet_file), self.__version).write()

	def write_routing_unit(self, start_prog, allocated_prog):
		num_files = 4
		files = self.get_file_names("routing_unit", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		prog += prog_step
		rout_unit_def_file = files[0].strip()
		if rout_unit_def_file != NULL_FILE:
			self.update_file_status(prog, rout_unit_def_file)
			routing_unit.Rout_unit_def(os.path.join(self.__dir, rout_unit_def_file), self.__version).write()

		prog += prog_step
		rout_unit_ele_file = files[1].strip()
		if rout_unit_ele_file != NULL_FILE:
			self.update_file_status(prog, rout_unit_ele_file)
			routing_unit.Rout_unit_ele(os.path.join(self.__dir, rout_unit_ele_file), self.__version).write()

		rout_unit_ru_file = files[2].strip()
		if rout_unit_ru_file != NULL_FILE:
			self.update_file_status(prog, rout_unit_ru_file)
			routing_unit.Rout_unit(os.path.join(self.__dir, rout_unit_ru_file), self.__version).write()

		prog += prog_step
		rout_unit_dr_file = files[3].strip()
		if rout_unit_dr_file != NULL_FILE:
			self.update_file_status(prog, rout_unit_dr_file)
			routing_unit.Rout_unit_dr(os.path.join(self.__dir, rout_unit_dr_file), self.__version).write()

	def write_hru(self, start_prog, allocated_prog):
		num_files = 2
		files = self.get_file_names("hru", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		hru_data_file = files[0].strip()
		if hru_data_file != NULL_FILE:
			self.update_file_status(prog, hru_data_file)
			hru.Hru_data_hru(os.path.join(self.__dir, hru_data_file), self.__version).write()

		prog += prog_step
		hru_lte_hru_file = files[1].strip()
		if hru_lte_hru_file != NULL_FILE:
			self.update_file_status(prog, hru_lte_hru_file)
			hru.Hru_lte_hru(os.path.join(self.__dir, hru_lte_hru_file), self.__version).write()

	def write_dr(self, start_prog, allocated_prog):
		num_files = 6
		files = self.get_file_names("dr", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		delratio_del_file = files[0].strip()
		if delratio_del_file != NULL_FILE:
			self.update_file_status(prog, delratio_del_file)
			dr.Delratio_del(os.path.join(self.__dir, delratio_del_file), self.__version).write()

		prog += prog_step
		dr_om_file = files[1].strip()
		if dr_om_file != NULL_FILE:
			self.update_file_status(prog, dr_om_file)
			dr.Dr_om_del(os.path.join(self.__dir, dr_om_file), self.__version).write()

	def write_aquifer(self, start_prog, allocated_prog):
		num_files = 2
		files = self.get_file_names("aquifer", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		aquifer_aqu_file = files[1].strip()
		if aquifer_aqu_file != NULL_FILE:
			self.update_file_status(start_prog, aquifer_aqu_file)
			aquifer.Aquifer_aqu(os.path.join(self.__dir, aquifer_aqu_file), self.__version).write()

		prog += prog_step
		initial_aqu_file = files[0].strip()
		if initial_aqu_file != NULL_FILE:
			self.update_file_status(prog, initial_aqu_file)
			aquifer.Initial_aqu(os.path.join(self.__dir, initial_aqu_file), self.__version).write()

	def write_herd(self, start_prog, allocated_prog):
		pass

	def write_water_rights(self, start_prog, allocated_prog):
		pass

	def write_link(self, start_prog, allocated_prog):
		pass
		"""num_files = 2
		files = self.get_file_names("link", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		chan_aqu_lin_file = files[1].strip()
		if chan_aqu_lin_file != NULL_FILE:
			self.update_file_status(start_prog, chan_aqu_lin_file)
			aquifer.Chan_aqu_lin(os.path.join(self.__dir, chan_aqu_lin_file), self.__version).write()"""

	def write_basin(self, start_prog, allocated_prog):
		num_files = 2
		files = self.get_file_names("basin", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		codes_bsn_file = files[0].strip()
		if codes_bsn_file != NULL_FILE:
			self.update_file_status(prog, codes_bsn_file)
			basin.Codes_bsn(os.path.join(self.__dir, codes_bsn_file), self.__version).write()

		prog += prog_step
		parameters_bsn_file = files[1].strip()
		if parameters_bsn_file != NULL_FILE:
			self.update_file_status(prog, parameters_bsn_file)
			basin.Parameters_bsn(os.path.join(self.__dir, parameters_bsn_file), self.__version).write()

	def write_hydrology(self, start_prog, allocated_prog):
		num_files = 3
		files = self.get_file_names("hydrology", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		hydrology_hyd_file = files[0].strip()
		if hydrology_hyd_file != NULL_FILE:
			self.update_file_status(start_prog, hydrology_hyd_file)
			hydrology.Hydrology_hyd(os.path.join(self.__dir, hydrology_hyd_file), self.__version).write()

		prog += prog_step
		topography_hyd_file = files[1].strip()
		if topography_hyd_file != NULL_FILE:
			self.update_file_status(start_prog + 5, topography_hyd_file)
			hydrology.Topography_hyd(os.path.join(self.__dir, topography_hyd_file), self.__version).write()

		prog += prog_step
		field_fld_file = files[2].strip()
		if field_fld_file != NULL_FILE:
			self.update_file_status(start_prog + 5, field_fld_file)
			hydrology.Field_fld(os.path.join(self.__dir, field_fld_file), self.__version).write()

	def write_exco(self, start_prog, allocated_prog):
		num_files = 6
		files = self.get_file_names("exco", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		exco_exc_file = files[0].strip()
		if exco_exc_file != NULL_FILE:
			self.update_file_status(prog, exco_exc_file)
			exco.Exco_exc(os.path.join(self.__dir, exco_exc_file), self.__version).write()

		prog += prog_step
		exco_om_file = files[1].strip()
		if exco_om_file != NULL_FILE:
			self.update_file_status(prog, exco_om_file)
			exco.Exco_om_exc(os.path.join(self.__dir, exco_om_file), self.__version).write()

		prog += prog_step
		exco_pest_file = files[2].strip()
		if exco_pest_file != NULL_FILE:
			self.update_file_status(prog, exco_pest_file)
			exco.Exco_pest_exc(os.path.join(self.__dir, exco_pest_file), self.__version).write()

		prog += prog_step
		exco_path_file = files[3].strip()
		if exco_path_file != NULL_FILE:
			self.update_file_status(prog, exco_path_file)
			exco.Exco_path_exc(os.path.join(self.__dir, exco_path_file), self.__version).write()

		prog += prog_step
		exco_hmet_file = files[4].strip()
		if exco_hmet_file != NULL_FILE:
			self.update_file_status(prog, exco_hmet_file)
			exco.Exco_hmet_exc(os.path.join(self.__dir, exco_hmet_file), self.__version).write()

		prog += prog_step
		exco_salt_file = files[5].strip()
		if exco_salt_file != NULL_FILE:
			self.update_file_status(prog, exco_salt_file)
			exco.Exco_salt_exc(os.path.join(self.__dir, exco_salt_file), self.__version).write()

	def write_recall(self, start_prog, allocated_prog):
		num_files = 1
		files = self.get_file_names("recall", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		recall_rec_file = files[0].strip()
		if recall_rec_file != NULL_FILE:
			self.update_file_status(prog, recall_rec_file)
			recall.Recall_rec(os.path.join(self.__dir, recall_rec_file), self.__version).write()

	def write_structural(self, start_prog, allocated_prog):
		num_files = 5
		files = self.get_file_names("structural", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		tiledrain_str_file = files[0].strip()
		if tiledrain_str_file != NULL_FILE:
			self.update_file_status(prog, tiledrain_str_file)
			structural.Tiledrain_str(os.path.join(self.__dir, tiledrain_str_file), self.__version).write()

		prog += prog_step
		septic_str_file = files[1].strip()
		if septic_str_file != NULL_FILE:
			self.update_file_status(prog, septic_str_file)
			structural.Septic_str(os.path.join(self.__dir, septic_str_file), self.__version).write()

		prog += prog_step
		filterstrip_str_file = files[2].strip()
		if filterstrip_str_file != NULL_FILE:
			self.update_file_status(prog, filterstrip_str_file)
			structural.Filterstrip_str(os.path.join(self.__dir, filterstrip_str_file), self.__version).write()

		prog += prog_step
		grassedww_str_file = files[3].strip()
		if grassedww_str_file != NULL_FILE:
			self.update_file_status(prog, grassedww_str_file)
			structural.Grassedww_str(os.path.join(self.__dir, grassedww_str_file), self.__version).write()

		prog += prog_step
		bmpuser_str_file = files[4].strip()
		if bmpuser_str_file != NULL_FILE:
			self.update_file_status(prog, bmpuser_str_file)
			structural.Bmpuser_str(os.path.join(self.__dir, bmpuser_str_file), self.__version).write()

	def write_parm_db(self, start_prog, allocated_prog):
		num_files = 10
		files = self.get_file_names("hru_parm_db", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		plants_plt_file = files[0].strip()
		if plants_plt_file != NULL_FILE:
			self.update_file_status(prog, plants_plt_file)
			hru_parm_db.Plants_plt(os.path.join(self.__dir, plants_plt_file), self.__version).write()

		prog += prog_step
		fertilizer_frt_file = files[1].strip()
		if fertilizer_frt_file != NULL_FILE:
			self.update_file_status(prog, fertilizer_frt_file)
			hru_parm_db.Fertilizer_frt(os.path.join(self.__dir, fertilizer_frt_file), self.__version).write()

		prog += prog_step
		tillage_til_file = files[2].strip()
		if tillage_til_file != NULL_FILE:
			self.update_file_status(prog, tillage_til_file)
			hru_parm_db.Tillage_til(os.path.join(self.__dir, tillage_til_file), self.__version).write()

		prog += prog_step
		pesticide_pst_file = files[3].strip()
		if pesticide_pst_file != NULL_FILE:
			self.update_file_status(prog, pesticide_pst_file)
			hru_parm_db.Pesticide_pst(os.path.join(self.__dir, pesticide_pst_file), self.__version).write()

		prog += prog_step
		pathogens_pth_file = files[4].strip()
		if pathogens_pth_file != NULL_FILE:
			self.update_file_status(prog, pathogens_pth_file)
			hru_parm_db.Pathogens_pth(os.path.join(self.__dir, pathogens_pth_file), self.__version).write()

		prog += prog_step
		urban_urb_file = files[7].strip()
		if urban_urb_file != NULL_FILE:
			self.update_file_status(prog, urban_urb_file)
			hru_parm_db.Urban_urb(os.path.join(self.__dir, urban_urb_file), self.__version).write()

		prog += prog_step
		septic_sep_file = files[8].strip()
		if septic_sep_file != NULL_FILE:
			self.update_file_status(prog, septic_sep_file)
			hru_parm_db.Septic_sep(os.path.join(self.__dir, septic_sep_file), self.__version).write()

		prog += prog_step
		snow_sno_file = files[9].strip()
		if snow_sno_file != NULL_FILE:
			self.update_file_status(prog, snow_sno_file)
			hru_parm_db.Snow_sno(os.path.join(self.__dir, snow_sno_file), self.__version).write()

	def write_ops(self, start_prog, allocated_prog):
		num_files = 6
		files = self.get_file_names("ops", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		harv_ops_file = files[0].strip()
		if harv_ops_file != NULL_FILE:
			self.update_file_status(prog, harv_ops_file)
			ops.Harv_ops(os.path.join(self.__dir, harv_ops_file), self.__version).write()

		prog += prog_step
		graze_ops_file = files[1].strip()
		if graze_ops_file != NULL_FILE:
			self.update_file_status(prog, graze_ops_file)
			ops.Graze_ops(os.path.join(self.__dir, graze_ops_file), self.__version).write()

		prog += prog_step
		irr_ops_file = files[2].strip()
		if irr_ops_file != NULL_FILE:
			self.update_file_status(prog, irr_ops_file)
			ops.Irr_ops(os.path.join(self.__dir, irr_ops_file), self.__version).write()

		prog += prog_step
		chem_app_ops_file = files[3].strip()
		if chem_app_ops_file != NULL_FILE:
			self.update_file_status(prog, chem_app_ops_file)
			ops.Chem_app_ops(os.path.join(self.__dir, chem_app_ops_file), self.__version).write()

		prog += prog_step
		fire_ops_file = files[4].strip()
		if fire_ops_file != NULL_FILE:
			self.update_file_status(prog, fire_ops_file)
			ops.Fire_ops(os.path.join(self.__dir, fire_ops_file), self.__version).write()

		prog += prog_step
		sweep_ops_file = files[5].strip()
		if sweep_ops_file != NULL_FILE:
			self.update_file_status(prog, sweep_ops_file)
			ops.Sweep_ops(os.path.join(self.__dir, sweep_ops_file), self.__version).write()

	def write_lum(self, start_prog, allocated_prog):
		num_files = 5
		files = self.get_file_names("lum", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		landuse_lum_file = files[0].strip()
		if landuse_lum_file != NULL_FILE:
			self.update_file_status(prog, landuse_lum_file)
			lum.Landuse_lum(os.path.join(self.__dir, landuse_lum_file), self.__version).write()

		prog += prog_step
		management_sch_file = files[1].strip()
		if management_sch_file != NULL_FILE:
			self.update_file_status(prog, management_sch_file)
			lum.Management_sch(os.path.join(self.__dir, management_sch_file), self.__version).write()

		prog += prog_step
		cntable_lum_file = files[2].strip()
		if cntable_lum_file != NULL_FILE:
			self.update_file_status(prog, cntable_lum_file)
			lum.Cntable_lum(os.path.join(self.__dir, cntable_lum_file), self.__version).write()

		prog += prog_step
		cons_prac_lum_file = files[3].strip()
		if cons_prac_lum_file != NULL_FILE:
			self.update_file_status(prog, cons_prac_lum_file)
			lum.Cons_prac_lum(os.path.join(self.__dir, cons_prac_lum_file), self.__version).write()

		prog += prog_step
		ovn_table_lum_file = files[4].strip()
		if ovn_table_lum_file != NULL_FILE:
			self.update_file_status(prog, ovn_table_lum_file)
			lum.Ovn_table_lum(os.path.join(self.__dir, ovn_table_lum_file), self.__version).write()

	def write_chg(self, start_prog, allocated_prog):
		num_files = 9
		files = self.get_file_names("chg", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		cal_parms_cal_file = files[0].strip()
		if cal_parms_cal_file != NULL_FILE:
			self.update_file_status(prog, cal_parms_cal_file)
			change.Cal_parms_cal(os.path.join(self.__dir, cal_parms_cal_file), self.__version).write()

		prog += prog_step
		calibration_cal_file = files[1].strip()
		if calibration_cal_file != NULL_FILE:
			self.update_file_status(prog, calibration_cal_file)
			change.Calibration_cal(os.path.join(self.__dir, calibration_cal_file), self.__version).write()

		prog += prog_step
		codes_sft_file = files[2].strip()
		if codes_sft_file != NULL_FILE:
			self.update_file_status(prog, codes_sft_file)
			change.Codes_sft(os.path.join(self.__dir, codes_sft_file), self.__version).write()

		prog += prog_step
		wb_parms_sft_file = files[3].strip()
		if wb_parms_sft_file != NULL_FILE:
			self.update_file_status(prog, wb_parms_sft_file)
			change.Wb_parms_sft(os.path.join(self.__dir, wb_parms_sft_file), self.__version).write()

		prog += prog_step
		water_balance_sft_file = files[4].strip()
		if water_balance_sft_file != NULL_FILE:
			self.update_file_status(prog, water_balance_sft_file)
			change.Water_balance_sft(os.path.join(self.__dir, water_balance_sft_file), self.__version).write()

		prog += prog_step
		ch_sed_budget_sft_file = files[5].strip()
		if ch_sed_budget_sft_file != NULL_FILE:
			self.update_file_status(prog, ch_sed_budget_sft_file)
			change.Ch_sed_budget_sft(os.path.join(self.__dir, ch_sed_budget_sft_file), self.__version).write()

		prog += prog_step
		chsed_parms_sft_file = files[6].strip()
		if chsed_parms_sft_file != NULL_FILE:
			self.update_file_status(prog, chsed_parms_sft_file)
			change.Ch_sed_parms_sft(os.path.join(self.__dir, chsed_parms_sft_file), self.__version).write()

		prog += prog_step
		plant_parms_sft_file = files[7].strip()
		if plant_parms_sft_file != NULL_FILE:
			self.update_file_status(prog, plant_parms_sft_file)
			change.Plant_parms_sft(os.path.join(self.__dir, plant_parms_sft_file), self.__version).write()

		prog += prog_step
		plant_gro_sft_file = files[8].strip()
		if plant_gro_sft_file != NULL_FILE:
			self.update_file_status(prog, plant_gro_sft_file)
			change.Plant_gro_sft(os.path.join(self.__dir, plant_gro_sft_file), self.__version).write()

	def write_init(self, start_prog, allocated_prog):
		num_files = 2
		files = self.get_file_names("init", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		initial_plt_file = files[0].strip()
		if initial_plt_file != NULL_FILE:
			self.update_file_status(start_prog, initial_plt_file)
			init.Plant_ini(os.path.join(self.__dir, initial_plt_file), self.__version).write()

		prog += prog_step
		soil_plant_ini_file = files[1].strip()
		if soil_plant_ini_file != NULL_FILE:
			self.update_file_status(prog, soil_plant_ini_file)
			init.Soil_plant_ini(os.path.join(self.__dir, soil_plant_ini_file), self.__version).write()

		prog += prog_step
		om_water_ini_file = files[2].strip()
		if om_water_ini_file != NULL_FILE:
			self.update_file_status(prog, om_water_ini_file)
			init.Om_water_ini(os.path.join(self.__dir, om_water_ini_file), self.__version).write()

		prog += prog_step
		pest_hru_ini_file = files[3].strip()
		if pest_hru_ini_file != NULL_FILE:
			self.update_file_status(prog, pest_hru_ini_file)
			init.Pest_hru_ini(os.path.join(self.__dir, pest_hru_ini_file), self.__version).write()

		prog += prog_step
		pest_water_ini_file = files[4].strip()
		if pest_water_ini_file != NULL_FILE:
			self.update_file_status(prog, pest_water_ini_file)
			init.Pest_water_ini(os.path.join(self.__dir, pest_water_ini_file), self.__version).write()

		prog += prog_step
		path_hru_ini_file = files[5].strip()
		if path_hru_ini_file != NULL_FILE:
			self.update_file_status(prog, path_hru_ini_file)
			init.Path_hru_ini(os.path.join(self.__dir, path_hru_ini_file), self.__version).write()

		prog += prog_step
		path_water_ini_file = files[6].strip()
		if path_water_ini_file != NULL_FILE:
			self.update_file_status(prog, path_water_ini_file)
			init.Path_water_ini(os.path.join(self.__dir, path_water_ini_file), self.__version).write()

	def write_soils(self, start_prog, allocated_prog):
		num_files = 3
		files = self.get_file_names("soils", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		nutrients_sol_file = files[1].strip()
		if nutrients_sol_file != NULL_FILE:
			self.update_file_status(prog, nutrients_sol_file)
			soils.Nutrients_sol(os.path.join(self.__dir, nutrients_sol_file), self.__version).write()

		prog += prog_step
		soils_sol_file = files[0].strip()
		if soils_sol_file != NULL_FILE:
			self.update_file_status(prog, soils_sol_file)
			soils.Soils_sol(os.path.join(self.__dir, soils_sol_file), self.__version).write()

		if self.__is_lte:
			prog += prog_step
			soils_lte_sol_file = files[2].strip()
			if soils_lte_sol_file != NULL_FILE:
				self.update_file_status(prog, soils_lte_sol_file)
				soils.Soils_lte_sol(os.path.join(self.__dir, soils_lte_sol_file), self.__version).write()

	def write_decision_table(self, start_prog, allocated_prog):
		num_files = 4
		files = self.get_file_names("decision_table", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		lum_dtl_file = files[0].strip()
		if lum_dtl_file != NULL_FILE:
			self.update_file_status(start_prog, lum_dtl_file)
			decision_table.D_table_dtl(os.path.join(self.__dir, lum_dtl_file), self.__version).write()

		prog += prog_step
		res_rel_dtl_file = files[1].strip()
		if res_rel_dtl_file != NULL_FILE:
			self.update_file_status(prog, res_rel_dtl_file)
			decision_table.D_table_dtl(os.path.join(self.__dir, res_rel_dtl_file), self.__version).write()

		prog += prog_step
		scen_lu_dtl_file = files[2].strip()
		if scen_lu_dtl_file != NULL_FILE:
			self.update_file_status(prog, scen_lu_dtl_file)
			decision_table.D_table_dtl(os.path.join(self.__dir, scen_lu_dtl_file), self.__version).write()

		prog += prog_step
		flo_con_dtl_file = files[3].strip()
		if flo_con_dtl_file != NULL_FILE:
			self.update_file_status(prog, flo_con_dtl_file)
			decision_table.D_table_dtl(os.path.join(self.__dir, flo_con_dtl_file), self.__version).write()

	def write_regions(self, start_prog, allocated_prog):
		num_files = 17
		files = self.get_file_names("regions", num_files)

		prog_step = round(allocated_prog / num_files)
		prog = start_prog

		ls_unit_ele_file = files[0].strip()
		if ls_unit_ele_file != NULL_FILE:
			self.update_file_status(start_prog, ls_unit_ele_file)
			regions.Ls_unit_ele(os.path.join(self.__dir, ls_unit_ele_file), self.__version).write()

		prog += prog_step
		ls_unit_def_file = files[1].strip()
		if ls_unit_def_file != NULL_FILE:
			self.update_file_status(start_prog, ls_unit_def_file)
			regions.Ls_unit_def(os.path.join(self.__dir, ls_unit_def_file), self.__version).write()

		prog += prog_step
		aqu_catunit_ele_file = files[8].strip()
		if aqu_catunit_ele_file != NULL_FILE:
			self.update_file_status(start_prog, aqu_catunit_ele_file)
			regions.Aqu_catunit_ele(os.path.join(self.__dir, aqu_catunit_ele_file), self.__version).write()

	def update_file_status(self, prog, file_name):
		self.emit_progress(prog, "Writing {name}...".format(name=file_name))


if __name__ == '__main__':
	sys.stdout = Unbuffered(sys.stdout)
	parser = argparse.ArgumentParser(description="Write SWAT+ text files from database.")
	parser.add_argument("project_db_file", type=str, help="full path of project SQLite database file")
	args = parser.parse_args()

	api = WriteFiles(args.project_db_file)
	api.write()
