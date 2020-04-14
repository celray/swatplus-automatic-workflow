from helpers.executable_api import ExecutableApi, Unbuffered
from helpers import utils
from database import lib
from database.project import base, init, dr, channel, reservoir, simulation, hru, lum, exco, connect, routing_unit, recall, change, soils, aquifer, hru_parm_db, decision_table, ops, basin
from database.project.config import Project_config, File_cio
from database.project.setup import SetupProjectDatabase
from database.datasets.setup import SetupDatasetsDatabase

from database.datasets.hru_parm_db import Plants_plt as dataset_plants
from database.datasets.definitions import File_cio as dataset_file_cio, Var_range, Version
from database.datasets import change as datasets_change, init as datasets_init, lum as datasets_lum, basin as datasets_basin
from actions.import_gis import GisImport

from .reimport_gis import ReimportGis

import sys
import argparse
import os, os.path
from shutil import copyfile
import time
from peewee import *
from playhouse.migrate import *
import datetime

available_to_update = [
	'1.2.0',
	'1.1.2',
	'1.1.1',
	'1.1.0',
	'1.0.0'
]


class UpdateProject(ExecutableApi):
	def __init__(self, project_db, new_version, datasets_db=None, update_project_values=False, reimport_gis=False):
		SetupProjectDatabase.init(project_db)
		try:
			m = self.check_config(new_version)

			base_path = os.path.dirname(project_db)
			rel_project_db = os.path.relpath(project_db, base_path)

			if datasets_db is None:
				datasets_db = utils.full_path(project_db, m.reference_db)
			else:				
				rel_datasets_db = os.path.relpath(datasets_db, base_path)
				m.reference_db = rel_datasets_db

			# Ensure correct version of datasets db
			ver_check = SetupDatasetsDatabase.check_version(datasets_db, new_version)
			if ver_check is not None:
				sys.exit(ver_check)

			# Backup original db before beginning
			try:
				self.emit_progress(2, 'Backing up project database...')
				filename, file_extension = os.path.splitext(rel_project_db)
				bak_filename = filename + '_v' + m.editor_version.replace('.', '_') + '_' + time.strftime('%Y%m%d-%H%M%S') + file_extension
				bak_dir = os.path.join(base_path, 'DatabaseBackups')
				if not os.path.exists(bak_dir):
					os.makedirs(bak_dir)
				backup_db_file = os.path.join(bak_dir, bak_filename)
				copyfile(project_db, os.path.join(bak_dir, bak_filename))
			except IOError as err:
				sys.exit(err)
			
			did_update = False
			if m.editor_version == '1.2.0':
				self.updates_for_1_2_1(project_db, backup_db_file)
				did_update = True
				reimport_gis = False
			if m.editor_version == '1.1.0' or m.editor_version == '1.1.1' or m.editor_version == '1.1.2':
				self.updates_for_1_2_0(project_db, update_project_values, backup_db_file)
				self.updates_for_1_2_1(project_db, backup_db_file)
				did_update = True
			elif m.editor_version == '1.0.0':
				self.updates_for_1_1_0(project_db, datasets_db, backup_db_file)
				self.updates_for_1_2_0(project_db, update_project_values, backup_db_file)
				self.updates_for_1_2_1(project_db, backup_db_file)
				did_update = True
			
			m.editor_version = new_version
			result = m.save()

			if did_update and reimport_gis:
				ReimportGis(project_db, new_version, None, m.project_name, datasets_db, True, m.is_lte)
		except Project_config.DoesNotExist:
			sys.exit("Could not retrieve project configuration data.")

	def check_config(self, new_version):
		m = Project_config.get()
		if m.editor_version not in available_to_update:
			sys.exit("Unable to update this project to {new_version}. Updates from {current_version} unavailable.".format(new_version=new_version, current_version=m.editor_version))
			
		return m

	def updates_for_1_2_1(self, project_db, rollback_db):
		try:
			lum.Landuse_lum.update({lum.Landuse_lum.plnt_com: None}).where(lum.Landuse_lum.name == 'barr_lum').execute()
		except Exception as ex:
			if rollback_db is not None:
				self.emit_progress(50, "Error occurred. Rolling back database...")
				SetupProjectDatabase.rollback(project_db, rollback_db)
				self.emit_progress(100, "Error occurred.")
			sys.exit(str(ex))

	def updates_for_1_2_0(self, project_db, update_project_values, rollback_db):
		try:
			self.emit_progress(5, 'Running migrations...')
			migrator = SqliteMigrator(SqliteDatabase(project_db))
			migrate(
				migrator.drop_column('wetland_wet', 'rel'),
				migrator.add_column('wetland_wet', 'rel_id', ForeignKeyField(decision_table.D_table_dtl, decision_table.D_table_dtl.id, on_delete='SET NULL', null=True)),
				migrator.drop_column('wetland_wet', 'hyd_id'),
				migrator.add_column('wetland_wet', 'hyd_id', ForeignKeyField(reservoir.Hydrology_wet, reservoir.Hydrology_wet.id, on_delete='SET NULL', null=True)),
				migrator.drop_column('hru_data_hru', 'surf_stor'),
				migrator.add_column('hru_data_hru', 'surf_stor_id', ForeignKeyField(reservoir.Wetland_wet, reservoir.Wetland_wet.id, on_delete='SET NULL', null=True))
			)

			self.emit_progress(10, 'Updating datasets database...')
			dataset_plants.update({dataset_plants.lai_pot: 0.5}).where(dataset_plants.name == 'watr').execute()
			hru_parm_db.Plants_plt.update({hru_parm_db.Plants_plt.lai_pot: 0.5}).where(hru_parm_db.Plants_plt.name == 'watr').execute()

			datasets_change.Cal_parms_cal.update({datasets_change.Cal_parms_cal.abs_max: 10, datasets_change.Cal_parms_cal.units: 'm'}).where((datasets_change.Cal_parms_cal.name == 'flo_min') | (datasets_change.Cal_parms_cal.name == 'revap_min')).execute()
			if datasets_change.Cal_parms_cal.select().where(datasets_change.Cal_parms_cal.name == 'dep_bot').count() < 1:
				datasets_change.Cal_parms_cal.insert(name='dep_bot', obj_typ='aqu', abs_min=0, abs_max=10, units='m').execute()

			Var_range.update({Var_range.max_value: 2, Var_range.default_value: 0.05}).where((Var_range.table == 'aquifer_aqu') & (Var_range.variable == 'gw_flo')).execute()
			Var_range.update({Var_range.max_value: 10, Var_range.default_value: 10}).where((Var_range.table == 'aquifer_aqu') & (Var_range.variable == 'dep_wt')).execute()
			Var_range.update({
				Var_range.max_value: 10, 
				Var_range.default_value: 5, 
				Var_range.units: 'm', 
				Var_range.description: 'Water table depth for return flow to occur'
			}).where((Var_range.table == 'aquifer_aqu') & (Var_range.variable == 'flo_min')).execute()
			Var_range.update({
				Var_range.max_value: 10, 
				Var_range.default_value: 3, 
				Var_range.units: 'm', 
				Var_range.description: 'Water table depth for revap to occur'
			}).where((Var_range.table == 'aquifer_aqu') & (Var_range.variable == 'revap_min')).execute()
			Var_range.update({
				Var_range.description: 'Fraction of years to maturity'
			}).where((Var_range.table == 'plant_ini') & (Var_range.variable == 'yrs_init')).execute()

			datasets_init.Plant_ini_item.update({
				datasets_init.Plant_ini_item.yrs_init: 1
			}).where(datasets_init.Plant_ini_item.yrs_init == 15).execute()

			bm_50k_plants = ['aspn', 'cedr', 'frsd', 'frsd_SuHF', 'frsd_SuMs', 'frsd_SuSt', 'frsd_TeCF', 'frsd_TeMs', 'frsd_TeOF', 'frsd_TeST', 'frse', 'frse_SuDrF', 'frse_SuDs', 'frse_SuHF', 'frse_SuMs', 'frse_SuSt', 'frse_TeCF', 'frse_TeDs', 'frse_TeMs', 'frse_TeOF', 'frse_TeST', 'frst', 'frst_SuHF', 'frst_SuMs', 'frst_SuSt', 'frst_TeCF', 'frst_TeMs', 'frst_TeOF', 'frst_TeST', 'juni', 'ldgp', 'mapl', 'mesq', 'oak', 'oilp', 'pine', 'popl', 'rngb', 'rngb_SuDrF', 'rngb_SuDs', 'rngb_SuHF', 'rngb_SuMs', 'rngb_SuSt', 'rngb_TeCF', 'rngb_TeDs', 'rngb_TeMs', 'rngb_TeOF', 'rngb_TeST', 'rubr', 'swrn', 'wetf', 'wetl', 'wetn', 'will', 'wspr']
			bm_20k_plants = ['almd', 'appl', 'barr', 'cash', 'coco', 'coct', 'coff', 'grap', 'oliv', 'oran', 'orcd', 'papa', 'past', 'plan', 'rnge', 'rnge_SuDrF', 'rnge_SuDs', 'rnge_SuHF', 'rnge_SuMs', 'rnge_SuSt', 'rnge_TeCF', 'rnge_TeDs', 'rnge_TeMs', 'rnge_TeOF', 'rnge_TeST', 'waln']
			bm_50k_ids = dataset_plants.select(dataset_plants.id).where(dataset_plants.name << bm_50k_plants)
			bm_20k_ids = dataset_plants.select(dataset_plants.id).where(dataset_plants.name << bm_20k_plants)

			datasets_init.Plant_ini_item.update({
				datasets_init.Plant_ini_item.bm_init: 50000
			}).where(datasets_init.Plant_ini_item.plnt_name_id << bm_50k_ids).execute()
			datasets_init.Plant_ini_item.update({
				datasets_init.Plant_ini_item.bm_init: 20000
			}).where(datasets_init.Plant_ini_item.plnt_name_id << bm_20k_ids).execute()
			datasets_init.Plant_ini_item.update({
				datasets_init.Plant_ini_item.lc_status: 1,
				datasets_init.Plant_ini_item.yrs_init: 1
			}).where(datasets_init.Plant_ini_item.plnt_name.name == 'past').execute()
			datasets_init.Plant_ini_item.update({
				datasets_init.Plant_ini_item.lc_status: 1
			}).where(datasets_init.Plant_ini_item.plnt_name.name == 'barr').execute()

			datasets_basin.Codes_bsn.update({
				datasets_basin.Codes_bsn.pet: 1,
				datasets_basin.Codes_bsn.rtu_wq: 1,
				datasets_basin.Codes_bsn.wq_cha: 1
			}).execute()

			Version.update({Version.value: '1.2.0', Version.release_date: datetime.datetime.now()}).execute()

			if update_project_values:
				self.emit_progress(60, 'Updating project cal_parms_cal and aquifer_aqu...')
				change.Cal_parms_cal.update({change.Cal_parms_cal.abs_max: 10, change.Cal_parms_cal.units: 'm'}).where((change.Cal_parms_cal.name == 'flo_min') | (change.Cal_parms_cal.name == 'revap_min')).execute()
				if change.Cal_parms_cal.select().where(change.Cal_parms_cal.name == 'dep_bot').count() < 1:
					change.Cal_parms_cal.insert(name='dep_bot', obj_typ='aqu', abs_min=0, abs_max=10, units='m').execute()

				aquifer.Aquifer_aqu.update({
					aquifer.Aquifer_aqu.gw_flo: 0.05,
					aquifer.Aquifer_aqu.dep_wt: 10,
					aquifer.Aquifer_aqu.flo_min: 5,
					aquifer.Aquifer_aqu.revap_min: 3
				}).execute()

				init.Plant_ini_item.update({
					init.Plant_ini_item.yrs_init: 1
				}).where(init.Plant_ini_item.yrs_init == 15).execute()

				bm_50k_ids = hru_parm_db.Plants_plt.select(hru_parm_db.Plants_plt.id).where(hru_parm_db.Plants_plt.name << bm_50k_plants)
				bm_20k_ids = hru_parm_db.Plants_plt.select(hru_parm_db.Plants_plt.id).where(hru_parm_db.Plants_plt.name << bm_20k_plants)

				init.Plant_ini_item.update({
					init.Plant_ini_item.bm_init: 50000
				}).where(init.Plant_ini_item.plnt_name_id << bm_50k_ids).execute()
				init.Plant_ini_item.update({
					init.Plant_ini_item.bm_init: 20000
				}).where(init.Plant_ini_item.plnt_name_id << bm_20k_ids).execute()
				init.Plant_ini_item.update({
					init.Plant_ini_item.lc_status: 1,
					init.Plant_ini_item.yrs_init: 1
				}).where(init.Plant_ini_item.plnt_name.name == 'past').execute()
				init.Plant_ini_item.update({
					init.Plant_ini_item.lc_status: 1
				}).where(init.Plant_ini_item.plnt_name.name == 'barr').execute()

				basin.Codes_bsn.update({
					basin.Codes_bsn.pet: 1,
					basin.Codes_bsn.rtu_wq: 1,
					basin.Codes_bsn.wq_cha: 1
				}).execute()
		except Exception as ex:
			if rollback_db is not None:
				self.emit_progress(50, "Error occurred. Rolling back database...")
				SetupProjectDatabase.rollback(project_db, rollback_db)
				self.emit_progress(100, "Error occurred.")
			sys.exit(str(ex))

	def updates_for_1_1_0(self, project_db, datasets_db, rollback_db):
		try:
			conn = lib.open_db(project_db)
			aquifer_cols = lib.get_column_names(conn, 'aquifer_aqu')
			aquifer_col_names = [v['name'] for v in aquifer_cols]
			if 'gw_dp' not in aquifer_col_names:
				sys.exit('It appears some of your tables may have already been migrated even though your project version is still listed at 1.0.0. Please check your tables, restart the upgrade using the backup database in the DatabaseBackups folder, or contact support.')

			self.emit_progress(10, 'Running migrations...')
			base.db.create_tables([aquifer.Initial_aqu]) 
			migrator = SqliteMigrator(SqliteDatabase(project_db))
			migrate(
				migrator.rename_column('aquifer_aqu', 'gw_dp', 'dep_bot'),
				migrator.rename_column('aquifer_aqu', 'gw_ht', 'dep_wt'),
				migrator.drop_column('aquifer_aqu', 'delay'),
				migrator.add_column('aquifer_aqu', 'bf_max', DoubleField(default=1)),
				migrator.add_column('aquifer_aqu', 'init_id', ForeignKeyField(aquifer.Initial_aqu, aquifer.Initial_aqu.id, on_delete='SET NULL', null=True)),
				
				migrator.drop_column('codes_bsn', 'atmo_dep'),
				migrator.add_column('codes_bsn', 'atmo_dep', CharField(default='a')),

				migrator.drop_column('cal_parms_cal', 'units'),
				migrator.add_column('cal_parms_cal', 'units', CharField(null=True)),
				migrator.rename_table('codes_cal', 'codes_sft'),
				migrator.rename_column('codes_sft', 'landscape', 'hyd_hru'),
				migrator.rename_column('codes_sft', 'hyd', 'hyd_hrulte'),
				migrator.rename_table('ls_parms_cal', 'wb_parms_sft'),
				migrator.rename_table('ch_parms_cal', 'ch_sed_parms_sft'),
				migrator.rename_table('pl_parms_cal', 'plant_parms_sft'),
				
				migrator.drop_column('channel_cha', 'pest_id'),
				migrator.drop_column('channel_cha', 'ls_link_id'),
				migrator.drop_column('channel_cha', 'aqu_link_id'),
				migrator.drop_column('initial_cha', 'vol'),
				migrator.drop_column('initial_cha', 'sed'),
				migrator.drop_column('initial_cha', 'ptl_n'),
				migrator.drop_column('initial_cha', 'no3_n'),
				migrator.drop_column('initial_cha', 'no2_n'),
				migrator.drop_column('initial_cha', 'nh4_n'),
				migrator.drop_column('initial_cha', 'ptl_p'),
				migrator.drop_column('initial_cha', 'sol_p'),
				migrator.drop_column('initial_cha', 'secchi'),
				migrator.drop_column('initial_cha', 'sand'),
				migrator.drop_column('initial_cha', 'silt'),
				migrator.drop_column('initial_cha', 'clay'),
				migrator.drop_column('initial_cha', 'sm_agg'),
				migrator.drop_column('initial_cha', 'lg_agg'),
				migrator.drop_column('initial_cha', 'gravel'),
				migrator.drop_column('initial_cha', 'chla'),
				migrator.drop_column('initial_cha', 'sol_pest'),
				migrator.drop_column('initial_cha', 'srb_pest'),
				migrator.drop_column('initial_cha', 'lp_bact'),
				migrator.drop_column('initial_cha', 'p_bact'),
				migrator.add_column('initial_cha', 'org_min_id', ForeignKeyField(init.Om_water_ini, init.Om_water_ini.id, on_delete='SET NULL', null=True)),
				migrator.add_column('initial_cha', 'pest_id', ForeignKeyField(init.Pest_water_ini, init.Pest_water_ini.id, on_delete='SET NULL', null=True)),
				migrator.add_column('initial_cha', 'path_id', ForeignKeyField(init.Path_water_ini, init.Path_water_ini.id, on_delete='SET NULL', null=True)),
				migrator.add_column('initial_cha', 'hmet_id', ForeignKeyField(init.Hmet_water_ini, init.Hmet_water_ini.id, on_delete='SET NULL', null=True)),
				migrator.add_column('initial_cha', 'salt_id', ForeignKeyField(init.Salt_water_ini, init.Salt_water_ini.id, on_delete='SET NULL', null=True)),

				migrator.add_column('d_table_dtl', 'file_name', CharField(null=True)),
				migrator.add_column('d_table_dtl_act', 'const2', DoubleField(default=0)),
				migrator.rename_column('d_table_dtl_act', 'application', 'fp'),
				migrator.rename_column('d_table_dtl_act', 'type', 'option'),

				migrator.drop_column('exco_om_exc', 'sol_pest'),
				migrator.drop_column('exco_om_exc', 'srb_pest'),
				migrator.drop_column('exco_om_exc', 'p_bact'),
				migrator.drop_column('exco_om_exc', 'lp_bact'),
				migrator.drop_column('exco_om_exc', 'metl1'),
				migrator.drop_column('exco_om_exc', 'metl2'),
				migrator.drop_column('exco_om_exc', 'metl3'),
				migrator.rename_column('exco_om_exc', 'ptl_n', 'orgn'),
				migrator.rename_column('exco_om_exc', 'ptl_p', 'sedp'),
				migrator.rename_column('exco_om_exc', 'no3_n', 'no3'),
				migrator.rename_column('exco_om_exc', 'sol_p', 'solp'),
				migrator.rename_column('exco_om_exc', 'nh3_n', 'nh3'),
				migrator.rename_column('exco_om_exc', 'no2_n', 'no2'),
				migrator.rename_column('exco_om_exc', 'bod', 'cbod'),
				migrator.rename_column('exco_om_exc', 'oxy', 'dox'),
				migrator.rename_column('exco_om_exc', 'sm_agg', 'sag'),
				migrator.rename_column('exco_om_exc', 'lg_agg', 'lag'),
				migrator.drop_column('exco_pest_exc', 'aatrex_sol'),
				migrator.drop_column('exco_pest_exc', 'aatrex_sor'),
				migrator.drop_column('exco_pest_exc', 'banvel_sol'),
				migrator.drop_column('exco_pest_exc', 'banvel_sor'),
				migrator.drop_column('exco_pest_exc', 'prowl_sol'),
				migrator.drop_column('exco_pest_exc', 'prowl_sor'),
				migrator.drop_column('exco_pest_exc', 'roundup_sol'),
				migrator.drop_column('exco_pest_exc', 'roundup_sor'),
				migrator.drop_column('exco_path_exc', 'fecals_sol'),
				migrator.drop_column('exco_path_exc', 'fecals_sor'),
				migrator.drop_column('exco_path_exc', 'e_coli_sol'),
				migrator.drop_column('exco_path_exc', 'e_coli_sor'),
				migrator.drop_column('exco_hmet_exc', 'mercury_sol'),
				migrator.drop_column('exco_hmet_exc', 'mercury_sor'),
				migrator.drop_column('exco_salt_exc', 'sodium_sol'),
				migrator.drop_column('exco_salt_exc', 'sodium_sor'),
				migrator.drop_column('exco_salt_exc', 'magnesium_sol'),
				migrator.drop_column('exco_salt_exc', 'magnesium_sor'),

				migrator.drop_column('fertilizer_frt', 'p_bact'),
				migrator.drop_column('fertilizer_frt', 'lp_bact'),
				migrator.drop_column('fertilizer_frt', 'sol_bact'),
				migrator.add_column('fertilizer_frt', 'pathogens', CharField(null=True)),

				migrator.drop_column('hru_data_hru', 'soil_nut_id'),
				migrator.add_column('hru_data_hru', 'soil_plant_init_id', ForeignKeyField(init.Soil_plant_ini, init.Soil_plant_ini.id, null=True, on_delete='SET NULL')),

				migrator.drop_column('hydrology_hyd', 'dp_imp'),

				migrator.rename_table('pest_soil_ini', 'pest_hru_ini'),
				migrator.rename_table('pest_soil_ini_item', 'pest_hru_ini_item'),
				migrator.rename_table('path_soil_ini', 'path_hru_ini'),
				migrator.rename_table('hmet_soil_ini', 'hmet_hru_ini'),
				migrator.rename_table('salt_soil_ini', 'salt_hru_ini'),

				migrator.add_column('plant_ini', 'rot_yr_ini', IntegerField(default=1)),
				migrator.rename_column('plants_plt', 'plnt_hu', 'days_mat'),

				migrator.drop_column('recall_dat', 'sol_pest'),
				migrator.drop_column('recall_dat', 'srb_pest'),
				migrator.drop_column('recall_dat', 'p_bact'),
				migrator.drop_column('recall_dat', 'lp_bact'),
				migrator.drop_column('recall_dat', 'metl1'),
				migrator.drop_column('recall_dat', 'metl2'),
				migrator.drop_column('recall_dat', 'metl3'),

				migrator.drop_column('reservoir_res', 'pest_id'),
				migrator.drop_column('wetland_wet', 'pest_id'),
				migrator.drop_column('initial_res', 'vol'),
				migrator.drop_column('initial_res', 'sed'),
				migrator.drop_column('initial_res', 'ptl_n'),
				migrator.drop_column('initial_res', 'no3_n'),
				migrator.drop_column('initial_res', 'no2_n'),
				migrator.drop_column('initial_res', 'nh3_n'),
				migrator.drop_column('initial_res', 'ptl_p'),
				migrator.drop_column('initial_res', 'sol_p'),
				migrator.drop_column('initial_res', 'secchi'),
				migrator.drop_column('initial_res', 'sand'),
				migrator.drop_column('initial_res', 'silt'),
				migrator.drop_column('initial_res', 'clay'),
				migrator.drop_column('initial_res', 'sm_agg'),
				migrator.drop_column('initial_res', 'lg_agg'),
				migrator.drop_column('initial_res', 'gravel'),
				migrator.drop_column('initial_res', 'chla'),
				migrator.drop_column('initial_res', 'sol_pest'),
				migrator.drop_column('initial_res', 'srb_pest'),
				migrator.drop_column('initial_res', 'lp_bact'),
				migrator.drop_column('initial_res', 'p_bact'),
				migrator.add_column('initial_res', 'org_min_id', ForeignKeyField(init.Om_water_ini, init.Om_water_ini.id, on_delete='SET NULL', null=True)),
				migrator.add_column('initial_res', 'pest_id', ForeignKeyField(init.Pest_water_ini, init.Pest_water_ini.id, on_delete='SET NULL', null=True)),
				migrator.add_column('initial_res', 'path_id', ForeignKeyField(init.Path_water_ini, init.Path_water_ini.id, on_delete='SET NULL', null=True)),
				migrator.add_column('initial_res', 'hmet_id', ForeignKeyField(init.Hmet_water_ini, init.Hmet_water_ini.id, on_delete='SET NULL', null=True)),
				migrator.add_column('initial_res', 'salt_id', ForeignKeyField(init.Salt_water_ini, init.Salt_water_ini.id, on_delete='SET NULL', null=True)),
				migrator.add_column('sediment_res', 'carbon', DoubleField(default=0)),
				migrator.add_column('sediment_res', 'bd', DoubleField(default=0)),

				migrator.drop_column('rout_unit_ele', 'hyd_typ'),
				migrator.rename_column('rout_unit_ele', 'rtu_id', 'old_rtu_id'),
				migrator.drop_index('rout_unit_ele', 'rout_unit_ele_rtu_id'),
				migrator.add_column('rout_unit_ele', 'rtu_id', ForeignKeyField(connect.Rout_unit_con, connect.Rout_unit_con.id, on_delete='SET NULL', null=True)),

				migrator.drop_not_null('soils_sol', 'texture'),
			)

			self.emit_progress(30, 'Updating rout_unit_ele foreign keys...')
			# Move foreign key from rout_unit_rtu to rout_unit_con
			lib.execute_non_query(base.db.database, 'UPDATE rout_unit_ele SET rtu_id = old_rtu_id')
			migrate(
				migrator.drop_column('rout_unit_ele', 'old_rtu_id')
			)

			self.emit_progress(35, 'Drop and re-creating recall, change, init, lte, constituents, dr, irr ops, and exco tables...')
			# Drop and re-create recall tables since they had no data and had significant structure changes
			base.db.drop_tables([recall.Recall_rec, recall.Recall_dat])
			base.db.create_tables([recall.Recall_rec, recall.Recall_dat])

			# Drop and re-create calibration tables
			base.db.drop_tables([change.Calibration_cal]) 
			base.db.create_tables([change.Calibration_cal, change.Calibration_cal_cond, change.Calibration_cal_elem, change.Water_balance_sft, change.Water_balance_sft_item, change.Plant_gro_sft, change.Plant_gro_sft_item, change.Ch_sed_budget_sft, change.Ch_sed_budget_sft_item])

			# Drop and re-create irrigation ops table
			base.db.drop_tables([ops.Irr_ops])
			base.db.create_tables([ops.Irr_ops])
			lib.copy_table('irr_ops', datasets_db, project_db)

			# Drop and re-create init tables since they had no data and had significant structure changes
			base.db.drop_tables([init.Pest_hru_ini, init.Pest_hru_ini_item, init.Pest_water_ini, init.Path_hru_ini, init.Path_water_ini, init.Hmet_hru_ini, init.Hmet_water_ini, init.Salt_hru_ini, init.Salt_water_ini])
			base.db.create_tables([init.Om_water_ini, init.Pest_hru_ini, init.Pest_hru_ini_item, init.Pest_water_ini, init.Path_hru_ini, init.Path_water_ini, init.Hmet_hru_ini, init.Hmet_water_ini, init.Salt_hru_ini, init.Salt_water_ini, init.Soil_plant_ini])
			
			lib.bulk_insert(base.db, init.Om_water_ini, init.Om_water_ini.get_default_data())
			channel.Initial_cha.update({channel.Initial_cha.org_min: 1}).execute()
			reservoir.Initial_res.update({reservoir.Initial_res.org_min: 1}).execute()

			self.emit_progress(40, 'Updating channels tables...')
			base.db.drop_tables([channel.Channel_lte_cha])
			base.db.create_tables([channel.Hyd_sed_lte_cha, channel.Channel_lte_cha])
			hydrology_chas = []
			for hc in channel.Hydrology_cha.select():
				hyd_cha = {
					'id': hc.id,
					'name': hc.name,
					'order': 'first',
					'wd': hc.wd,
					'dp': hc.dp,
					'slp': hc.slp,
					'len': hc.len,
					'mann': hc.mann,
					'k': hc.k,
					'erod_fact': 0.01,
					'cov_fact': 0.005,
					'hc_cov': 0,
					'eq_slp': 0.001,
					'd50': 12,
					'clay': 50,
					'carbon': 0.04,
					'dry_bd': 1,
					'side_slp': 0.5,
					'bed_load': 0.5,
					't_conc': 10,
					'shear_bnk': 0.75,
					'hc_erod': 0.1,
					'hc_ht': 0.3,
					'hc_len': 0.3
				}
				hydrology_chas.append(hyd_cha)
			lib.bulk_insert(base.db, channel.Hyd_sed_lte_cha, hydrology_chas)

			channel_chas = []
			for cha in channel.Channel_cha.select():
				chan_cha = {
					'id': cha.id,
					'name': cha.name,
					'hyd': cha.hyd_id,
					'init': cha.init_id,
					'nut': cha.nut_id
				}
				channel_chas.append(chan_cha)
			lib.bulk_insert(base.db, channel.Channel_lte_cha, channel_chas)

			channel_cons = []
			channel_con_outs = []
			for cc in connect.Channel_con.select():
				chan_con = {
					'lcha': cc.cha_id,
					'id': cc.id,
					'name': cc.name,
					'gis_id': cc.gis_id,
					'lat': cc.lat,
					'lon': cc.lon,
					'elev': cc.elev,
					'wst': cc.wst_id,
					'area': cc.area,
					'ovfl': cc.ovfl,
					'rule': cc.rule
				}
				channel_cons.append(chan_con)

				for co in cc.con_outs:
					cha_out = {
						'id': co.id,
						'chandeg_con_id': co.channel_con.id,
						'order': co.order,
						'obj_typ': co.obj_typ,
						'obj_id': co.obj_id,
						'hyd_typ': co.hyd_typ,
						'frac': co.frac
					}
					channel_con_outs.append(cha_out)
			lib.bulk_insert(base.db, connect.Chandeg_con, channel_cons)
			lib.bulk_insert(base.db, connect.Chandeg_con_out, channel_con_outs)

			# Update from cha to sdc
			connect.Chandeg_con_out.update(obj_typ='sdc').where(connect.Chandeg_con_out.obj_typ=='cha').execute()
			connect.Hru_con_out.update(obj_typ='sdc').where(connect.Hru_con_out.obj_typ=='cha').execute()
			connect.Rout_unit_con_out.update(obj_typ='sdc').where(connect.Rout_unit_con_out.obj_typ=='cha').execute()
			connect.Aquifer_con_out.update(obj_typ='sdc').where(connect.Aquifer_con_out.obj_typ=='cha').execute()
			connect.Reservoir_con_out.update(obj_typ='sdc').where(connect.Reservoir_con_out.obj_typ=='cha').execute()
			connect.Recall_con_out.update(obj_typ='sdc').where(connect.Recall_con_out.obj_typ=='cha').execute()
			connect.Exco_con_out.update(obj_typ='sdc').where(connect.Exco_con_out.obj_typ=='cha').execute()
			connect.Delratio_con_out.update(obj_typ='sdc').where(connect.Delratio_con_out.obj_typ=='cha').execute()

			connect.Channel_con.delete().execute()
			connect.Channel_con_out.delete().execute()
			channel.Channel_cha.delete().execute()
			channel.Hydrology_cha.delete().execute()
			channel.Sediment_cha.delete().execute()
			
			# Drop and re-create all dr tables since not used previously
			base.db.drop_tables([dr.Dr_om_del, dr.Dr_pest_del, dr.Dr_path_del, dr.Dr_hmet_del, dr.Dr_salt_del, dr.Delratio_del])
			base.db.create_tables([dr.Dr_om_del, 
									dr.Dr_pest_del, dr.Dr_pest_col, dr.Dr_pest_val,
									dr.Dr_path_del, dr.Dr_path_col, dr.Dr_path_val,
									dr.Dr_hmet_del, dr.Dr_hmet_col, dr.Dr_hmet_val, 
									dr.Dr_salt_del, dr.Dr_salt_col, dr.Dr_salt_val, 
									dr.Delratio_del])

			# Drop and re-create exco tables since not used previously
			base.db.create_tables([exco.Exco_pest_col, exco.Exco_pest_val,
									exco.Exco_path_col, exco.Exco_path_val,
									exco.Exco_hmet_col, exco.Exco_hmet_val, 
									exco.Exco_salt_col, exco.Exco_salt_val])
			
			# Drop and re-create constituents.cs
			base.db.drop_tables([simulation.Constituents_cs])
			base.db.create_tables([simulation.Constituents_cs])

			# LTE tables
			base.db.drop_tables([hru.Hru_lte_hru])
			base.db.create_tables([hru.Hru_lte_hru, soils.Soils_lte_sol])

			self.emit_progress(50, 'Update aquifer, calibration parameters, fertilizer, and pesticides data...')
			aquifer.Initial_aqu.insert(name='initaqu1', org_min=1).execute()
			aquifer.Aquifer_aqu.update({aquifer.Aquifer_aqu.dep_bot: 10, aquifer.Aquifer_aqu.dep_wt: 5, aquifer.Aquifer_aqu.spec_yld: 0.05, aquifer.Aquifer_aqu.init: 1}).execute()

			lib.copy_table('cal_parms_cal', datasets_db, project_db)

			# Drop and re-create pesticide_pst
			base.db.drop_tables([hru_parm_db.Pesticide_pst])
			base.db.create_tables([hru_parm_db.Pesticide_pst])
			lib.copy_table('pesticide_pst', datasets_db, project_db)

			sp = init.Soil_plant_ini.create(
				name='soilplant1',
				sw_frac=0,
				nutrients=1
			)

			hru.Hru_data_hru.update({hru.Hru_data_hru.soil_plant_init: sp.id}).execute()

			hru_parm_db.Fertilizer_frt.delete().execute()
			lib.copy_table('fertilizer_frt', datasets_db, project_db, include_id=True)

			self.emit_progress(60, 'Update decision tables...')
			res_rels = {}
			for r in reservoir.Reservoir_res.select():
				res_rels[r.id] = r.rel.name

			decision_table.D_table_dtl.delete().execute()
			decision_table.D_table_dtl_cond.delete().execute()
			decision_table.D_table_dtl_cond_alt.delete().execute()
			decision_table.D_table_dtl_act.delete().execute()
			decision_table.D_table_dtl_act_out.delete().execute()
			lib.copy_table('d_table_dtl', datasets_db, project_db, include_id=True)
			lib.copy_table('d_table_dtl_cond', datasets_db, project_db, include_id=True)
			lib.copy_table('d_table_dtl_cond_alt', datasets_db, project_db, include_id=True)
			lib.copy_table('d_table_dtl_act', datasets_db, project_db, include_id=True)
			lib.copy_table('d_table_dtl_act_out', datasets_db, project_db, include_id=True)

			for r in reservoir.Reservoir_res.select():
				try:
					d_tbl_name = res_rels.get(r.id, None)
					if d_tbl_name is not None:
						r.rel_id = decision_table.D_table_dtl.get(decision_table.D_table_dtl.name == d_tbl_name).id
						r.save()
				except decision_table.D_table_dtl.DoesNotExist:
					pass

			self.emit_progress(70, 'Update management schedules...')
			lum.Management_sch.delete().execute()
			lum.Management_sch_auto.delete().execute()
			lum.Management_sch_op.delete().execute()
			lum.Landuse_lum.update(cal_group=None,mgt=None).execute()
			for lu in lum.Landuse_lum.select():
				plant_name = lu.name.replace('_lum', '')

				plant = hru_parm_db.Plants_plt.get_or_none(hru_parm_db.Plants_plt.name == plant_name)
				if plant is not None:
					new_d_table_id = None
					if plant.plnt_typ == 'warm_annual':
						new_d_table_id = GisImport.insert_decision_table(plant.name, 'pl_hv_corn')
					elif plant.plnt_typ == 'cold_annual':
						new_d_table_id = GisImport.insert_decision_table(plant.name, 'pl_hv_wwht') 

					if new_d_table_id is not None:
						mgt_name = '{plant}_rot'.format(plant=plant.name)
						
						mgt_id = lum.Management_sch.insert(
							name = mgt_name
						).execute()
						lum.Management_sch_auto.insert(
							management_sch=mgt_id,
							d_table=new_d_table_id
						).execute()

						lu.mgt = mgt_id
						lu.save()

			self.emit_progress(80, 'Update file_cio and print tables...')
			simulation.Print_prt_object.create(name='pest', daily=False, monthly=False, yearly=False, avann=False, print_prt_id=1)

			File_cio.delete().execute()
			file_cios = []
			for f in dataset_file_cio.select():
				file_cio = {
					'classification': f.classification.id,
					'order_in_class': f.order_in_class,
					'file_name': f.default_file_name
				}
				file_cios.append(file_cio)

			lib.bulk_insert(base.db, File_cio, file_cios)

			self.emit_progress(90, 'Update plants table to use days_mat column...')
			for p in hru_parm_db.Plants_plt:
				dp = dataset_plants.get_or_none(dataset_plants.name == p.name)
				if dp is not None:
					p.days_mat = dp.days_mat
				else:
					p.days_mat = 0
				p.save()
		except Exception as ex:
			if rollback_db is not None:
				self.emit_progress(50, "Error occurred. Rolling back database...")
				SetupProjectDatabase.rollback(project_db, rollback_db)
				self.emit_progress(100, "Error occurred.")
			sys.exit(str(ex))


if __name__ == '__main__':
	sys.stdout = Unbuffered(sys.stdout)
	parser = argparse.ArgumentParser(description="Update SWAT+ project database")
	parser.add_argument("--project_db_file", type=str, help="full path of project SQLite database file", nargs="?")
	parser.add_argument("--datasets_db_file", type=str, help="full path of datasets SQLite database file", nargs="?")
	parser.add_argument("--editor_version", type=str, help="editor version", nargs="?")
	parser.add_argument("--update_project_values", type=str, help="y/n update project values (default n)", nargs="?")
	parser.add_argument("--reimport_gis", type=str, help="y/n re-import GIS data (default n)", nargs="?")

	args = parser.parse_args()

	update_project_values = True if args.update_project_values == "y" else False
	reimport_gis = True if args.reimport_gis == "y" else False
	api = UpdateProject(args.project_db_file, args.editor_version, args.datasets_db_file, update_project_values, reimport_gis)
