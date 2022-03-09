from peewee import *
from . import base, config, simulation, climate, link, channel, reservoir, dr, exco, recall, hydrology, routing_unit, aquifer, \
	basin, hru_parm_db, structural, ops, decision_table, init, lum, soils, \
	change, regions, hru, connect, gis
from database import lib
from database.datasets import base as datasets_base, definitions as dataset_defs, decision_table as dataset_dts
import os, os.path
from shutil import copyfile, copy
import time

class SetupProjectDatabase():
	@staticmethod
	def init(project_db:str, datasets_db:str = None):
		base.db.init(project_db, pragmas={'journal_mode': 'off'})
		if datasets_db:
			datasets_base.db.init(datasets_db, pragmas={'journal_mode': 'off'})

	@staticmethod
	def rollback(project_db:str, rollback_db:str):
		base_path = os.path.dirname(project_db)
		rel_project_db = os.path.relpath(project_db, base_path)
		filename, file_extension = os.path.splitext(rel_project_db)
		err_filename = filename + '_error_' + time.strftime('%Y%m%d-%H%M%S') + file_extension
		err_dir = os.path.join(base_path, 'DatabaseErrors')
		if not os.path.exists(err_dir):
			os.makedirs(err_dir)
		
		copyfile(project_db, os.path.join(err_dir, err_filename))
		copy(rollback_db, project_db)
		SetupProjectDatabase.init(project_db)

	@staticmethod
	def create_tables():
		base.db.create_tables([config.Project_config, config.File_cio_classification, config.File_cio])
		base.db.create_tables([basin.Codes_bsn, basin.Parameters_bsn])
		base.db.create_tables([simulation.Time_sim, simulation.Print_prt, simulation.Print_prt_aa_int, simulation.Print_prt_object, simulation.Object_prt, simulation.Object_cnt, simulation.Constituents_cs])
		base.db.create_tables([climate.Weather_wgn_cli, climate.Weather_wgn_cli_mon, climate.Weather_sta_cli, climate.Weather_file, climate.Wind_dir_cli, climate.Atmo_cli, climate.Atmo_cli_sta, climate.Atmo_cli_sta_value])
		base.db.create_tables([link.Chan_aqu_lin, link.Chan_aqu_lin_ob, link.Chan_surf_lin, link.Chan_surf_lin_ob])
		base.db.create_tables([channel.Initial_cha, channel.Hydrology_cha, channel.Sediment_cha, channel.Nutrients_cha, channel.Channel_cha, channel.Hyd_sed_lte_cha, channel.Channel_lte_cha])
		base.db.create_tables([reservoir.Initial_res, reservoir.Hydrology_res, reservoir.Sediment_res, reservoir.Nutrients_res, reservoir.Weir_res, reservoir.Reservoir_res, reservoir.Hydrology_wet, reservoir.Wetland_wet])
		base.db.create_tables([dr.Dr_om_del, dr.Dr_pest_del, dr.Dr_pest_col, dr.Dr_pest_val, dr.Dr_path_del, dr.Dr_path_col, dr.Dr_path_val, dr.Dr_hmet_del, dr.Dr_hmet_col, dr.Dr_hmet_val, dr.Dr_salt_del, dr.Dr_salt_col, dr.Dr_salt_val, dr.Delratio_del])
		base.db.create_tables([exco.Exco_om_exc, exco.Exco_pest_exc, exco.Exco_path_exc, exco.Exco_hmet_exc, exco.Exco_salt_exc, exco.Exco_exc])
		base.db.create_tables([exco.Exco_pest_col, exco.Exco_pest_val, exco.Exco_path_col, exco.Exco_path_val, exco.Exco_hmet_col, exco.Exco_hmet_val, exco.Exco_salt_col, exco.Exco_salt_val])
		base.db.create_tables([recall.Recall_rec, recall.Recall_dat])
		base.db.create_tables([hydrology.Topography_hyd, hydrology.Hydrology_hyd, hydrology.Field_fld])
		base.db.create_tables([routing_unit.Rout_unit_dr, routing_unit.Rout_unit_rtu])
		base.db.create_tables([aquifer.Initial_aqu, aquifer.Aquifer_aqu])
		base.db.create_tables([hru_parm_db.Plants_plt, hru_parm_db.Fertilizer_frt, hru_parm_db.Tillage_til, hru_parm_db.Pesticide_pst, hru_parm_db.Pathogens_pth, hru_parm_db.Metals_mtl, hru_parm_db.Salts_slt, hru_parm_db.Urban_urb, hru_parm_db.Septic_sep, hru_parm_db.Snow_sno])
		base.db.create_tables([structural.Septic_str, structural.Bmpuser_str, structural.Filterstrip_str, structural.Grassedww_str, structural.Tiledrain_str])
		base.db.create_tables([ops.Graze_ops, ops.Harv_ops, ops.Irr_ops, ops.Chem_app_ops, ops.Fire_ops, ops.Sweep_ops])
		base.db.create_tables([decision_table.D_table_dtl, decision_table.D_table_dtl_cond, decision_table.D_table_dtl_cond_alt, decision_table.D_table_dtl_act, decision_table.D_table_dtl_act_out])
		base.db.create_tables([init.Plant_ini, init.Plant_ini_item, init.Om_water_ini, 
								init.Pest_hru_ini, init.Pest_hru_ini_item, init.Pest_water_ini, init.Pest_water_ini_item, 
								init.Path_hru_ini, init.Path_hru_ini_item, init.Path_water_ini, init.Path_water_ini_item, 
								init.Hmet_hru_ini, init.Hmet_hru_ini_item, init.Hmet_water_ini, init.Hmet_water_ini_item, 
								init.Salt_hru_ini, init.Salt_hru_ini_item, init.Salt_water_ini, init.Salt_water_ini_item, 
								init.Soil_plant_ini])
		base.db.create_tables([lum.Management_sch, lum.Management_sch_auto, lum.Management_sch_op, lum.Cntable_lum, lum.Cons_prac_lum, lum.Ovn_table_lum, lum.Landuse_lum])
		base.db.create_tables([soils.Soils_sol, soils.Soils_sol_layer, soils.Nutrients_sol, soils.Soils_lte_sol])
		base.db.create_tables([change.Cal_parms_cal, change.Calibration_cal, change.Calibration_cal_cond, change.Calibration_cal_elem, change.Codes_sft, change.Wb_parms_sft, change.Water_balance_sft, change.Water_balance_sft_item, change.Plant_parms_sft, change.Plant_parms_sft_item, change.Plant_gro_sft, change.Plant_gro_sft_item, change.Ch_sed_parms_sft, change.Ch_sed_budget_sft, change.Ch_sed_budget_sft_item])

		base.db.create_tables([regions.Ls_unit_def, regions.Ls_unit_ele,
							   regions.Ls_reg_def, regions.Ls_reg_ele,
							   regions.Ch_catunit_ele, regions.Ch_catunit_def, regions.Ch_catunit_def_elem, regions.Ch_reg_def, regions.Ch_reg_def_elem,
							   regions.Aqu_catunit_ele, regions.Aqu_catunit_def, regions.Aqu_catunit_def_elem, regions.Aqu_reg_def, regions.Aqu_reg_def_elem,
							   regions.Res_catunit_ele, regions.Res_catunit_def, regions.Res_catunit_def_elem, regions.Res_reg_def, regions.Res_reg_def_elem,
							   regions.Rec_catunit_ele, regions.Rec_catunit_def, regions.Rec_catunit_def_elem, regions.Rec_reg_def, regions.Rec_reg_def_elem])

		base.db.create_tables([hru.Hru_lte_hru, hru.Hru_data_hru])

		base.db.create_tables([connect.Hru_con, connect.Hru_con_out,
							   connect.Hru_lte_con, connect.Hru_lte_con_out,
							   connect.Rout_unit_con, connect.Rout_unit_con_out,
							   connect.Modflow_con, connect.Modflow_con_out,
							   connect.Aquifer_con, connect.Aquifer_con_out,
							   connect.Aquifer2d_con, connect.Aquifer2d_con_out,
							   connect.Channel_con, connect.Channel_con_out,
							   connect.Reservoir_con, connect.Reservoir_con_out,
							   connect.Recall_con, connect.Recall_con_out,
							   connect.Exco_con, connect.Exco_con_out,
							   connect.Delratio_con, connect.Delratio_con_out,
							   connect.Outlet_con, connect.Outlet_con_out,
							   connect.Chandeg_con, connect.Chandeg_con_out])

		base.db.create_tables([connect.Rout_unit_ele])
		base.db.create_tables([gis.Gis_channels, gis.Gis_subbasins, gis.Gis_hrus, gis.Gis_lsus, gis.Gis_water, gis.Gis_points, gis.Gis_routing])

	@staticmethod
	def initialize_data(project_name, is_lte=False, overwrite_plants=False):
		# Set up default simulation data
		simulation.Object_cnt.get_or_create_default(project_name=project_name)
		simulation.Time_sim.get_or_create_default()

		datasets_db_name = datasets_base.db.database
		project_db_name = base.db.database

		if basin.Codes_bsn.select().count() < 1:
			lib.copy_table('codes_bsn', datasets_db_name, project_db_name)

		if basin.Parameters_bsn.select().count() < 1:
			lib.copy_table('parameters_bsn', datasets_db_name, project_db_name)

		if overwrite_plants:
			base.db.drop_tables([hru_parm_db.Plants_plt])
			base.db.create_tables([hru_parm_db.Plants_plt])
		
		if hru_parm_db.Plants_plt.select().count() < 1:
			lib.copy_table('plants_plt', datasets_db_name, project_db_name)

		if hru_parm_db.Urban_urb.select().count() < 1:
			lib.copy_table('urban_urb', datasets_db_name, project_db_name)

		if not is_lte:	
			if hru_parm_db.Fertilizer_frt.select().count() < 1:
				lib.copy_table('fertilizer_frt', datasets_db_name, project_db_name)

			if hru_parm_db.Septic_sep.select().count() < 1:
				lib.copy_table('septic_sep', datasets_db_name, project_db_name)

			if hru_parm_db.Snow_sno.select().count() < 1:
				lib.copy_table('snow_sno', datasets_db_name, project_db_name)

			if hru_parm_db.Tillage_til.select().count() < 1:
				lib.copy_table('tillage_til', datasets_db_name, project_db_name)

			if hru_parm_db.Pesticide_pst.select().count() < 1:
				lib.copy_table('pesticide_pst', datasets_db_name, project_db_name)

			if lum.Cntable_lum.select().count() < 1:
				lib.copy_table('cntable_lum', datasets_db_name, project_db_name)

			if lum.Ovn_table_lum.select().count() < 1:
				lib.copy_table('ovn_table_lum', datasets_db_name, project_db_name)

			if lum.Cons_prac_lum.select().count() < 1:
				lib.copy_table('cons_prac_lum', datasets_db_name, project_db_name)

			if ops.Graze_ops.select().count() < 1:
				lib.copy_table('graze_ops', datasets_db_name, project_db_name)

			if ops.Harv_ops.select().count() < 1:
				lib.copy_table('harv_ops', datasets_db_name, project_db_name)

			if ops.Fire_ops.select().count() < 1:
				lib.copy_table('fire_ops', datasets_db_name, project_db_name)

			if ops.Irr_ops.select().count() < 1:
				lib.copy_table('irr_ops', datasets_db_name, project_db_name)

			if ops.Sweep_ops.select().count() < 1:
				lib.copy_table('sweep_ops', datasets_db_name, project_db_name)

			if ops.Chem_app_ops.select().count() < 1:
				lib.copy_table('chem_app_ops', datasets_db_name, project_db_name)

			if structural.Bmpuser_str.select().count() < 1:
				lib.copy_table('bmpuser_str', datasets_db_name, project_db_name)

			if structural.Filterstrip_str.select().count() < 1:
				lib.copy_table('filterstrip_str', datasets_db_name, project_db_name)

			if structural.Grassedww_str.select().count() < 1:
				lib.copy_table('grassedww_str', datasets_db_name, project_db_name)

			if structural.Septic_str.select().count() < 1:
				lib.copy_table('septic_str', datasets_db_name, project_db_name)

			if structural.Tiledrain_str.select().count() < 1:
				lib.copy_table('tiledrain_str', datasets_db_name, project_db_name)

			if change.Cal_parms_cal.select().count() < 1:
				lib.copy_table('cal_parms_cal', datasets_db_name, project_db_name)

		if is_lte and soils.Soils_lte_sol.select().count() < 1:
			lib.copy_table('soils_lte_sol', datasets_db_name, project_db_name)

		if decision_table.D_table_dtl.select().count() < 1:
			if not is_lte:
				"""lib.copy_table('d_table_dtl', datasets_db_name, project_db_name, include_id=True)
				lib.copy_table('d_table_dtl_cond', datasets_db_name, project_db_name, include_id=True)
				lib.copy_table('d_table_dtl_cond_alt', datasets_db_name, project_db_name, include_id=True)
				lib.copy_table('d_table_dtl_act', datasets_db_name, project_db_name, include_id=True)
				lib.copy_table('d_table_dtl_act_out', datasets_db_name, project_db_name, include_id=True)"""
				valid_res_tables = ['corps_med_res1', 'corps_med_res', 'wetland', 'lrew_sm_res']
				query = dataset_dts.D_table_dtl.select().where((dataset_dts.D_table_dtl.file_name != 'scen_lu.dtl') & ((dataset_dts.D_table_dtl.file_name != 'res_rel.dtl') | (dataset_dts.D_table_dtl.name.in_(valid_res_tables))))
			else:
				dt_names = ['pl_grow_sum', 'pl_end_sum', 'pl_grow_win', 'pl_end_win']
				query = dataset_dts.D_table_dtl.select().where(dataset_dts.D_table_dtl.name << dt_names)

			for dt in query:
				d_id = decision_table.D_table_dtl.insert(name=dt.name, file_name=dt.file_name).execute()
				for c in dt.conditions:
					c_id = decision_table.D_table_dtl_cond.insert(
						d_table=d_id,
						var=c.var,
						obj=c.obj,
						obj_num=c.obj_num,
						lim_var=c.lim_var,
						lim_op=c.lim_op,
						lim_const=c.lim_const
					).execute()
					for ca in c.alts:
						decision_table.D_table_dtl_cond_alt.insert(cond=c_id, alt=ca.alt).execute()

				for a in dt.actions:
					a_id = decision_table.D_table_dtl_act.insert(
						d_table=d_id,
						act_typ=a.act_typ,
						obj=a.obj,
						obj_num=a.obj_num,
						name=a.name,
						option=a.option,
						const=a.const,
						const2=a.const2,
						fp=a.fp
					).execute()
					for ao in a.outcomes:
						decision_table.D_table_dtl_act_out.insert(act=a_id, outcome=ao.outcome).execute()


		if not is_lte and lum.Management_sch.select().count() < 1:
			lib.copy_table('management_sch', datasets_db_name, project_db_name, include_id=True)
			lib.copy_table('management_sch_auto', datasets_db_name, project_db_name, include_id=True)
			lib.copy_table('management_sch_op', datasets_db_name, project_db_name, include_id=True)

		if config.File_cio_classification.select().count() < 1:
			#lib.copy_table('file_cio_classification', datasets_db_name, project_db_name)
			class_query = dataset_defs.File_cio_classification.select()
			if class_query.count() > 0:
				classes = []
				for f in class_query:
					cl = {
						'name': f.name
					}
					classes.append(cl)

				lib.bulk_insert(base.db, config.File_cio_classification, classes)

			file_cio_query = dataset_defs.File_cio.select()
			if file_cio_query.count() > 0:
				file_cios = []
				for f in file_cio_query:
					file_cio = {
						'classification': f.classification.id,
						'order_in_class': f.order_in_class,
						'file_name': f.default_file_name
					}
					file_cios.append(file_cio)

				lib.bulk_insert(base.db, config.File_cio, file_cios)

		if simulation.Print_prt.select().count() < 1:
			lib.copy_table('print_prt', datasets_db_name, project_db_name)

		print_prt_id = simulation.Print_prt.select().first().id
		print_obj_query = dataset_defs.Print_prt_object.select().order_by(dataset_defs.Print_prt_object.id)

		if print_obj_query.count() > 0:
			print_objs = []
			for p in print_obj_query:
				try:
					existing = simulation.Print_prt_object.get(simulation.Print_prt_object.name == p.name)
				except simulation.Print_prt_object.DoesNotExist:
					print_obj = {
						'print_prt': print_prt_id,
						'name': p.name,
						'daily': p.daily,
						'monthly': p.monthly,
						'yearly': p.yearly,
						'avann': p.avann
					}
					print_objs.append(print_obj)

			lib.bulk_insert(base.db, simulation.Print_prt_object, print_objs)
