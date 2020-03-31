from peewee import *
from . import base, definitions, hru_parm_db, lum, ops, structural, decision_table, basin, climate, soils, init, change
from fileio import hru_parm_db as files_parmdb
from fileio import lum as files_lum
from fileio import ops as files_ops
from fileio import structural as files_str
from fileio import decision_table as files_dtable
from fileio import basin as files_basin
from fileio import change as files_change
from fileio import soils as files_soils
from database import lib as db_lib

source_data_path = "../data/source-data/"


def val_exists(val):
	return val is not None and val != ''


class SetupDatasetsDatabase():
	@staticmethod
	def init(datasets_db: str = None):
		base.db.init(datasets_db, pragmas={'journal_mode': 'off'})
	
	@staticmethod
	def create_tables():
		base.db.create_tables([definitions.Tropical_bounds, definitions.Version, definitions.File_cio_classification, definitions.File_cio, definitions.Print_prt, definitions.Print_prt_object])
		base.db.create_tables([hru_parm_db.Plants_plt, hru_parm_db.Fertilizer_frt, hru_parm_db.Tillage_til, hru_parm_db.Pesticide_pst, hru_parm_db.Pathogens_pth, hru_parm_db.Urban_urb, hru_parm_db.Septic_sep, hru_parm_db.Snow_sno, soils.Soil, soils.Soil_layer, soils.Soils_lte_sol, climate.Wgn, climate.Wgn_mon])
		base.db.create_tables([basin.Codes_bsn, basin.Parameters_bsn])
		base.db.create_tables([decision_table.D_table_dtl, decision_table.D_table_dtl_cond, decision_table.D_table_dtl_cond_alt, decision_table.D_table_dtl_act, decision_table.D_table_dtl_act_out])
		base.db.create_tables([ops.Graze_ops, ops.Harv_ops, ops.Fire_ops, ops.Irr_ops, ops.Sweep_ops, ops.Chem_app_ops])
		base.db.create_tables([structural.Bmpuser_str, structural.Filterstrip_str, structural.Grassedww_str, structural.Septic_str, structural.Tiledrain_str])
		base.db.create_tables([lum.Cntable_lum, lum.Ovn_table_lum, lum.Cons_prac_lum, lum.Management_sch, lum.Management_sch_auto, lum.Management_sch_op, lum.Landuse_lum])
		base.db.create_tables([init.Plant_ini, init.Plant_ini_item])
		base.db.create_tables([change.Cal_parms_cal])

	@staticmethod
	def check_version(datasets_db, editor_version, compatibility_versions=['1.1.0', '1.1.1', '1.1.2', '1.2.0']):
		conn = db_lib.open_db(datasets_db)
		if db_lib.exists_table(conn, 'version'):
			SetupDatasetsDatabase.init(datasets_db)
			m = definitions.Version.get()
			if not (m.value in compatibility_versions or m.value == editor_version):
				return 'Please update your swatplus_datasets.sqlite to the most recent version: {new_version}. Your version is {current_version}.'.format(new_version=editor_version, current_version=m.value)
		else:
			return 'Please update your swatplus_datasets.sqlite to the most recent version, {new_version}, before creating your project.'.format(new_version=editor_version)

		return None
	
	@staticmethod
	def initialize_data(version: str = None):
		codes = [
			{'table': 'connect', 'variable': 'obj_typ', 'code': 'hru', 'description': 'hru'},
			{'table': 'connect', 'variable': 'obj_typ', 'code': 'hlt', 'description': 'hru_lte'},
			{'table': 'connect', 'variable': 'obj_typ', 'code': 'ru', 'description': 'routing unit'},
			{'table': 'connect', 'variable': 'obj_typ', 'code': 'mfl', 'description': 'modflow'},
			{'table': 'connect', 'variable': 'obj_typ', 'code': 'aqu', 'description': 'aquifer'},
			{'table': 'connect', 'variable': 'obj_typ', 'code': 'cha', 'description': 'channel'},
			{'table': 'connect', 'variable': 'obj_typ', 'code': 'res', 'description': 'reservoir'},
			{'table': 'connect', 'variable': 'obj_typ', 'code': 'rec', 'description': 'recall'},
			{'table': 'connect', 'variable': 'obj_typ', 'code': 'exc', 'description': 'export coefficients'},
			{'table': 'connect', 'variable': 'obj_typ', 'code': 'dr', 'description': 'delivery ratio'},
			{'table': 'connect', 'variable': 'obj_typ', 'code': 'out', 'description': 'outlet'},
			{'table': 'connect', 'variable': 'obj_typ', 'code': 'sdc', 'description': 'swat-deg channel'},
			{'table': 'connect', 'variable': 'hyd_typ', 'code': 'tot', 'description': 'total flow'},
			{'table': 'connect', 'variable': 'hyd_typ', 'code': 'rhg', 'description': 'recharge'},
			{'table': 'connect', 'variable': 'hyd_typ', 'code': 'sur', 'description': 'surface'},
			{'table': 'connect', 'variable': 'hyd_typ', 'code': 'lat', 'description': 'lateral'},
			{'table': 'connect', 'variable': 'hyd_typ', 'code': 'til', 'description': 'tile'},
			{'table': 'management_sch', 'variable': 'op_typ', 'code': 'plnt', 'description': 'plant'},
			{'table': 'management_sch', 'variable': 'op_typ', 'code': 'harv', 'description': 'harvest only'},
			{'table': 'management_sch', 'variable': 'op_typ', 'code': 'kill', 'description': 'kill'},
			{'table': 'management_sch', 'variable': 'op_typ', 'code': 'hvkl', 'description': 'harvest and kill'},
			{'table': 'management_sch', 'variable': 'op_typ', 'code': 'till', 'description': 'tillage'},
			{'table': 'management_sch', 'variable': 'op_typ', 'code': 'irrm', 'description': 'irrigation'},
			{'table': 'management_sch', 'variable': 'op_typ', 'code': 'fert', 'description': 'fertilizer'},
			{'table': 'management_sch', 'variable': 'op_typ', 'code': 'pest', 'description': 'pesticide application'},
			{'table': 'management_sch', 'variable': 'op_typ', 'code': 'graz', 'description': 'grazing'},
			{'table': 'management_sch', 'variable': 'op_typ', 'code': 'burn', 'description': 'burn'},
			{'table': 'management_sch', 'variable': 'op_typ', 'code': 'swep', 'description': 'street sweep'},
			{'table': 'management_sch', 'variable': 'op_typ', 'code': 'prtp', 'description': 'print plant vars'},
			{'table': 'management_sch', 'variable': 'op_typ', 'code': 'skip', 'description': 'skip to end of the year'}
		]

		with base.db.atomic():
			if version is not None:
				definitions.Version.create(value=version)

			definitions.Tropical_bounds.insert(north=18, south=-18).execute()

			"""if definitions.Var_code.select().count() < 1:
				definitions.Var_code.insert_many(codes).execute()"""
			
			if basin.Codes_bsn.select().count() < 1:
				files_basin.Codes_bsn(source_data_path + 'codes.bsn').read('datasets')
			
			if basin.Parameters_bsn.select().count() < 1:
				files_basin.Parameters_bsn(source_data_path + 'parameters.bsn').read('datasets')
			
			if change.Cal_parms_cal.select().count() < 1:
				files_change.Cal_parms_cal(source_data_path + 'cal_parms.cal').read('datasets')
			
			if hru_parm_db.Plants_plt.select().count() < 1:
				files_parmdb.Plants_plt(source_data_path + 'plants.plt').read('datasets')
			
			if hru_parm_db.Fertilizer_frt.select().count() < 1:
				files_parmdb.Fertilizer_frt(source_data_path + 'fertilizer.frt').read('datasets')
			
			if hru_parm_db.Tillage_til.select().count() < 1:
				files_parmdb.Tillage_til(source_data_path + 'tillage.til').read('datasets')
			
			if hru_parm_db.Pesticide_pst.select().count() < 1:
				files_parmdb.Pesticide_pst(source_data_path + 'pesticide.pst').read('datasets')
			
			if hru_parm_db.Urban_urb.select().count() < 1:
				files_parmdb.Urban_urb(source_data_path + 'urban.urb').read('datasets')
			
			if hru_parm_db.Septic_sep.select().count() < 1:
				files_parmdb.Septic_sep(source_data_path + 'septic.sep').read('datasets')
			
			if hru_parm_db.Snow_sno.select().count() < 1:
				files_parmdb.Snow_sno(source_data_path + 'snow.sno').read('datasets')
			
			if lum.Cntable_lum.select().count() < 1:
				files_lum.Cntable_lum(source_data_path + 'cntable.lum').read('datasets')
			
			if lum.Ovn_table_lum.select().count() < 1:
				files_lum.Ovn_table_lum(source_data_path + 'ovn_table.lum').read('datasets')
			
			if lum.Cons_prac_lum.select().count() < 1:
				files_lum.Cons_prac_lum(source_data_path + 'cons_practice.lum').read('datasets')
			
			if ops.Graze_ops.select().count() < 1:
				files_ops.Graze_ops(source_data_path + 'graze.ops').read('datasets')
			
			if ops.Harv_ops.select().count() < 1:
				files_ops.Harv_ops(source_data_path + 'harv.ops').read('datasets')
			
			if ops.Fire_ops.select().count() < 1:
				files_ops.Fire_ops(source_data_path + 'fire.ops').read('datasets')
			
			if ops.Irr_ops.select().count() < 1:
				files_ops.Irr_ops(source_data_path + 'irr.ops').read('datasets')
			
			if ops.Sweep_ops.select().count() < 1:
				files_ops.Sweep_ops(source_data_path + 'sweep.ops').read('datasets')
			
			if ops.Chem_app_ops.select().count() < 1:
				files_ops.Chem_app_ops(source_data_path + 'chem_app.ops').read('datasets')
			
			if structural.Bmpuser_str.select().count() < 1:
				files_str.Bmpuser_str(source_data_path + 'bmpuser.str').read('datasets')
			
			if structural.Filterstrip_str.select().count() < 1:
				files_str.Filterstrip_str(source_data_path + 'filterstrip.str').read('datasets')
			
			if structural.Grassedww_str.select().count() < 1:
				files_str.Grassedww_str(source_data_path + 'grassedww.str').read('datasets')
			
			if structural.Septic_str.select().count() < 1:
				files_str.Septic_str(source_data_path + 'septic.str').read('datasets')
			
			if structural.Tiledrain_str.select().count() < 1:
				files_str.Tiledrain_str(source_data_path + 'tiledrain.str').read('datasets')
			
			if decision_table.D_table_dtl.select().count() < 1:
				files_dtable.D_table_dtl(source_data_path + 'lum.dtl').read('datasets')
				files_dtable.D_table_dtl(source_data_path + 'res_rel.dtl').read('datasets')
				files_dtable.D_table_dtl(source_data_path + 'scen_lu.dtl').read('datasets')
				files_dtable.D_table_dtl(source_data_path + 'flo_con.dtl').read('datasets')
			
			if soils.Soils_lte_sol.select().count() < 1:
				files_soils.Soils_lte_sol(source_data_path + 'soils_lte.sol').read('datasets')
				
			"""if lum.Management_sch.select().count() < 1:
				files_lum.Management_sch(source_data_path + 'management.sch').read('datasets')"""

		classifications = [
			{'id': 1, 'name': 'simulation'},
			{'id': 2, 'name': 'basin'},
			{'id': 3, 'name': 'climate'},
			{'id': 4, 'name': 'connect'},
			{'id': 5, 'name': 'channel'},
			{'id': 6, 'name': 'reservoir'},
			{'id': 7, 'name': 'routing_unit'},
			{'id': 8, 'name': 'hru'},
			{'id': 9, 'name': 'exco'},
			{'id': 10, 'name': 'recall'},
			{'id': 11, 'name': 'dr'},
			{'id': 12, 'name': 'aquifer'},
			{'id': 13, 'name': 'herd'},
			{'id': 14, 'name': 'water_rights'},
			{'id': 15, 'name': 'link'},
			{'id': 16, 'name': 'hydrology'},
			{'id': 17, 'name': 'structural'},
			{'id': 18, 'name': 'hru_parm_db'},
			{'id': 19, 'name': 'ops'},
			{'id': 20, 'name': 'lum'},
			{'id': 21, 'name': 'chg'},
			{'id': 22, 'name': 'init'},
			{'id': 23, 'name': 'soils'},
			{'id': 24, 'name': 'decision_table'},
			{'id': 25, 'name': 'regions'},
			{'id': 26, 'name': 'pcp_path'},
			{'id': 27, 'name': 'tmp_path'},
			{'id': 28, 'name': 'slr_path'},
			{'id': 29, 'name': 'hmd_path'},
			{'id': 30, 'name': 'wnd_path'}
		]
		
		file_cio = [
			{'classification': 1, 'order_in_class': 1, 'default_file_name': 'time.sim', 'database_table': 'time_sim', 'is_core_file': True},
			{'classification': 1, 'order_in_class': 2, 'default_file_name': 'print.prt', 'database_table': 'print_prt', 'is_core_file': True},
			{'classification': 1, 'order_in_class': 3, 'default_file_name': 'object.prt', 'database_table': 'object_prt', 'is_core_file': False},
			{'classification': 1, 'order_in_class': 4, 'default_file_name': 'object.cnt', 'database_table': 'object_cnt', 'is_core_file': True},
			{'classification': 1, 'order_in_class': 5, 'default_file_name': 'constituents.cs', 'database_table': 'constituents_cs', 'is_core_file': False},
			
			{'classification': 2, 'order_in_class': 1, 'default_file_name': 'codes.bsn', 'database_table': 'codes_bsn', 'is_core_file': True},
			{'classification': 2, 'order_in_class': 2, 'default_file_name': 'parameters.bsn', 'database_table': 'parameters_bsn', 'is_core_file': True},
			
			{'classification': 3, 'order_in_class': 1, 'default_file_name': 'weather-sta.cli', 'database_table': 'weather_sta_cli', 'is_core_file': True},
			{'classification': 3, 'order_in_class': 2, 'default_file_name': 'weather-wgn.cli', 'database_table': 'weather_wgn_cli', 'is_core_file': True},
			{'classification': 3, 'order_in_class': 3, 'default_file_name': 'wind-dir.cli', 'database_table': 'wind_dir_cli', 'is_core_file': False},
			{'classification': 3, 'order_in_class': 4, 'default_file_name': 'pcp.cli', 'database_table': 'weather_file', 'is_core_file': True},
			{'classification': 3, 'order_in_class': 5, 'default_file_name': 'tmp.cli', 'database_table': 'weather_file', 'is_core_file': True},
			{'classification': 3, 'order_in_class': 6, 'default_file_name': 'slr.cli', 'database_table': 'weather_file', 'is_core_file': True},
			{'classification': 3, 'order_in_class': 7, 'default_file_name': 'hmd.cli', 'database_table': 'weather_file', 'is_core_file': True},
			{'classification': 3, 'order_in_class': 8, 'default_file_name': 'wnd.cli', 'database_table': 'weather_file', 'is_core_file': True},
			{'classification': 3, 'order_in_class': 9, 'default_file_name': 'atmodep.cli', 'database_table': 'atmodep_cli', 'is_core_file': False},
			
			{'classification': 4, 'order_in_class': 1, 'default_file_name': 'hru.con', 'database_table': 'hru_con', 'is_core_file': True},
			{'classification': 4, 'order_in_class': 2, 'default_file_name': 'hru-lte.con', 'database_table': 'hru_lte_con', 'is_core_file': False},
			{'classification': 4, 'order_in_class': 3, 'default_file_name': 'rout_unit.con', 'database_table': 'rout_unit_con', 'is_core_file': True},
			{'classification': 4, 'order_in_class': 4, 'default_file_name': 'modflow.con', 'database_table': 'modflow_con', 'is_core_file': False},
			{'classification': 4, 'order_in_class': 5, 'default_file_name': 'aquifer.con', 'database_table': 'aquifer_con', 'is_core_file': True},
			{'classification': 4, 'order_in_class': 6, 'default_file_name': 'aquifer2d.con', 'database_table': 'aquifer2d_con', 'is_core_file': False},
			{'classification': 4, 'order_in_class': 7, 'default_file_name': 'channel.con', 'database_table': 'channel_con', 'is_core_file': True},
			{'classification': 4, 'order_in_class': 8, 'default_file_name': 'reservoir.con', 'database_table': 'reservoir_con', 'is_core_file': True},
			{'classification': 4, 'order_in_class': 9, 'default_file_name': 'recall.con', 'database_table': 'recall_con', 'is_core_file': True},
			{'classification': 4, 'order_in_class': 10, 'default_file_name': 'exco.con', 'database_table': 'exco_con', 'is_core_file': False},
			{'classification': 4, 'order_in_class': 11, 'default_file_name': 'delratio.con', 'database_table': 'delratio_con', 'is_core_file': False},
			{'classification': 4, 'order_in_class': 12, 'default_file_name': 'outlet.con', 'database_table': 'outlet_con', 'is_core_file': True},
			{'classification': 4, 'order_in_class': 13, 'default_file_name': 'chandeg.con', 'database_table': 'chandeg_con', 'is_core_file': False},
			
			{'classification': 5, 'order_in_class': 1, 'default_file_name': 'initial.cha', 'database_table': 'initial_cha', 'is_core_file': True},
			{'classification': 5, 'order_in_class': 2, 'default_file_name': 'channel.cha', 'database_table': 'channel_cha', 'is_core_file': True},
			{'classification': 5, 'order_in_class': 3, 'default_file_name': 'hydrology.cha', 'database_table': 'hydrology_cha', 'is_core_file': True},
			{'classification': 5, 'order_in_class': 4, 'default_file_name': 'sediment.cha', 'database_table': 'sediment_cha', 'is_core_file': True},
			{'classification': 5, 'order_in_class': 5, 'default_file_name': 'nutrients.cha', 'database_table': 'nutrients_cha', 'is_core_file': True},
			{'classification': 5, 'order_in_class': 6, 'default_file_name': 'channel-lte.cha', 'database_table': 'channel_lte_cha', 'is_core_file': False},
			{'classification': 5, 'order_in_class': 7, 'default_file_name': 'hyd-sed-lte.cha', 'database_table': 'hyd_sed_lte_cha', 'is_core_file': False},
			{'classification': 5, 'order_in_class': 8, 'default_file_name': 'temperature.cha', 'database_table': 'temperature_cha', 'is_core_file': False},
			
			{'classification': 6, 'order_in_class': 1, 'default_file_name': 'initial.res', 'database_table': 'initial_res', 'is_core_file': True},
			{'classification': 6, 'order_in_class': 2, 'default_file_name': 'reservoir.res', 'database_table': 'reservoir_res', 'is_core_file': True},
			{'classification': 6, 'order_in_class': 3, 'default_file_name': 'hydrology.res', 'database_table': 'hydrology_res', 'is_core_file': True},
			{'classification': 6, 'order_in_class': 4, 'default_file_name': 'sediment.res', 'database_table': 'sediment_res', 'is_core_file': True},
			{'classification': 6, 'order_in_class': 5, 'default_file_name': 'nutrients.res', 'database_table': 'nutrients_res', 'is_core_file': True},
			{'classification': 6, 'order_in_class': 6, 'default_file_name': 'weir.res', 'database_table': 'weir_res', 'is_core_file': False},
			{'classification': 6, 'order_in_class': 7, 'default_file_name': 'wetland.wet', 'database_table': 'wetland_wet', 'is_core_file': False},
			{'classification': 6, 'order_in_class': 8, 'default_file_name': 'hydrology.wet', 'database_table': 'hydrology_wet', 'is_core_file': False},
			
			{'classification': 7, 'order_in_class': 1, 'default_file_name': 'rout_unit.def', 'database_table': '', 'is_core_file': True},
			{'classification': 7, 'order_in_class': 2, 'default_file_name': 'rout_unit.ele', 'database_table': 'rout_unit_ele', 'is_core_file': True},
			{'classification': 7, 'order_in_class': 3, 'default_file_name': 'rout_unit.rtu', 'database_table': 'rout_unit_rtu', 'is_core_file': True},
			{'classification': 7, 'order_in_class': 4, 'default_file_name': 'rout_unit.dr', 'database_table': 'rout_unit_dr', 'is_core_file': False},
			
			{'classification': 8, 'order_in_class': 1, 'default_file_name': 'hru-data.hru', 'database_table': 'hru_data_hru', 'is_core_file': True},
			{'classification': 8, 'order_in_class': 2, 'default_file_name': 'hru-lte.hru', 'database_table': 'hru_lte_hru', 'is_core_file': False},
			
			{'classification': 9, 'order_in_class': 1, 'default_file_name': 'exco.exc', 'database_table': 'exco_exc', 'is_core_file': False},
			{'classification': 9, 'order_in_class': 2, 'default_file_name': 'exco_om.exc', 'database_table': 'exco_om_exc', 'is_core_file': False},
			{'classification': 9, 'order_in_class': 3, 'default_file_name': 'exco_pest.exc', 'database_table': 'exco_pest_exc', 'is_core_file': False},
			{'classification': 9, 'order_in_class': 4, 'default_file_name': 'exco_path.exc', 'database_table': 'exco_path_exc', 'is_core_file': False},
			{'classification': 9, 'order_in_class': 5, 'default_file_name': 'exco_hmet.exc', 'database_table': 'exco_hmet_exc', 'is_core_file': False},
			{'classification': 9, 'order_in_class': 6, 'default_file_name': 'exco_salt.exc', 'database_table': 'exco_salt_exc', 'is_core_file': False},
			
			{'classification': 10, 'order_in_class': 1, 'default_file_name': 'recall.rec', 'database_table': 'recall_rec', 'is_core_file': True},
			
			{'classification': 11, 'order_in_class': 1, 'default_file_name': 'delratio.del', 'database_table': 'delratio_del', 'is_core_file': False},
			{'classification': 11, 'order_in_class': 2, 'default_file_name': 'dr_om.del', 'database_table': 'dr_om_exc', 'is_core_file': False},
			{'classification': 11, 'order_in_class': 3, 'default_file_name': 'dr_pest.del', 'database_table': 'dr_pest_del', 'is_core_file': False},
			{'classification': 11, 'order_in_class': 4, 'default_file_name': 'dr_path.del', 'database_table': 'dr_path_del', 'is_core_file': False},
			{'classification': 11, 'order_in_class': 5, 'default_file_name': 'dr_hmet.del', 'database_table': 'dr_hmet_del', 'is_core_file': False},
			{'classification': 11, 'order_in_class': 6, 'default_file_name': 'dr_salt.del', 'database_table': 'dr_salt_del', 'is_core_file': False},
			
			{'classification': 12, 'order_in_class': 1, 'default_file_name': 'initial.aqu', 'database_table': 'initial_aqu', 'is_core_file': True},
			{'classification': 12, 'order_in_class': 2, 'default_file_name': 'aquifer.aqu', 'database_table': 'aquifer_aqu', 'is_core_file': True},
			
			{'classification': 13, 'order_in_class': 1, 'default_file_name': 'animal.hrd', 'database_table': 'animal_hrd', 'is_core_file': False},
			{'classification': 13, 'order_in_class': 2, 'default_file_name': 'herd.hrd', 'database_table': 'herd_hrd', 'is_core_file': False},
			{'classification': 13, 'order_in_class': 3, 'default_file_name': 'ranch.hrd', 'database_table': 'ranch_hrd', 'is_core_file': False},
			
			{'classification': 14, 'order_in_class': 1, 'default_file_name': 'define.wro', 'database_table': 'define_wro', 'is_core_file': False},
			{'classification': 14, 'order_in_class': 2, 'default_file_name': 'element.wro', 'database_table': 'element_wro', 'is_core_file': False},
			{'classification': 14, 'order_in_class': 3, 'default_file_name': 'water_rights.wro', 'database_table': 'water_rights_wro', 'is_core_file': False},
			
			{'classification': 15, 'order_in_class': 1, 'default_file_name': 'chan-surf.lin', 'database_table': 'chan_surf_lin', 'is_core_file': False},
			{'classification': 15, 'order_in_class': 2, 'default_file_name': 'chan-aqu.lin', 'database_table': 'chan_aqu_lin', 'is_core_file': False},
			
			{'classification': 16, 'order_in_class': 1, 'default_file_name': 'hydrology.hyd', 'database_table': 'hydrology_hyd', 'is_core_file': True},
			{'classification': 16, 'order_in_class': 2, 'default_file_name': 'topography.hyd', 'database_table': 'topography_hyd', 'is_core_file': True},
			{'classification': 16, 'order_in_class': 3, 'default_file_name': 'field.fld', 'database_table': 'field_fld', 'is_core_file': True},
			
			{'classification': 17, 'order_in_class': 1, 'default_file_name': 'tiledrain.str', 'database_table': 'tiledrain_str', 'is_core_file': True},
			{'classification': 17, 'order_in_class': 2, 'default_file_name': 'septic.str', 'database_table': 'septic_str', 'is_core_file': False},
			{'classification': 17, 'order_in_class': 3, 'default_file_name': 'filterstrip.str', 'database_table': 'filterstrip_str', 'is_core_file': True},
			{'classification': 17, 'order_in_class': 4, 'default_file_name': 'grassedww.str', 'database_table': 'grassedww_str', 'is_core_file': True},
			{'classification': 17, 'order_in_class': 5, 'default_file_name': 'bmpuser.str', 'database_table': 'bmpuser_str', 'is_core_file': False},
			
			{'classification': 18, 'order_in_class': 1, 'default_file_name': 'plants.plt', 'database_table': 'plants_plt', 'is_core_file': True},
			{'classification': 18, 'order_in_class': 2, 'default_file_name': 'fertilizer.frt', 'database_table': 'fertilizer_frt', 'is_core_file': True},
			{'classification': 18, 'order_in_class': 3, 'default_file_name': 'tillage.til', 'database_table': 'tillage_til', 'is_core_file': True},
			{'classification': 18, 'order_in_class': 4, 'default_file_name': 'pesticide.pst', 'database_table': 'pesticide_pst', 'is_core_file': False},
			{'classification': 18, 'order_in_class': 5, 'default_file_name': 'pathogens.pth', 'database_table': 'pathogens_pth', 'is_core_file': False},
			{'classification': 18, 'order_in_class': 6, 'default_file_name': 'metals.mtl', 'database_table': 'metals_mtl', 'is_core_file': False},
			{'classification': 18, 'order_in_class': 7, 'default_file_name': 'salts.slt', 'database_table': 'salts_slt', 'is_core_file': False},
			{'classification': 18, 'order_in_class': 8, 'default_file_name': 'urban.urb', 'database_table': 'urban_urb', 'is_core_file': True},
			{'classification': 18, 'order_in_class': 9, 'default_file_name': 'septic.sep', 'database_table': 'septic_sep', 'is_core_file': False},
			{'classification': 18, 'order_in_class': 10, 'default_file_name': 'snow.sno', 'database_table': 'snow_sno', 'is_core_file': True},
			
			{'classification': 19, 'order_in_class': 1, 'default_file_name': 'harv.ops', 'database_table': 'harv_ops', 'is_core_file': True},
			{'classification': 19, 'order_in_class': 2, 'default_file_name': 'graze.ops', 'database_table': 'graze_ops', 'is_core_file': True},
			{'classification': 19, 'order_in_class': 3, 'default_file_name': 'irr.ops', 'database_table': 'irr_ops', 'is_core_file': True},
			{'classification': 19, 'order_in_class': 4, 'default_file_name': 'chem_app.ops', 'database_table': 'chem_app_ops', 'is_core_file': False},
			{'classification': 19, 'order_in_class': 5, 'default_file_name': 'fire.ops', 'database_table': 'fire_ops', 'is_core_file': True},
			{'classification': 19, 'order_in_class': 6, 'default_file_name': 'sweep.ops', 'database_table': 'sweep_ops', 'is_core_file': False},
			
			{'classification': 20, 'order_in_class': 1, 'default_file_name': 'landuse.lum', 'database_table': 'landuse_lum', 'is_core_file': True},
			{'classification': 20, 'order_in_class': 2, 'default_file_name': 'management.sch', 'database_table': 'management_sch', 'is_core_file': True},
			{'classification': 20, 'order_in_class': 3, 'default_file_name': 'cntable.lum', 'database_table': 'cntable_lum', 'is_core_file': True},
			{'classification': 20, 'order_in_class': 4, 'default_file_name': 'cons_practice.lum', 'database_table': 'cons_practice_lum', 'is_core_file': True},
			{'classification': 20, 'order_in_class': 5, 'default_file_name': 'ovn_table.lum', 'database_table': 'ovn_table_lum', 'is_core_file': True},
			
			{'classification': 21, 'order_in_class': 1, 'default_file_name': 'cal_parms.cal', 'database_table': 'cal_parms_cal', 'is_core_file': False},
			{'classification': 21, 'order_in_class': 2, 'default_file_name': 'calibration.cal', 'database_table': 'calibration_cal', 'is_core_file': False},
			{'classification': 21, 'order_in_class': 3, 'default_file_name': 'codes.sft', 'database_table': 'codes_sft', 'is_core_file': False},
			{'classification': 21, 'order_in_class': 4, 'default_file_name': 'wb_parms.sft', 'database_table': 'wb_parms_sft', 'is_core_file': False},
			{'classification': 21, 'order_in_class': 5, 'default_file_name': 'water_balance.sft', 'database_table': 'water_balance_sft', 'is_core_file': False},
			{'classification': 21, 'order_in_class': 6, 'default_file_name': 'ch_sed_budget.sft', 'database_table': 'ch_sed_budget_sft', 'is_core_file': False},
			{'classification': 21, 'order_in_class': 7, 'default_file_name': 'ch_sed_parms.sft', 'database_table': 'ch_sed_parms_sft', 'is_core_file': False},
			{'classification': 21, 'order_in_class': 8, 'default_file_name': 'plant_parms.sft', 'database_table': 'plant_parms_sft', 'is_core_file': False},
			{'classification': 21, 'order_in_class': 9, 'default_file_name': 'plant_gro.sft', 'database_table': 'plant_gro_sft', 'is_core_file': False},
			
			{'classification': 22, 'order_in_class': 1, 'default_file_name': 'plant.ini', 'database_table': 'plant_ini', 'is_core_file': False},
			{'classification': 22, 'order_in_class': 2, 'default_file_name': 'soil_plant.ini', 'database_table': 'soil_plant_ini', 'is_core_file': True},
			{'classification': 22, 'order_in_class': 3, 'default_file_name': 'om_water.ini', 'database_table': 'om_water_ini', 'is_core_file': True},
			{'classification': 22, 'order_in_class': 4, 'default_file_name': 'pest_hru.ini', 'database_table': 'pest_hru_ini', 'is_core_file': True},
			{'classification': 22, 'order_in_class': 5, 'default_file_name': 'pest_water.ini', 'database_table': 'pest_water_ini', 'is_core_file': True},
			{'classification': 22, 'order_in_class': 6, 'default_file_name': 'path_hru.ini', 'database_table': 'path_hru_ini', 'is_core_file': True},
			{'classification': 22, 'order_in_class': 7, 'default_file_name': 'path_water.ini', 'database_table': 'path_water_ini', 'is_core_file': True},
			{'classification': 22, 'order_in_class': 8, 'default_file_name': 'hmet_hru.ini', 'database_table': 'hmet_hru_ini', 'is_core_file': True},
			{'classification': 22, 'order_in_class': 9, 'default_file_name': 'hmet_water.ini', 'database_table': 'hmet_water_ini', 'is_core_file': True},
			{'classification': 22, 'order_in_class': 10, 'default_file_name': 'salt_hru.ini', 'database_table': 'salt_hru_ini', 'is_core_file': True},
			{'classification': 22, 'order_in_class': 11, 'default_file_name': 'salt_water.ini', 'database_table': 'salt_water_ini', 'is_core_file': True},

			{'classification': 23, 'order_in_class': 1, 'default_file_name': 'soils.sol', 'database_table': 'soils_sol', 'is_core_file': True},
			{'classification': 23, 'order_in_class': 2, 'default_file_name': 'nutrients.sol', 'database_table': 'nutrients_sol', 'is_core_file': True},
			{'classification': 23, 'order_in_class': 3, 'default_file_name': 'soils_lte.sol', 'database_table': 'soils_lte_sol', 'is_core_file': True},
			
			{'classification': 24, 'order_in_class': 1, 'default_file_name': 'lum.dtl', 'database_table': 'lum_dtl', 'is_core_file': True},
			{'classification': 24, 'order_in_class': 2, 'default_file_name': 'res_rel.dtl', 'database_table': 'res_rel_dtl', 'is_core_file': True},
			{'classification': 24, 'order_in_class': 3, 'default_file_name': 'scen_lu.dtl', 'database_table': 'scen_lu_dtl', 'is_core_file': True},
			{'classification': 24, 'order_in_class': 4, 'default_file_name': 'flo_con.dtl', 'database_table': 'flo_con_dtl', 'is_core_file': True},
			
			{'classification': 25, 'order_in_class': 1, 'default_file_name': 'ls_unit.ele', 'database_table': 'ls_unit_ele', 'is_core_file': True},
			{'classification': 25, 'order_in_class': 2, 'default_file_name': 'ls_unit.def', 'database_table': 'ls_unit_def', 'is_core_file': True},
			{'classification': 25, 'order_in_class': 3, 'default_file_name': 'ls_reg.ele', 'database_table': 'ls_reg_ele', 'is_core_file': False},
			{'classification': 25, 'order_in_class': 4, 'default_file_name': 'ls_reg.def', 'database_table': 'ls_reg_def', 'is_core_file': False},
			{'classification': 25, 'order_in_class': 5, 'default_file_name': 'ls_cal.reg', 'database_table': 'ls_cal_reg', 'is_core_file': False},
			{'classification': 25, 'order_in_class': 6, 'default_file_name': 'ch_catunit.ele', 'database_table': 'ch_catunit_ele', 'is_core_file': False},
			{'classification': 25, 'order_in_class': 7, 'default_file_name': 'ch_catunit.def', 'database_table': 'ch_catunit_def', 'is_core_file': False},
			{'classification': 25, 'order_in_class': 8, 'default_file_name': 'ch_reg.def', 'database_table': 'ch_reg_def', 'is_core_file': False},
			{'classification': 25, 'order_in_class': 9, 'default_file_name': 'aqu_catunit.ele', 'database_table': 'aqu_catunit_ele', 'is_core_file': False},
			{'classification': 25, 'order_in_class': 10, 'default_file_name': 'aqu_catunit.def', 'database_table': 'aqu_catunit_def', 'is_core_file': False},
			{'classification': 25, 'order_in_class': 11, 'default_file_name': 'aqu_reg.def', 'database_table': 'aqu_reg_def', 'is_core_file': False},
			{'classification': 25, 'order_in_class': 12, 'default_file_name': 'res_catunit.ele', 'database_table': 'res_catunit_ele', 'is_core_file': False},
			{'classification': 25, 'order_in_class': 13, 'default_file_name': 'res_catunit.def', 'database_table': 'res_catunit_def', 'is_core_file': False},
			{'classification': 25, 'order_in_class': 14, 'default_file_name': 'res_reg.def', 'database_table': 'res_reg_def', 'is_core_file': False},
			{'classification': 25, 'order_in_class': 15, 'default_file_name': 'rec_catunit.ele', 'database_table': 'rec_catunit_ele', 'is_core_file': False},
			{'classification': 25, 'order_in_class': 16, 'default_file_name': 'rec_catunit.def', 'database_table': 'rec_catunit_def', 'is_core_file': False},
			{'classification': 25, 'order_in_class': 17, 'default_file_name': 'rec_reg.def', 'database_table': 'rec_reg_def', 'is_core_file': False}
		]
		
		print_prt_objects = [
			{'name': 'basin_wb', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'basin_nb', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'basin_ls', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'basin_pw', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'basin_aqu', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'basin_res', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'basin_cha', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'basin_sd_cha', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'basin_psc', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'region_wb', 'daily': False, 'monthly': False, 'yearly': False, 'avann': False},
			{'name': 'region_nb', 'daily': False, 'monthly': False, 'yearly': False, 'avann': False},
			{'name': 'region_ls', 'daily': False, 'monthly': False, 'yearly': False, 'avann': False},
			{'name': 'region_pw', 'daily': False, 'monthly': False, 'yearly': False, 'avann': False},
			{'name': 'region_aqu', 'daily': False, 'monthly': False, 'yearly': False, 'avann': False},
			{'name': 'region_res', 'daily': False, 'monthly': False, 'yearly': False, 'avann': False},
			{'name': 'region_cha', 'daily': False, 'monthly': False, 'yearly': False, 'avann': False},
			{'name': 'region_sd_cha', 'daily': False, 'monthly': False, 'yearly': False, 'avann': False},
			{'name': 'region_psc', 'daily': False, 'monthly': False, 'yearly': False, 'avann': False},
			{'name': 'lsunit_wb', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'lsunit_nb', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'lsunit_ls', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'lsunit_pw', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'hru_wb', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'hru_nb', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'hru_ls', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'hru_pw', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'hru-lte_wb', 'daily': False, 'monthly': False, 'yearly': False, 'avann': False},
			{'name': 'hru-lte_nb', 'daily': False, 'monthly': False, 'yearly': False, 'avann': False},
			{'name': 'hru-lte_ls', 'daily': False, 'monthly': False, 'yearly': False, 'avann': False},
			{'name': 'hru-lte_pw', 'daily': False, 'monthly': False, 'yearly': False, 'avann': False},
			{'name': 'channel', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'channel_sd', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'aquifer', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'reservoir', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'recall', 'daily': False, 'monthly': False, 'yearly': True, 'avann': False},
			{'name': 'hyd', 'daily': False, 'monthly': False, 'yearly': False, 'avann': False},
			{'name': 'ru', 'daily': False, 'monthly': False, 'yearly': False, 'avann': False},
			{'name': 'pest', 'daily': False, 'monthly': False, 'yearly': False, 'avann': False}
		]

		with base.db.atomic():
			if definitions.File_cio_classification.select().count() < 1:
				definitions.File_cio_classification.insert_many(classifications).execute()
			
			if definitions.File_cio.select().count() < 1:
				definitions.File_cio.insert_many(file_cio).execute()
			
			if definitions.Print_prt.select().count() < 1:
				definitions.Print_prt.create(
					nyskip=1,
					day_start=0,
					day_end=0,
					yrc_start=0,
					yrc_end=0,
					interval=1,
					csvout=False,
					dbout=False,
					cdfout=False,
					soilout=False,
					mgtout=False,
					hydcon=False,
					fdcout=False
				)
			
			if definitions.Print_prt_object.select().count() < 1:
				definitions.Print_prt_object.insert_many(print_prt_objects).execute()
				
		if lum.Landuse_lum.select().count() < 1:
			SetupDatasetsDatabase.insert_lum()
			
		"""if definitions.Var_range.select().count() < 1:
			SetupDatasetsDatabase.insert_var_range()
			SetupDatasetsDatabase.insert_var_range_option()"""
	
	@staticmethod
	def insert_var_range():
		file = open(source_data_path + 'var_range.csv', "r")
		
		i = 0
		items = []
		for line in file:
			if i > 0:
				val = line.split(',')
				items.append({
					'id': i,
					'table': val[0],
					'variable': val[1],
					'type': val[2],
					'min_value': val[3],
					'max_value': val[4],
					'default_value': val[5],
					'default_text': val[6],
					'units': val[7],
					'description': val[8]
				})
			
			i += 1
		
		db_lib.bulk_insert(base.db, definitions.Var_range, items)
	
	@staticmethod
	def insert_var_range_option():
		file = open(source_data_path + 'var_range_option.csv', "r")
		
		i = 0
		items = []
		for line in file:
			if i > 0:
				val = line.split(',')

				vr = definitions.Var_range.get_or_none((definitions.Var_range.table == val[0]) & (definitions.Var_range.variable == val[1]))
				
				if vr is not None:
					items.append({
						'id': i,
						'var_range_id': vr.id,
						'value': val[2],
						'text': val[3],
						'text_only': True if val[4].strip() == '1' else False,
						'text_value': None if val[5].strip() == '' else val[5].strip()
					})
			
			i += 1
		
		db_lib.bulk_insert(base.db, definitions.Var_range_option, items)

	@staticmethod
	def insert_lum():
		file = open(source_data_path + 'plants_landuse_rules.csv', "r")
		
		i = 1
		rules = {}
		for line in file:
			if i > 1:
				val = line.split(',')
				n = val[0].lower().strip()
				lc = int(val[6])
				rules[n] = {
					'mgt': None,
					'cn2': val[3],
					'cons_prac': val[4],
					'ov_mann': val[5],
					'lc_status': True if lc is 1 else False,
					'lai_init': float(val[7]),
					'bm_init': float(val[8]),
					'phu_init': float(val[9]),
					'plnt_pop': float(val[10]),
					'yrs_init': float(val[11]),
					'rsd_init': float(val[12])
				}
			
			i += 1
			
		plants = hru_parm_db.Plants_plt.select()
		
		plant_coms = []
		plant_com_items = []
		plant_com_id = 1
		for plt in plants:
			rule = rules[plt.name]
			
			plant_com = {
				'id': plant_com_id,
				'name': '{name}_comm'.format(name=plt.name),
				'rot_yr_ini': 1
			}
			plant_coms.append(plant_com)
			
			plant_com_item = {
				'plant_ini': plant_com_id,
				'plnt_name': plt.id,
				'lc_status': rule['lc_status'],
				'lai_init': rule['lai_init'],
				'bm_init': rule['bm_init'],
				'phu_init': rule['phu_init'],
				'plnt_pop': rule['plnt_pop'],
				'yrs_init': rule['yrs_init'],
				'rsd_init': rule['rsd_init']
			}
			plant_com_items.append(plant_com_item)
			plant_com_id += 1
		
		db_lib.bulk_insert(base.db, init.Plant_ini, plant_coms)
		db_lib.bulk_insert(base.db, init.Plant_ini_item, plant_com_items)
		
		lum_default_cal_group = None
		lum_default_mgt = None #lum.Management_sch.get(lum.Management_sch.name == 'no_mgt').id
		lum_default_cn2 = 5
		lum_default_cons_prac = 1
		lum_default_ov_mann = 2
		
		lums = []
		lum_dict = {}
		lum_id = 1
		for pcom in init.Plant_ini.select().order_by(init.Plant_ini.id):
			plant_name = pcom.name.strip().split('_comm')[0]
			rule = rules[plant_name]
			
			"""mgt_id = lum_default_mgt
			if val_exists(rule['mgt']):
				mgt = lum.Management_sch.get(lum.Management_sch.name == rule['mgt'])
				mgt_id = mgt.id"""
				
			cn2_id = lum_default_cn2
			if val_exists(rule['cn2']):
				cn2 = lum.Cntable_lum.get(lum.Cntable_lum.name == rule['cn2'])
				cn2_id = cn2.id
				
			cons_prac_id = lum_default_cons_prac
			if val_exists(rule['cons_prac']):
				cons_prac = lum.Cons_prac_lum.get(lum.Cons_prac_lum.name == rule['cons_prac'])
				cons_prac_id = cons_prac.id
				
			ov_mann_id = lum_default_ov_mann
			if val_exists(rule['ov_mann']):
				ov_mann = lum.Ovn_table_lum.get(lum.Ovn_table_lum.name == rule['ov_mann'])
				ov_mann_id = ov_mann.id
			
			l = {
				'id': lum_id,
				'name': '{name}_lum'.format(name=plant_name),
				'plnt_com': pcom.id,
				'mgt': None, #mgt_id,
				'cn2': cn2_id,
				'cons_prac': cons_prac_id,
				'ov_mann': ov_mann_id,
				'cal_group': lum_default_cal_group
			}
			lums.append(l)
			
			lum_dict[plant_name] = lum_id
			lum_id += 1
			
		db_lib.bulk_insert(base.db, lum.Landuse_lum, lums)
		
		urbans = hru_parm_db.Urban_urb.select()
		urb_lums = []
		for urb in urbans:
			l = {
				'id': lum_id,
				'name': '{name}_lum'.format(name=urb.name),
				'urban': urb.id,
				'urb_ro': 'buildup_washoff',
				'mgt': lum_default_mgt,
				'cn2': 49,
				'cons_prac': lum_default_cons_prac,
				'ov_mann': 18,
				'cal_group': lum_default_cal_group
			}
			urb_lums.append(l)
			
			lum_dict[urb.name] = lum_id
			lum_id += 1
			
		db_lib.bulk_insert(base.db, lum.Landuse_lum, urb_lums)
