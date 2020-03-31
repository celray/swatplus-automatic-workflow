from peewee import *
from . import base, aquifer, channel, hyd, losses, misc, nutbal, plantwx, reservoir, waterbal, pest


class SetupOutputDatabase():
	@staticmethod
	def init(db:str):
		base.db.init(db, pragmas={'journal_mode': 'off'})

	@staticmethod
	def create_tables():
		base.db.create_tables([
			base.Project_config, base.Table_group, base.Definition
		])

		base.db.create_tables([
			aquifer.Basin_aqu_day, aquifer.Basin_aqu_mon, aquifer.Basin_aqu_yr, aquifer.Basin_aqu_aa,
			aquifer.Aquifer_day, aquifer.Aquifer_mon, aquifer.Aquifer_yr, aquifer.Aquifer_aa
		])

		base.db.create_tables([
			channel.Basin_cha_day, channel.Basin_cha_mon, channel.Basin_cha_yr, channel.Basin_cha_aa,
			channel.Channel_day, channel.Channel_mon, channel.Channel_yr, channel.Channel_aa,
			channel.Basin_sd_cha_day, channel.Basin_sd_cha_mon, channel.Basin_sd_cha_yr, channel.Basin_sd_cha_aa,
			channel.Channel_sd_day, channel.Channel_sd_mon, channel.Channel_sd_yr, channel.Channel_sd_aa,
			channel.Basin_sd_chamorph_day, channel.Basin_sd_chamorph_mon, channel.Basin_sd_chamorph_yr, channel.Basin_sd_chamorph_aa,
			channel.Channel_sdmorph_day, channel.Channel_sdmorph_mon, channel.Channel_sdmorph_yr, channel.Channel_sdmorph_aa
		])

		base.db.create_tables([
			hyd.Basin_psc_day, hyd.Basin_psc_mon, hyd.Basin_psc_yr, hyd.Basin_psc_aa,
			hyd.Hydin_day, hyd.Hydin_mon, hyd.Hydin_yr, hyd.Hydin_aa,
			hyd.Hydout_day, hyd.Hydout_mon, hyd.Hydout_yr, hyd.Hydout_aa,
			hyd.Ru_day, hyd.Ru_mon, hyd.Ru_yr, hyd.Ru_aa,
			hyd.Deposition_day, hyd.Deposition_mon, hyd.Deposition_yr, hyd.Deposition_aa,
		])

		base.db.create_tables([
			losses.Basin_ls_day, losses.Basin_ls_mon, losses.Basin_ls_yr, losses.Basin_ls_aa,
			losses.Lsunit_ls_day, losses.Lsunit_ls_mon, losses.Lsunit_ls_yr, losses.Lsunit_ls_aa,
			losses.Hru_ls_day, losses.Hru_ls_mon, losses.Hru_ls_yr, losses.Hru_ls_aa,
			losses.Hru_lte_ls_day, losses.Hru_lte_ls_mon, losses.Hru_lte_ls_yr, losses.Hru_lte_ls_aa
		])

		base.db.create_tables([
			misc.Mgt_out, misc.Flow_duration_curve, misc.Crop_yld_aa, misc.Soil_nutcarb_out,
			misc.Basin_crop_yld_aa, misc.Basin_crop_yld_yr
		])

		base.db.create_tables([
			nutbal.Basin_nb_day, nutbal.Basin_nb_mon, nutbal.Basin_nb_yr, nutbal.Basin_nb_aa,
			nutbal.Lsunit_nb_day, nutbal.Lsunit_nb_mon, nutbal.Lsunit_nb_yr, nutbal.Lsunit_nb_aa,
			nutbal.Hru_nb_day, nutbal.Hru_nb_mon, nutbal.Hru_nb_yr, nutbal.Hru_nb_aa
		])

		base.db.create_tables([
			plantwx.Basin_pw_day, plantwx.Basin_pw_mon, plantwx.Basin_pw_yr, plantwx.Basin_pw_aa,
			plantwx.Lsunit_pw_day, plantwx.Lsunit_pw_mon, plantwx.Lsunit_pw_yr, plantwx.Lsunit_pw_aa,
			plantwx.Hru_pw_day, plantwx.Hru_pw_mon, plantwx.Hru_pw_yr, plantwx.Hru_pw_aa,
			plantwx.Hru_lte_pw_day, plantwx.Hru_lte_pw_mon, plantwx.Hru_lte_pw_yr, plantwx.Hru_lte_pw_aa
		])

		base.db.create_tables([
			reservoir.Basin_res_day, reservoir.Basin_res_mon, reservoir.Basin_res_yr, reservoir.Basin_res_aa,
			reservoir.Reservoir_day, reservoir.Reservoir_mon, reservoir.Reservoir_yr, reservoir.Reservoir_aa,
			reservoir.Wetland_day, reservoir.Wetland_mon, reservoir.Wetland_yr, reservoir.Wetland_aa
		])

		base.db.create_tables([
			waterbal.Basin_wb_day, waterbal.Basin_wb_mon, waterbal.Basin_wb_yr, waterbal.Basin_wb_aa,
			waterbal.Lsunit_wb_day, waterbal.Lsunit_wb_mon, waterbal.Lsunit_wb_yr, waterbal.Lsunit_wb_aa,
			waterbal.Hru_wb_day, waterbal.Hru_wb_mon, waterbal.Hru_wb_yr, waterbal.Hru_wb_aa,
			waterbal.Hru_lte_wb_day, waterbal.Hru_lte_wb_mon, waterbal.Hru_lte_wb_yr, waterbal.Hru_lte_wb_aa
		])

		base.db.create_tables([
			pest.Hru_pest_day, pest.Hru_pest_mon, pest.Hru_pest_yr, pest.Hru_pest_aa,
			pest.Basin_ls_pest_day, pest.Basin_ls_pest_mon, pest.Basin_ls_pest_yr, pest.Basin_ls_pest_aa,
			pest.Basin_ch_pest_day, pest.Basin_ch_pest_mon, pest.Basin_ch_pest_yr, pest.Basin_ch_pest_aa,
			pest.Basin_res_pest_day, pest.Basin_res_pest_mon, pest.Basin_ls_pest_yr, pest.Basin_res_pest_aa,
			pest.Channel_pest_day, pest.Channel_pest_mon, pest.Channel_pest_yr, pest.Channel_pest_aa,
			pest.Reservoir_pest_day, pest.Reservoir_pest_mon, pest.Reservoir_pest_yr, pest.Reservoir_pest_aa,
			pest.Basin_aqu_pest_day, pest.Basin_aqu_pest_mon, pest.Basin_aqu_pest_yr, pest.Basin_aqu_pest_aa,
			pest.Aquifer_pest_day, pest.Aquifer_pest_mon, pest.Aquifer_pest_yr, pest.Aquifer_pest_aa
		])
