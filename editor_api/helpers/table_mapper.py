from database.project import connect, climate, channel, aquifer, reservoir, hydrology, hru, hru_parm_db, lum, soils, routing_unit, dr, init, decision_table, exco, dr, structural, ops, regions, change, recall

obj_typs = {
	"hru": connect.Hru_con,
	"hlt": connect.Hru_lte_con,
	"ru": connect.Rout_unit_con,
	"aqu": connect.Aquifer_con,
	"cha": connect.Channel_con,
	"res": connect.Reservoir_con,
	"rec": connect.Recall_con,
	"exc": connect.Exco_con,
	"dr": connect.Delratio_con,
	"out": connect.Outlet_con,
	"mfl": connect.Modflow_con,
	"sdc": connect.Chandeg_con,
	"cli": climate.Weather_sta_cli
}

cal_to_obj = {
	"hru": "hru",
	"sol": "hru",
	"swq": "cha",
	"rte": "cha",
	"res": "res",
	"gw": "aqu",
	"hlt": "hlt",
	"cli": "cli",
	"bsn": None
}

types = {
	"aqu": aquifer.Aquifer_aqu,
	"init_aqu": aquifer.Initial_aqu,

	"cal_parms": change.Cal_parms_cal,
	"calibration": change.Calibration_cal,
	"wb_parms_sft": change.Wb_parms_sft,
	"chsed_parms_sft": change.Ch_sed_parms_sft,
	"plant_parms_sft": change.Plant_parms_sft,
	"water_balance_sft": change.Water_balance_sft,
	"ch_sed_budget_sft": change.Ch_sed_budget_sft,
	"plant_gro_sft": change.Plant_gro_sft,

	"cha": channel.Channel_cha,
	"lcha": channel.Channel_lte_cha,
	"init_cha": channel.Initial_cha,
	"hyd_cha": channel.Hydrology_cha,
	"sed_cha": channel.Sediment_cha,
	"nut_cha": channel.Nutrients_cha,
	"hyd_sed_lte_cha": channel.Hyd_sed_lte_cha,

	"wgn": climate.Weather_wgn_cli,
	"wgn_mon": climate.Weather_wgn_cli_mon,
	"wst": climate.Weather_sta_cli,

	"aqu_con": connect.Aquifer_con,
	"cha_con": connect.Channel_con,
	"hru_con": connect.Hru_con,
	"res_con": connect.Reservoir_con,
	"exco_con": connect.Exco_con,
	"dr_con": connect.Delratio_con,
	"rtu_con": connect.Rout_unit_con,
	"rec_con": connect.Recall_con,
	"out_con": connect.Outlet_con,
	"hru_lte_con": connect.Hru_lte_con,
	"modflow_con": connect.Modflow_con,
	"chandeg_con": connect.Chandeg_con,
	"rout_unit_ele": connect.Rout_unit_ele,

	"lum.dtl": decision_table.D_table_dtl,
	"res_rel.dtl": decision_table.D_table_dtl,
	"scen_lu.dtl": decision_table.D_table_dtl,
	"flo_con.dtl": decision_table.D_table_dtl,
	"dtl": decision_table.D_table_dtl,

	"exco": exco.Exco_exc,
	"om_exc": exco.Exco_om_exc,
	"pest_exc": exco.Exco_pest_exc,
	"path_exc": exco.Exco_path_exc,
	"hmet_exc": exco.Exco_hmet_exc,
	"salt_exc": exco.Exco_salt_exc,

	"dlr": dr.Delratio_del,
	"om_del": dr.Dr_om_del,
	"pest_del": dr.Dr_pest_del,
	"path_del": dr.Dr_path_del,
	"hmet_del": dr.Dr_hmet_del,
	"salt_del": dr.Dr_salt_del,

	"hru": hru.Hru_data_hru,
	"lhru": hru.Hru_lte_hru,

	"fert": hru_parm_db.Fertilizer_frt,
	"plant": hru_parm_db.Plants_plt,
	"till": hru_parm_db.Tillage_til,
	"snow": hru_parm_db.Snow_sno,
	"urban": hru_parm_db.Urban_urb,
	"sep": hru_parm_db.Septic_sep,
	"pest": hru_parm_db.Pesticide_pst,

	"hyd": hydrology.Hydrology_hyd,
	"fld": hydrology.Field_fld,
	"topo": hydrology.Topography_hyd,

	"plant_ini": init.Plant_ini,
	"soil_plant_ini": init.Soil_plant_ini,
	"om_water_ini": init.Om_water_ini,
	"pest_water_ini": init.Pest_water_ini,
	"path_water_ini": init.Path_water_ini,
	"hmet_water_ini": init.Hmet_water_ini,
	"salt_water_ini": init.Salt_water_ini,
	"pest_hru_ini": init.Pest_hru_ini,
	"path_hru_ini": init.Path_hru_ini,
	"hmet_hru_ini": init.Hmet_hru_ini,
	"salt_hru_ini": init.Salt_hru_ini,

	"lu_mgt": lum.Landuse_lum,
	"mgt_sch": lum.Management_sch,
	"cntable": lum.Cntable_lum,
	"cons_prac": lum.Cons_prac_lum,
	"ovntable": lum.Ovn_table_lum,

	"harv_ops": ops.Harv_ops,
	"graze_ops": ops.Graze_ops,
	"irr_ops": ops.Irr_ops,
	"sweep_ops": ops.Sweep_ops,
	"fire_ops": ops.Fire_ops,
	"chem_app_ops": ops.Chem_app_ops,

	"rec": recall.Recall_rec,
	"rec_dat": recall.Recall_dat,
	"rec_cnst": recall.Recall_dat,

	"ls_unit_def": regions.Ls_unit_def,
	"ls_unit_ele": regions.Ls_unit_ele,

	"res": reservoir.Reservoir_res,
	"init_res": reservoir.Initial_res,
	"hyd_res": reservoir.Hydrology_res,
	"sed_res": reservoir.Sediment_res,
	"nut_res": reservoir.Nutrients_res,
	"wet_res": reservoir.Wetland_wet,
	"hyd_wet": reservoir.Hydrology_wet,

	"rtu": routing_unit.Rout_unit_rtu,

	"soil": soils.Soils_sol,
	"soil_nut": soils.Nutrients_sol,
	"soil_lte": soils.Soils_lte_sol,

	"tiledrain_str": structural.Tiledrain_str,
	"septic_str": structural.Septic_str,
	"filterstrip_str": structural.Filterstrip_str,
	"grassedww_str": structural.Grassedww_str,
	"bmpuser_str": structural.Bmpuser_str
}