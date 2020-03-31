from .base import BaseFileModel, FileColumn as col
from helpers import utils

from peewee import *

import database.project.config as db
from database.project import simulation, climate, connect, channel, reservoir, routing_unit, hru, dr, aquifer, link, basin, hydrology, exco, recall, structural, hru_parm_db, ops, lum, change, init, soils, decision_table, regions, config


class File_cio(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version
	
	def read(self):
		raise NotImplementedError('Reading not implemented yet.')
	
	def write(self):
		is_lte = False
		c = config.Project_config.get_or_none()
		if c is not None:
			is_lte = c.is_lte

		classes = db.File_cio_classification.select().order_by(db.File_cio_classification.id)
		files = db.File_cio.select().order_by(db.File_cio.order_in_class)
		query = prefetch(classes, files)
		
		null_str = utils.NULL_STR

		with open(self.file_name, 'w') as file:
			self.write_meta_line(file)
			classifications = self.get_classifications(is_lte)

			for row in query:
				utils.write_string(file, row.name, direction="left")
				
				conditions = classifications.get(row.name, {})
				
				for f in row.files:
					file_name = f.file_name if conditions.get(f.order_in_class, False) else null_str
					
					if file_name is None or file_name == "":
						file_name = null_str

					utils.write_string(file, file_name, direction="left")

				if len(row.files) < 1:
					utils.write_string(file, null_str, direction="left")

				file.write("\n")

	def get_classifications(self, is_lte=False):
		sim_conditions = {
			1: True,
			2: True,
			3: simulation.Object_prt.select().count() > 0,
			4: True,
			5: simulation.Constituents_cs.select().count() > 0
		}
		
		basin_conditions = {
			1: basin.Codes_bsn.select().count() > 0,
			2: basin.Parameters_bsn.select().count() > 0
		}
		
		climate_conditions = {
			1: True,
			2: True,
			3: climate.Weather_file.select().where(climate.Weather_file.type == "wind-dir").count() > 0,
			4: climate.Weather_file.select().where(climate.Weather_file.type == "pcp").count() > 0,
			5: climate.Weather_file.select().where(climate.Weather_file.type == "tmp").count() > 0,
			6: climate.Weather_file.select().where(climate.Weather_file.type == "slr").count() > 0,
			7: climate.Weather_file.select().where(climate.Weather_file.type == "hmd").count() > 0,
			8: climate.Weather_file.select().where(climate.Weather_file.type == "wnd").count() > 0,
			9: climate.Atmo_cli.select().count() > 0
		}
		
		connect_conditions = {
			1: connect.Hru_con.select().count() > 0,
			2: connect.Hru_lte_con.select().count() > 0,
			3: connect.Rout_unit_con.select().count() > 0,
			4: connect.Modflow_con.select().count() > 0,
			5: connect.Aquifer_con.select().count() > 0,
			6: connect.Aquifer2d_con.select().count() > 0,
			7: connect.Channel_con.select().count() > 0,
			8: connect.Reservoir_con.select().count() > 0,
			9: connect.Recall_con.select().count() > 0,
			10: connect.Exco_con.select().count() > 0,
			11: connect.Delratio_con.select().count() > 0,
			12: connect.Outlet_con.select().count() > 0,
			13: connect.Chandeg_con.select().count() > 0
		}
		
		channel_conditions = {
			1: channel.Initial_cha.select().count() > 0,
			2: channel.Channel_cha.select().count() > 0,
			3: channel.Hydrology_cha.select().count() > 0,
			4: channel.Sediment_cha.select().count() > 0,
			5: channel.Nutrients_cha.select().count() > 0,
			6: channel.Channel_lte_cha.select().count() > 0,
			7: channel.Hyd_sed_lte_cha.select().count() > 0,
			8: False
		}
		
		reservoir_conditions = {
			1: reservoir.Initial_res.select().count() > 0,
			2: reservoir.Reservoir_res.select().count() > 0,
			3: reservoir.Hydrology_res.select().count() > 0,
			4: reservoir.Sediment_res.select().count() > 0,
			5: reservoir.Nutrients_res.select().count() > 0,
			6: reservoir.Weir_res.select().count() > 0,
			7: reservoir.Wetland_wet.select().count() > 0,
			8: reservoir.Hydrology_wet.select().count() > 0
		}
		
		rout_unit_conditions = {
			1: connect.Rout_unit_ele.select().count() > 0,
			2: connect.Rout_unit_ele.select().count() > 0,
			3: routing_unit.Rout_unit_rtu.select().count() > 0,
			4: routing_unit.Rout_unit_dr.select().count() > 0
		}
		
		hru_conditions = {
			1: hru.Hru_data_hru.select().count() > 0,
			2: hru.Hru_lte_hru.select().count() > 0
		}
		
		exco_conditions = {
			1: exco.Exco_exc.select().count() > 0 or recall.Recall_rec.select().where(recall.Recall_rec.rec_typ == 4).count() > 0,
			2: exco.Exco_om_exc.select().count() > 0 or recall.Recall_rec.select().where(recall.Recall_rec.rec_typ == 4).count() > 0,
			3: exco.Exco_pest_exc.select().count() > 0,
			4: exco.Exco_path_exc.select().count() > 0,
			5: exco.Exco_hmet_exc.select().count() > 0,
			6: exco.Exco_salt_exc.select().count() > 0
		}
		
		recall_conditions = {
			1: recall.Recall_rec.select().count() > 0
		}
		
		dr_conditions = {
			1: dr.Delratio_del.select().count() > 0,
			2: dr.Dr_om_del.select().count() > 0,
			3: dr.Dr_pest_del.select().count() > 0,
			4: dr.Dr_path_del.select().count() > 0,
			5: dr.Dr_hmet_del.select().count() > 0,
			6: dr.Dr_salt_del.select().count() > 0
		}
		
		aquifer_conditions = {
			1: aquifer.Initial_aqu.select().count() > 0,
			2: aquifer.Aquifer_aqu.select().count() > 0
		}
		
		link_conditions = {
			1: link.Chan_surf_lin.select().count() > 0,
			2: False #connect.Aquifer_con.select().count() > 0
		}
		
		hydrology_conditions = {
			1: hydrology.Hydrology_hyd.select().count() > 0,
			2: hydrology.Topography_hyd.select().count() > 0,
			3: hydrology.Field_fld.select().count() > 0
		}
		
		structural_conditions = {
			1: structural.Tiledrain_str.select().count() > 0,
			2: structural.Septic_str.select().count() > 0,
			3: structural.Filterstrip_str.select().count() > 0,
			4: structural.Grassedww_str.select().count() > 0,
			5: structural.Bmpuser_str.select().count() > 0
		}
		
		parm_db_conditions = {
			1: hru_parm_db.Plants_plt.select().count() > 0,
			2: hru_parm_db.Fertilizer_frt.select().count() > 0,
			3: hru_parm_db.Tillage_til.select().count() > 0,
			4: hru_parm_db.Pesticide_pst.select().count() > 0,
			5: hru_parm_db.Pathogens_pth.select().count() > 0,
			6: hru_parm_db.Metals_mtl.select().count() > 0,
			7: hru_parm_db.Salts_slt.select().count() > 0,
			8: hru_parm_db.Urban_urb.select().count() > 0,
			9: hru_parm_db.Septic_sep.select().count() > 0,
			10: hru_parm_db.Snow_sno.select().count() > 0
		}
		
		ops_conditions = {
			1: ops.Harv_ops.select().count() > 0,
			2: ops.Graze_ops.select().count() > 0,
			3: ops.Irr_ops.select().count() > 0,
			4: ops.Chem_app_ops.select().count() > 0,
			5: ops.Fire_ops.select().count() > 0,
			6: ops.Sweep_ops.select().count() > 0
		}
		
		lum_conditions = {
			1: lum.Landuse_lum.select().count() > 0,
			2: lum.Management_sch.select().count() > 0,
			3: lum.Cntable_lum.select().count() > 0,
			4: lum.Cons_prac_lum.select().count() > 0,
			5: lum.Ovn_table_lum.select().count() > 0
		}
		
		chg_conditions = {
			1: change.Cal_parms_cal.select().count() > 0,
			2: change.Calibration_cal.select().count() > 0,
			3: change.Codes_sft.select().count() > 0,
			4: change.Wb_parms_sft.select().count() > 0,
			5: change.Water_balance_sft.select().count() > 0,
			6: change.Ch_sed_budget_sft.select().count() > 0,
			7: change.Ch_sed_parms_sft.select().count() > 0,
			8: change.Plant_parms_sft.select().count() > 0,
			9: change.Plant_gro_sft.select().count() > 0
		}
		
		init_conditions = {
			1: init.Plant_ini.select().count() > 0,
			2: init.Soil_plant_ini.select().count() > 0,
			3: init.Om_water_ini.select().count() > 0,
			4: init.Pest_hru_ini.select().count() > 0,
			5: init.Pest_water_ini.select().count() > 0,
			6: init.Path_hru_ini.select().count() > 0,
			7: init.Path_water_ini.select().count() > 0,
			8: init.Hmet_hru_ini.select().count() > 0,
			9: init.Hmet_water_ini.select().count() > 0,
			10: init.Salt_hru_ini.select().count() > 0,
			11: init.Salt_water_ini.select().count() > 0
		}
		
		soils_conditions = {
			1: not is_lte and soils.Soils_sol.select().count() > 0,
			2: soils.Nutrients_sol.select().count() > 0,
			3: is_lte and soils.Soils_lte_sol.select().count() > 0
		}
		
		decision_table_conditions = {
			1: True,
			2: True,
			3: True,
			4: True
		}
		
		regions_conditions = {
			1: regions.Ls_unit_ele.select().count() > 0,
			2: regions.Ls_unit_def.select().count() > 0,
			3: regions.Ls_reg_ele.select().count() > 0,
			4: regions.Ls_reg_def.select().count() > 0,
			5: False,
			6: regions.Ch_catunit_ele.select().count() > 0,
			7: regions.Ch_catunit_def.select().count() > 0,
			8: regions.Ch_reg_def.select().count() > 0,
			9: connect.Aquifer_con.select().count() > 0,
			10: regions.Aqu_catunit_def.select().count() > 0,
			11: regions.Aqu_reg_def.select().count() > 0,
			12: regions.Res_catunit_ele.select().count() > 0,
			13: regions.Res_catunit_def.select().count() > 0,
			14: regions.Res_reg_def.select().count() > 0,
			15: regions.Rec_catunit_ele.select().count() > 0,
			16: regions.Rec_catunit_def.select().count() > 0,
			17: regions.Rec_reg_def.select().count() > 0
		}

		classifications = {
			"simulation": sim_conditions,
			"basin": basin_conditions,
			"climate": climate_conditions,
			"connect": connect_conditions,
			"channel": channel_conditions,
			"reservoir": reservoir_conditions,
			"routing_unit": rout_unit_conditions,
			"hru": hru_conditions,
			"exco": exco_conditions,
			"recall": recall_conditions,
			"dr": dr_conditions,
			"aquifer": aquifer_conditions,
			"link": link_conditions,
			"hydrology": hydrology_conditions,
			"structural": structural_conditions,
			"hru_parm_db": parm_db_conditions,
			"ops": ops_conditions,
			"lum": lum_conditions,
			"chg": chg_conditions,
			"init": init_conditions,
			"soils": soils_conditions,
			"decision_table": decision_table_conditions,
			"regions": regions_conditions
		}

		return classifications
