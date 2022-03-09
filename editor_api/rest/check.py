from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project.setup import SetupProjectDatabase
from database.output.setup import SetupOutputDatabase
from database.output import check, aquifer, channel, hyd, losses, misc, nutbal, plantwx, reservoir, waterbal, pest, base
from database.project import connect, climate, gis, regions, simulation
from database import lib

import traceback


def get_in_out_percent(value_in, value_out):
	return 0 if value_in == 0 else (value_in - value_out) / value_in * 100


def get_info(has_project_config):
	info = check.CheckInfo()

	time_sim = simulation.Time_sim.get_or_none()
	if time_sim is not None:
		info.simulationLength = time_sim.yrc_end - time_sim.yrc_start + 1

	prt = simulation.Print_prt.get_or_none()
	if prt is not None:
		info.warmUp = prt.nyskip

	info.hrus = connect.Hru_con.select().count()
	info.subbasins = gis.Gis_subbasins.select().count()
	info.lsus = regions.Ls_unit_def.select().count()
	info.weatherMethod = 'Observed' if climate.Weather_sta_cli.observed_count() > 0 else 'Simulated'
	info.watershedArea = connect.Rout_unit_con.select(fn.Sum(connect.Rout_unit_con.area)).scalar()

	if has_project_config:
		pc = base.Project_config.get_or_none()
		if pc is not None:
			info.swatVersion = pc.swat_version

	return info


def get_hyd(wb, aqu):
	hyd = check.CheckHydrology()
	if wb is not None:
		hyd.averageCn = wb.cn
		hyd.et = wb.et
		hyd.etPlant = wb.eplant
		hyd.etSoil = wb.esoil
		hyd.pet = wb.pet
		hyd.precipitation = wb.precip
		hyd.surfaceRunoff = wb.surq_gen
		hyd.lateralFlow = wb.latq_runon
		hyd.percolation = wb.perc
		hyd.irrigation = wb.irr
		hyd.tile = wb.qtile
	if aqu is not None:
		hyd.returnFlow = aqu.flo
		hyd.revap = aqu.revap

	deep_aqu = aquifer.Aquifer_aa.select(fn.SUM(aquifer.Aquifer_aa.rchrg).alias('rchrg_total')).where(aquifer.Aquifer_aa.name.contains('_deep')).get()
	if deep_aqu is not None and deep_aqu.rchrg_total is not None:
		hyd.recharge = deep_aqu.rchrg_total

	totalFlow = hyd.returnFlow + hyd.lateralFlow + hyd.surfaceRunoff
	if totalFlow > 0:
		hyd.baseflowTotalFlow = (hyd.returnFlow + hyd.lateralFlow) / totalFlow
		hyd.surfaceRunoffTotalFlow = hyd.surfaceRunoff / totalFlow

	if hyd.precipitation > 0:
		hyd.streamflowPrecipitation = totalFlow / hyd.precipitation
		hyd.percolationPrecipitation = hyd.percolation / hyd.precipitation
		hyd.etPrecipitation = hyd.et / hyd.precipitation
		hyd.deepRechargePrecipitation = hyd.recharge / hyd.precipitation

	hyd.warnings = []
	if hyd.precipitation < 65:
		hyd.warnings.append('Precipitation too small. (< 65mm)')
	elif hyd.precipitation > 3400:
		hyd.warnings.append('Precipitation may be too high. (> 3400 mm)')

	if hyd.surfaceRunoffTotalFlow > 0.78:
		hyd.warnings.append('Surface runoff ratio may be high (> 0.8)')
	elif hyd.surfaceRunoffTotalFlow < 0.31:
		hyd.warnings.append('Surface runoff ratio may be low (< 0.2)')

	if totalFlow > 0:
		gwqRatio = hyd.returnFlow / totalFlow
		if gwqRatio > 0.69:
			hyd.warnings.append('Groundwater ratio may be high')
		elif gwqRatio < 0.22:
			hyd.warnings.append('Groundwater ratio may be low')

	if hyd.lateralFlow > hyd.returnFlow:
		hyd.warnings.append('Lateral flow is greater than groundwater flow; may indicate a problem')

	if hyd.et > hyd.precipitation:
		hyd.warnings.append('ET Greater than precipitation; may indicate a problem unless irrigated')

	#Check hydro using Jimmy Williams equations
	eWaterYield = 0.26 * hyd.precipitation
	eET = 0.74 * hyd.precipitation
	ratio = 0.0129 * hyd.averageCn - 0.2857
	eSurq = ratio * eWaterYield

	if eWaterYield != 0:
		ratio = totalFlow / eWaterYield
		if ratio > 1.5:
			hyd.warnings.append('Water yield may be excessive')
		elif ratio < 0.5:
			hyd.warnings.append('Water yield may be too low')

	if eSurq != 0:
		ratio = hyd.surfaceRunoff / eSurq
		if ratio > 1.5:
			hyd.warnings.append('Surface runoff may be excessive')
		elif ratio < 0.5:
			hyd.warnings.append('Surface runoff may be too low')

	return hyd
	

def get_ncycle(nb, pw, ls):
	ncycle = check.CheckNitrogenCycle()
	ncycle.initialNO3 = 'NA'
	ncycle.finalNO3 = 'NA'
	ncycle.initialOrgN = 'NA'
	ncycle.finalOrgN = 'NA'
	ncycle.volatilization = 'NA'
	ncycle.nitrification = 'NA'
	ncycle.mineralization = 'NA'

	if nb is not None:
		ncycle.denitrification = nb.denit
		ncycle.nH4InOrgNFertilizer = nb.nh4atmo
		ncycle.nO3InOrgNFertilizer = nb.no3atmo
		ncycle.totalFertilizerN = nb.fertn
		ncycle.activeToStableOrgN = nb.act_sta_n
		ncycle.residueMineralization = nb.rsd_nitorg_n
		ncycle.nFixation = nb.fixn

	if pw is not None:
		ncycle.plantUptake = pw.nplt

	if ls is not None:
		ncycle.orgNFertilizer = ls.sedorgn

	if ncycle.denitrification == 0:
		ncycle.warnings.append('Denitrification is zero, consider decreasing SDNCO: (Denitrification threshold water content)')
	elif ncycle.totalFertilizerN != 0:
		calc = ncycle.denitrification / ncycle.totalFertilizerN

		if calc < 0.01:
			ncycle.warnings.append('Denitrification is less than 2% of the applied fertilizer amount')
		elif calc > 0.4:
			ncycle.warnings.append('Denitrification is greater than 25% of the applied fertilizer amount')

	"""if ncycle.totalFertilizerN != 0:
		calc = ncycle.volatilization / ncycle.totalFertilizerN

		if calc < 0.001:
			ncycle.warnings.append('Ammonia volatilization is less than 0.1% of the applied fertilizer amount')
		elif calc > 0.38:
			ncycle.warnings.append('Ammonia volatilization is greater than 38% of the applied fertilizer amount')

	if ncycle.initialNO3 != 0:
		calc = (ncycle.finalNO3 - ncycle.initialNO3) / ncycle.initialNO3

		if calc > 0.5:
			ncycle.warnings.append('Nitrate is building up in the soil, the simulation ends with {:.1f}% more'.format(calc * 100))
		elif calc < -0.5:
			ncycle.warnings.append('Nitrate is being removed from the soil profile, the simulation ends with {:.1f}% less'.format(calc * -100))

	if ncycle.initialOrgN != 0:
		calc = (ncycle.finalOrgN - ncycle.initialOrgN) / ncycle.initialOrgN

		if calc > 0.5:
			ncycle.warnings.append('Organic nitrogen is building up in the soil, the simulation ends with {:.1f}% more'.format(calc * 100))
		elif calc < -0.5:
			ncycle.warnings.append('Organic nitrogen is being removed from the soil profile, the simulation ends with {:.1f}% less'.format(calc * -100))"""

	if ncycle.totalFertilizerN != 0:
		calc = ncycle.plantUptake / ncycle.totalFertilizerN

		if calc < 0.5:
			ncycle.warnings.append('Crop is consuming less than half the amount of applied nitrogen')

	return ncycle


def get_pcycle(nb, pw, ls):
	pcycle = check.CheckPhosphorusCycle()
	pcycle.initialMinP = 'NA'
	pcycle.finalMinP = 'NA'
	pcycle.initialOrgP = 'NA'
	pcycle.finalOrgP = 'NA'
	pcycle.activeSolution = 'NA'
	pcycle.mineralization = 'NA'
	pcycle.orgPFertilizer = 'NA'

	if nb is not None:
		pcycle.totalFertilizerP = nb.fertp
		pcycle.inOrgPFertilizer = nb.lab_min_p
		pcycle.stableActive = nb.act_sta_p
		pcycle.residueMineralization = nb.rsd_laborg_p

	if pw is not None:
		pcycle.plantUptake = pw.pplnt

	if ls is not None:
		pcycle.orgPFertilizer = ls.sedorgp

	"""if pcycle.initialMinP != 0:
		calc = (pcycle.finalMinP - pcycle.initialMinP) / pcycle.initialMinP

		if calc > 0.5:
			pcycle.warnings.append('Mineral phosphorus is building up in the soil, the simulation ends with {:.1f}% more'.format(calc * 100))
		elif calc < -0.5:
			pcycle.warnings.append('Mineral phosphorus is being removed from the soil profile, the simulation ends with {:.1f}% less'.format(calc * -100))

	if pcycle.initialOrgP != 0:
		calc = (pcycle.finalOrgP - pcycle.initialOrgP) / pcycle.initialOrgP

		if calc > 0.5:
			pcycle.warnings.append('Organic phosphorus is building up in the soil, the simulation ends with {:.1f}% more'.format(calc * 100))
		elif calc < -0.5:
			pcycle.warnings.append('Organic phosphorus is being removed from the soil profile, the simulation ends with {:.1f}% less'.format(calc * -100))"""

	if pcycle.totalFertilizerP != 0:
		calc = pcycle.plantUptake / pcycle.totalFertilizerP

		if calc < 0.5:
			pcycle.warnings.append('Crop is consuming less than half the amount of applied phosphorus')
	
	return pcycle


def get_pg(nb, pw):
	pg = check.CheckPlantGrowth()
	pg.nRemoved = 'NA'
	pg.pRemoved = 'NA'

	if nb is not None:
		pg.totalFertilizerN = nb.fertn
		pg.totalFertilizerP = nb.fertp

	if pw is not None:
		pg.tempStressDays = pw.strstmp
		pg.waterStressDays = pw.strsw
		pg.nStressDays = pw.strsn
		pg.pStressDays = pw.strsp
		pg.avgBiomass = pw.bioms
		pg.avgYield = pw.yld
		pg.plantUptakeN = pw.nplt
		pg.plantUptakeP = pw.pplnt
		pg.soilAirStressDays = pw.strsa

	if pg.pStressDays > 60:
		pg.warnings.append('More than 100 days of phosphorus stress')
	if pg.nStressDays > 60:
		pg.warnings.append('More than 100 days of nitrogen stress')
	if pg.waterStressDays > 80:
		pg.warnings.append('More than 100 days of water stress')

	if pg.pStressDays < 1:
		pg.warnings.append('Unusually low phosphorus stress')
	if pg.nStressDays < 1:
		pg.warnings.append('Unusually low nitrogen stress')

	if pg.avgYield < 0.5:
		pg.warnings.append('Yield may be low if there is harvested crop')
	if pg.avgBiomass < 1:
		pg.warnings.append('Biomass averages less than 1 metric ton per hectare')

	return pg


def get_landscape(ls, ncycle, aqu):
	landscape = check.CheckLandscapeLosses()
	landscape.nLosses = check.CheckNitrogenLosses()
	landscape.pLosses = check.CheckPhosphorusLosses()

	if aqu is not None:
		landscape.nLosses.leached = aqu.seepno3
		landscape.nLosses.groundwaterYield = aqu.no3gw

	if ls is not None:
		landscape.nLosses.totalLoss = ls.sedorgn + ls.surqno3 + ls.lat3no3
		landscape.nLosses.orgN = ls.sedorgn
		landscape.nLosses.surfaceRunoff = ls.surqno3
		landscape.nLosses.lateralFlow = ls.lat3no3
		totalN = landscape.nLosses.orgN + landscape.nLosses.surfaceRunoff
		if totalN != 0:
			landscape.nLosses.solubilityRatio = landscape.nLosses.surfaceRunoff / totalN

		landscape.pLosses.totalLoss = ls.sedorgp + ls.surqsolp
		landscape.pLosses.orgP = ls.sedorgp
		landscape.pLosses.surfaceRunoff = ls.surqsolp
		if landscape.pLosses.totalLoss != 0:
			landscape.pLosses.solubilityRatio = landscape.pLosses.surfaceRunoff / landscape.pLosses.totalLoss

	if landscape.nLosses.totalLoss > 0.4 * ncycle.totalFertilizerN:
		landscape.warnings.append('Total nitrogen losses are greater than 40% of applied N')
	elif landscape.nLosses.totalLoss < 0.1 * ncycle.totalFertilizerN:
		landscape.warnings.append('Total nitrogen losses are less than 8% of applied N, may be incorrect in agricultural areas. Likely fine in unmanaged areas or forest dominated watersheds.')

	if landscape.nLosses.surfaceRunoff > 4.7:
		landscape.warnings.append('Nitrate losses in surface runoff may be high')
	elif landscape.nLosses.surfaceRunoff < 0.15:
		landscape.warnings.append('Nitrate losses in surface runoff may be low')

	if landscape.nLosses.orgN > 33:
		landscape.warnings.append('Organic/Particulate nitrogen losses in surface runoff may be high')
	elif landscape.nLosses.orgN < 0.3:
		landscape.warnings.append('Organic/Particulate nitrogen losses in surface runoff may be low')

	if landscape.pLosses.surfaceRunoff > 1.2:
		landscape.warnings.append('Soluble phosphorus losses in surface runoff may be high')
	elif landscape.pLosses.surfaceRunoff < 0.025:
		landscape.warnings.append('Soluble phosphorus losses in surface runoff may be low')

	if landscape.pLosses.orgP > 14:
		landscape.warnings.append('Organic/Particulate phosphorus losses in surface runoff may be high')
	elif landscape.pLosses.orgP < 0:
		landscape.warnings.append('Organic/Particulate phosphorus losses in surface runoff may be low')

	if landscape.nLosses.solubilityRatio > 0.85:
		landscape.warnings.append('Solubility ratio for nitrogen in runoff is high')
	elif landscape.nLosses.solubilityRatio < 0.1:
		landscape.warnings.append('Solubility ratio for nitrogen in runoff is low')

	if landscape.pLosses.solubilityRatio > 0.95:
		landscape.warnings.append('Solubility ratio for phosphorus in runoff is high, may be ok in uncultivated areas')
	elif landscape.pLosses.solubilityRatio < 0.13:
		landscape.warnings.append('Solubility ratio for phosphorus in runoff is low, may indicate a problem')

	"""if landscape.nLosses.leached > 50:
		landscape.warnings.append('Nitrate leaching is greater than 50 kg/ha, may indicate a problem.')

	if ncycle.totalFertilizerN != 0:
		ratio = landscape.nLosses.leached / ncycle.totalFertilizerN;

		if ratio < 0.21:
			landscape.warnings.append('Nitrate leaching is less than 21% of the applied fertilizer.')
		elif ratio > 0.38:
			landscape.warnings.append('Nitrate leaching is greater is more than 38% of the applied fertilizer, may indicate a problem.')"""

	return landscape


def get_landuse():
	#get plant name for each hru
	hru_to_crop = { c.unit: c.plantnm for c in misc.Crop_yld_aa.select() }
	hru_name_to_area = { h.name: h.area for h in connect.Hru_con.select() }
	hru_wb = waterbal.Hru_wb_aa.select().order_by(waterbal.Hru_wb_aa.unit)
	hru_ls = losses.Hru_ls_aa.select().order_by(losses.Hru_ls_aa.unit)
	hru_pw = plantwx.Hru_pw_aa.select().order_by(plantwx.Hru_pw_aa.unit)

	rows = {}
	warnings = []
	if len(hru_wb) == len(hru_ls) and len(hru_wb) == len(hru_pw):
		i = 0
		for wb in hru_wb:
			landuse = hru_to_crop.get(wb.unit, 'NA').strip()
			area = hru_name_to_area.get(wb.name, 0)
			match = rows.get(landuse, None)

			if match is None:
				rows[landuse] = {
					'landUse': landuse,
					'area': area,
					'cn': wb.cn * area,
					'awc': 'NA',
					'usle_ls': 'NA',
					'irr': wb.irr * area,
					'prec': wb.precip * area,
					'surq': wb.surq_cont * area,
					'gwq': 'NA',
					'et': wb.et * area,
					'sed': hru_ls[i].sedyld * area,
					'no3': hru_ls[i].surqno3 * area,
					'orgn': hru_ls[i].sedorgn * area,
					'biom': hru_pw[i].bioms * area,
					'yld': hru_pw[i].yld * area,
				}
			else:
				rows[landuse]['area'] += area
				rows[landuse]['cn'] += wb.cn * area
				rows[landuse]['irr'] += wb.irr * area
				rows[landuse]['prec'] += wb.precip * area
				rows[landuse]['surq'] += wb.surq_cont * area
				rows[landuse]['et'] += wb.et * area
				rows[landuse]['sed'] += hru_ls[i].sedyld * area
				rows[landuse]['no3'] += hru_ls[i].surqno3 * area
				rows[landuse]['orgn'] += hru_ls[i].sedorgn * area
				rows[landuse]['biom'] += hru_pw[i].bioms * area
				rows[landuse]['yld'] += hru_pw[i].yld * area

			i += 1

		lu_rows = []
		for k in rows:
			if rows[k]['area'] > 0:
				rows[k]['cn'] /= rows[k]['area']
				rows[k]['irr'] /= rows[k]['area']
				rows[k]['prec'] /= rows[k]['area']
				rows[k]['surq'] /= rows[k]['area']
				rows[k]['et'] /= rows[k]['area']
				rows[k]['sed'] /= rows[k]['area']
				rows[k]['no3'] /= rows[k]['area']
				rows[k]['orgn'] /= rows[k]['area']
				rows[k]['biom'] /= rows[k]['area']
				rows[k]['yld'] /= rows[k]['area']

				rows[k]['biom'] /= 1000
				rows[k]['yld'] /= 1000
			lu_rows.append(rows[k])

			if rows[k]['cn'] > 95:
				warnings.append('{} curve number may be too high'.format(k))
			elif rows[k]['cn'] < 35:
				warnings.append('{} curve number may be too low'.format(k))

			"""if rows[k]['awc'] > 606:
				warnings.append('{} available water may be too high'.format(k))
			elif rows[k]['awc'] < 41:
				warnings.append('{} available water may be too low'.format(k))

			if rows[k]['usle_ls'] > 16.4:
				warnings.append('{} USLE LS factor may be too high'.format(k))
			elif rows[k]['usle_ls'] < 0.02:
				warnings.append('{} USLE LS factor may be too low'.format(k))"""

			if rows[k]['prec'] != 0:
				if rows[k]['et'] / rows[k]['prec'] < 0.31:
					warnings.append('{} ET less than 31% of irrigation water + precipitation'.format(k))
				elif rows[k]['et'] / (rows[k]['prec'] + rows[k]['irr']) > 0.98:
					warnings.append('{} ET more than 98% of irrigation water + precipitation'.format(k))

				if rows[k]['surq'] / rows[k]['prec'] > 0.5:
					warnings.append('{} more than 1/2 precipitation is runoff'.format(k))
				elif rows[k]['surq'] / rows[k]['prec'] < 0.01:
					warnings.append('{} less than 1% of precipitation in runoff'.format(k))

			ratio = 0.0129 * rows[k]['cn'] - 0.2857
			eSurq = ratio * 0.26 * rows[k]['prec']

			if eSurq != 0:
				ratio = rows[k]['surq'] / eSurq
				if ratio > 1.5:
					warnings.append('{} surface runoff may be excessive'.format(k))
				elif ratio < 0.5:
					warnings.append('{} surface runoff may be too low'.format(k))

			if rows[k]['no3'] > 80:
				warnings.append('{} nitrate yield may be too high {:.2f} kg/ha'.format(k, rows[k]['no3']))

			if rows[k]['biom'] > 50:
				warnings.append('{} biomass may be too high {:.2f} t/ha'.format(k, rows[k]['biom']))
			elif rows[k]['biom'] < 1:
				warnings.append('{} biomass may be too low {:.2f} t/ha'.format(k, rows[k]['biom']))

			"""if rows[k]['surq'] != 0 or rows[k]['gwq'] != 0:
				if rows[k]['gwq'] / (rows[k]['surq'] + rows[k]['gwq']) > 0.69:
					warnings.append('{} more than 69% of water yield is baseflow'.format(k))
				elif rows[k]['gwq'] / (rows[k]['surq'] + rows[k]['gwq']) < 0.22:
					warnings.append('{} less than 22% of water yield is baseflow'.format(k))"""

			if rows[k]['area'] < 0.05:
				warnings.append('{} HRU area is less than 5 hectares, is this necessary?'.format(k))

			if rows[k]['prec'] > 3400:
				warnings.append('{} precipitation greater than 3400mm/yr'.format(k))
			elif rows[k]['prec'] < 65:
				warnings.append('{} precipitation less than 65mm/yr'.format(k))

	landuse = check.CheckLandUseSummary()
	landuse.landUseRows = lu_rows
	landuse.warnings = warnings

	too_high_cn = waterbal.Hru_wb_aa.select().where(waterbal.Hru_wb_aa.cn > 98)
	if too_high_cn.count() > 0:
		hrus = [h.name for h in too_high_cn]
		landuse.hruLevelWarnings.append('Curve number may be too high (>98) for the following HRUs: {}'.format(', '.join(hrus)))

	too_low_cn = waterbal.Hru_wb_aa.select().where(waterbal.Hru_wb_aa.cn < 35)
	if too_low_cn.count() > 0:
		hrus = [h.name for h in too_low_cn]
		landuse.hruLevelWarnings.append('Curve number may be too low (<35) for the following HRUs: {}'.format(', '.join(hrus)))

	return landuse


def get_psrc(ls, total_area):
	subLoad = check.CheckPointSourcesLoad()
	psLoad = check.CheckPointSourcesLoad()
	fromLoad = check.CheckPointSourcesLoad()

	if channel.Channel_sd_aa.select().count() > 0:
		cha = channel.Channel_sd_aa.select().order_by(channel.Channel_sd_aa.flo_out.desc())[0]
		subLoad.flow = cha.flo_out / 365
		subLoad.sediment = cha.sed_out
		subLoad.nitrogen = cha.orgn_out + cha.no3_out + cha.nh3_out + cha.no2_out
		subLoad.phosphorus = cha.sedp_out + cha.solp_out

	ptable = hyd.Recall_aa
	if ptable.select().count() > 0:
		pts = ptable.select(fn.SUM(ptable.flo).alias('flow_total'), fn.SUM(ptable.sed).alias('sed_total'), fn.SUM(ptable.orgn).alias('orgn_total'), fn.SUM(ptable.sedp).alias('sedp_total'), fn.SUM(ptable.no3).alias('no3_total'), fn.SUM(ptable.nh3).alias('nh3_total'), fn.SUM(ptable.no2).alias('no2_total'), fn.SUM(ptable.solp).alias('solp_total')).get()
		psLoad.flow = pts.flow_total / 365
		psLoad.sediment = pts.sed_total
		psLoad.nitrogen = pts.orgn_total + pts.no3_total + pts.nh3_total + pts.no2_total
		psLoad.phosphorus = pts.sedp_total + pts.solp_total

	fromLoad.flow = 0 if subLoad.flow == 0 else psLoad.flow / (psLoad.flow + subLoad.flow) * 100
	fromLoad.sediment = 0 if subLoad.sediment == 0 else psLoad.sediment / (psLoad.sediment + subLoad.sediment) * 100
	fromLoad.nitrogen = 0 if subLoad.nitrogen == 0 else psLoad.nitrogen / (psLoad.nitrogen + subLoad.nitrogen) * 100
	fromLoad.phosphorus = 0 if subLoad.phosphorus == 0 else psLoad.phosphorus / (psLoad.phosphorus + subLoad.phosphorus) * 100

	warnings = []
	if fromLoad.flow > 30:
		warnings.append('Inlets/point sources contribute more than 30% of the total streamflow')
	if fromLoad.phosphorus > 55:
		warnings.append('Inlets/point sources contribute more than 55% of the total phosphorus')
	if fromLoad.nitrogen > 20:
		warnings.append('Inlets/point sources contribute more than 20% of the total nitrogen')
	if fromLoad.sediment > 30:
		warnings.append('Inlets/point sources contribute more than 30% of the total sediment')

	if psLoad.flow == 0 and psLoad.sediment > 0:
		warnings.append('Inlets/point sources contribute sediment but not flow, error likely')
	if psLoad.flow == 0 and psLoad.phosphorus > 0:
		warnings.append('Inlets/point sources contribute phosphorus but not flow, error likely')
	if psLoad.flow == 0 and psLoad.nitrogen > 0:
		warnings.append('Inlets/point sources contribute nitrogen but not flow, error likely')

	if psLoad.flow > 0 and psLoad.sediment == 0:
		warnings.append('Inlets/point sources contribute flow, but not sediment')
	if psLoad.flow > 0 and psLoad.phosphorus == 0:
		warnings.append('Inlets/point sources contribute flow, but not phosphorus')
	if psLoad.flow > 0 and psLoad.nitrogen == 0:
		warnings.append('Inlets/point sources contribute flow, but not nitrogen')

	if psLoad.flow == 0 and psLoad.nitrogen == 0 and psLoad.phosphorus == 0 and psLoad.sediment == 0:
		warnings.append('Inlets/point source not present')

	if psLoad.phosphorus > 0:
		if psLoad.nitrogen / psLoad.phosphorus > 8.8:
			warnings.append('Inlets/point sources N:P ratio greater than 8.8')
		elif psLoad.nitrogen / psLoad.phosphorus < 2.8:
			warnings.append('Inlets/point sources N:P ratio less than 2.8')

	psrc = check.CheckPointSources()
	psrc.subbasinLoad = subLoad
	psrc.pointSourceInletLoad = psLoad
	psrc.fromInletAndPointSource = fromLoad

	return psrc


def get_res(has_res, has_yr_res):
	res = check.CheckReservoirs()
	res.avgTrappingEfficiencies = check.CheckAvgTrappingEfficiency()
	res.avgWaterLosses = check.CheckAvgWaterLoss()
	res.avgReservoirTrends = check.CheckAvgReservoirTrend()
	res.avgReservoirTrends.fractionEmpty = 'NA'
	res.avgReservoirTrends.maxVolume = 'NA'
	res.avgReservoirTrends.minVolume = 'NA'

	if not has_res:
		res.warnings.append('No reservoir data available.')
	else:
		basin_res = reservoir.Basin_res_aa.get_or_none()
		if basin_res is None:
			res.warnings.append('No reservoir data available.')
		else:
			basin_n_in = basin_res.orgn_in + basin_res.no3_in + basin_res.no2_in + basin_res.nh3_in
			basin_n_out = basin_res.orgn_out + basin_res.no3_out + basin_res.no2_out + basin_res.nh3_out
			basin_p_in = basin_res.sedp_in + basin_res.solp_in
			basin_p_out = basin_res.sedp_out + basin_res.solp_out

			res.avgTrappingEfficiencies.sediment = get_in_out_percent(basin_res.sed_in, basin_res.sed_out)
			res.avgTrappingEfficiencies.nitrogen = get_in_out_percent(basin_n_in, basin_n_out)
			res.avgTrappingEfficiencies.phosphorus = get_in_out_percent(basin_p_in, basin_p_out)

			res.avgWaterLosses.totalRemoved = get_in_out_percent(basin_res.flo_in, basin_res.flo_out)
			res.avgWaterLosses.seepage = 0 if basin_res.flo_stor == 0 else basin_res.seep / basin_res.flo_stor * 100
			res.avgWaterLosses.evaporation = 0 if basin_res.flo_stor == 0 else basin_res.evap / basin_res.flo_stor * 100

			num_yrs = 0
			init_yr = 0
			final_yr = 0
			if has_yr_res:
				res_yrs = reservoir.Reservoir_yr.select().where(reservoir.Reservoir_yr.unit == 1).order_by(reservoir.Reservoir_yr.yr)
				num_yrs = res_yrs.count()
				if (num_yrs > 0):
					init_yr = res_yrs[0].yr
					final_yr = res_yrs[num_yrs - 1].yr


			res_list = reservoir.Reservoir_aa.select()
			res.avgReservoirTrends.numberReservoirs = res_list.count()

			per_res_warns = [None] * 9
			ratios = []
			empty_vols = []
			for r in res_list:
				n_in = r.orgn_in + r.no3_in + r.no2_in + r.nh3_in
				n_out = r.orgn_out + r.no3_out + r.no2_out + r.nh3_out
				p_in = r.sedp_in + r.solp_in
				p_out = r.sedp_out + r.solp_out

				row = check.CheckReservoirRow()
				row.id = r.name
				row.sediment = get_in_out_percent(r.sed_in, r.sed_out)
				row.phosphorus = get_in_out_percent(p_in, p_out)
				row.nitrogen = get_in_out_percent(n_in, n_out)
				row.seepage = 0 if r.flo_stor == 0 else r.seep / r.flo_stor * 100
				row.evapLoss = 0 if r.flo_stor == 0 else r.evap / r.flo_stor * 100

				row.volumeRatio = 'NA'
				row.fractionEmpty = 'NA'
				if has_yr_res:
					init_vol = reservoir.Reservoir_yr.select().where((reservoir.Reservoir_yr.unit == r.unit) & (reservoir.Reservoir_yr.yr == init_yr)).get().flo_stor
					final_vol = reservoir.Reservoir_yr.select().where((reservoir.Reservoir_yr.unit == r.unit) & (reservoir.Reservoir_yr.yr == final_yr)).get().flo_stor
					empty_vol_count = reservoir.Reservoir_yr.select().where((reservoir.Reservoir_yr.unit == r.unit) & (reservoir.Reservoir_yr.flo_stor < 1)).count()

					ratio = 0 if init_vol == 0 else final_vol / init_vol
					empty_frac = 0 if num_yrs == 0 else empty_vol_count / num_yrs

					row.volumeRatio = ratio
					row.fractionEmpty = empty_frac
					ratios.append(ratio)
					empty_vols.append(empty_frac)

				res.reservoirRows.append(row)

				if row.sediment < 40:
					per_res_warns[0] = 'Sediment trapping efficiency less than 40% at one or more reservoirs'
				if row.sediment > 98:
					per_res_warns[1] = 'Sediment trapping efficiency greater than 98% at one or more reservoirs'

				if row.nitrogen< 7:
					per_res_warns[2] = 'Nitrogen trapping efficiency less than 7% at one or more reservoirs'
				if row.nitrogen > 72:
					per_res_warns[3] = 'Nitrogen trapping efficiency greater than 72% at one or more reservoirs'

				if row.phosphorus < 18:
					per_res_warns[4] = 'Phosphorus trapping efficiency less than 18% at one or more reservoirs'
				if row.phosphorus > 82:
					per_res_warns[5] = 'Phosphorus trapping efficiency greater than 82% at one or more reservoirs'

				if row.evapLoss < 5:
					per_res_warns[6] = 'Evaporation losses are less than 2% at one or more reservoirs'
				if row.evapLoss > 50:
					per_res_warns[7] = 'Evaporation losses are more than 30% at one or more reservoirs'

				if row.seepage > 25:
					per_res_warns[8] = 'Seepage losses are more than 10% at one or more reservoirs'

			for w in per_res_warns:
				if w is not None:
					res.warnings.append(w)
			
			if has_yr_res:
				res.avgReservoirTrends.fractionEmpty = max(empty_vols)
				res.avgReservoirTrends.maxVolume = max(ratios)
				res.avgReservoirTrends.minVolume = min(ratios)

				if res.avgReservoirTrends.fractionEmpty > 0:
					res.warnings.append('At least one of your reservoirs has become complexly dry during the simulation')
				if res.avgReservoirTrends.maxVolume > 5:
					res.warnings.append('At least one of your reservoirs ends the simulation with at least 500% more volume that it begins with. Check your release parameters.')
				if res.avgReservoirTrends.minVolume > 0.2:
					res.warnings.append('At least one of your reservoirs ends the simulation with less than 20% volume that it begins with. Check your release parameters.')

	return res


def get_instream(basin_cha, cha, wb, ls, total_area, psrc):
	instream = check.CheckInstreamProcesses()

	if basin_cha is None or wb is None or ls is None:
		instream.warnings.append('Water balance, losses, and channel outputs used in this section are not available in your printed output files.')
	else:
		sed_chg = basin_cha.sed_out - basin_cha.sed_in
		upland_sed = ls.sedyld * total_area

		cha_erosion = 0
		cha_deposition = 0
		if upland_sed > 0:
			if sed_chg > 0:
				cha_erosion = sed_chg / (upland_sed + sed_chg) * 100
				if cha_erosion > 50:
					instream.warnings.append('More than 50% of sediment is from instream processes')
			else:
				cha_deposition = sed_chg * -1 / upland_sed * 100
				if cha_deposition > 95:
					instream.warnings.append('More than 95% of sediment is deposited instream')

		if cha_erosion == 0 and cha_deposition == 0:
			instream.warnings.append('No in-stream sediment modification; this is unusual')
		elif (cha_erosion > -2 and cha_erosion < 2) or (cha_deposition > -2 and cha_deposition < 2):
			instream.warnings.append('Very little in-stream sediment modification (< +-2%); this is unusual')

		min_n_in = basin_cha.no3_in + basin_cha.nh3_in + basin_cha.no2_in
		min_n_out = basin_cha.no3_out + basin_cha.nh3_out + basin_cha.no2_out
		min_n = min_n_out - min_n_in
		org_n = basin_cha.orgn_out - basin_cha.orgn_in

		total_n_ratio = 0
		if psrc.subbasinLoad.nitrogen != 0 or psrc.pointSourceInletLoad.nitrogen != 0:
			total_n_ratio = (min_n + org_n) / (psrc.subbasinLoad.nitrogen + psrc.pointSourceInletLoad.nitrogen) * 100

			if total_n_ratio < -50:
				instream.warnings.append('Excessive in-stream nitrogen modification (loss)')
			elif total_n_ratio > 10:
				instream.warnings.append('Excessive in-stream nitrogen modification (gain)')

		min_p = basin_cha.solp_out - basin_cha.solp_in
		org_p = basin_cha.sedp_out - basin_cha.sedp_in

		total_p_ratio = 0
		if psrc.subbasinLoad.phosphorus != 0 or psrc.pointSourceInletLoad.phosphorus != 0:
			total_p_ratio = (min_p + org_p) / (psrc.subbasinLoad.phosphorus + psrc.pointSourceInletLoad.phosphorus) * 100

			if total_p_ratio < -50:
				instream.warnings.append('Excessive in-stream phosphorus modification (loss)')
			elif total_p_ratio > 10:
				instream.warnings.append('Excessive in-stream phosphorus modification (gain)')

		total_streamflow_loss = 0
		evap = 0
		seep = 0
		water_yld = wb.wateryld
		if water_yld != 0:
			tloss = wb.tloss #already in mm?
			tevap = basin_cha.evap / (total_area / 100 * 1000000) #ha-m to mm? 

			total_streamflow_loss = (tloss + tevap) / water_yld * 100
			evap = tevap / water_yld * 100
			seep = tloss / water_yld * 100

		rch = []
		for c in cha:
			c_n_in = c.no3_in + c.nh3_in + c.no2_in + c.orgn_in
			c_n_out = c.no3_out + c.nh3_out + c.no2_out + c.orgn_out
			c_p_in = c.solp_in + c.sedp_in
			c_p_out = c.solp_out + c.sedp_out

			r = check.CheckReach()
			r.id = c.name
			r.sediment = 0 if c.sed_in == 0 else c.sed_out / c.sed_in * 100
			r.nitrogen = 0 if c_n_in == 0 else c_n_out / c_n_in * 100
			r.phosphorus = 0 if c_p_in == 0 else c_p_out / c_p_in * 100
			rch.append(r)

		instream.uplandSedimentYield = ls.sedyld
		instream.channelErosion = cha_erosion
		instream.channelDeposition = cha_deposition
		instream.totalN = total_n_ratio
		instream.totalP = total_p_ratio
		instream.instreamSedimentChange = 0 if total_area == 0 else sed_chg / total_area
		instream.totalStreamflowLosses = total_streamflow_loss
		instream.evaporationLoss = evap
		instream.seepageLoss = seep
		instream.reaches = rch

	return instream


def get_sed(instream, psrc, ls, wb):
	sed = check.CheckSediment()
	sed.inStreamSedimentChange = instream.instreamSedimentChange
	sed.inletSediment = psrc.pointSourceInletLoad.sediment
	if wb is not None:
		sed.surfaceRunoff = wb.surq_gen
	if ls is not None:
		sed.avgUplandSedimentYield = ls.sedyld

	if losses.Hru_ls_aa.select().count() > 0:
		sed.maxUplandSedimentYield = losses.Hru_ls_aa.select(fn.Max(losses.Hru_ls_aa.sedyld)).scalar()

	return sed


class SwatCheckApi(BaseRestModel):
	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument('project_db', type=str, required=True, location='json')
		parser.add_argument('output_db', type=str, required=True, location='json')
		args = parser.parse_args(strict=False)

		SetupOutputDatabase.init(args.output_db)
		SetupProjectDatabase.init(args.project_db)

		required_tables = [
			'basin_wb_aa', 'basin_nb_aa', 'basin_pw_aa', 'basin_ls_aa', 'basin_psc_aa',
			'basin_aqu_aa', 'aquifer_aa', 'recall_aa',
			'basin_sd_cha_aa', 'channel_sd_aa', 'channel_sdmorph_aa', 
			'hru_ls_aa', 'hru_wb_aa', 'hru_pw_aa', 'crop_yld_aa'
		]

		conn = lib.open_db(args.output_db)
		for table in required_tables:
			if not lib.exists_table(conn, table):
				abort(500, message='Could not load SWAT+ Check because the table "{}" does not exist in your output database. Re-run your model and check all yearly and average annual files under the print options, and keep the analyze output box checked.'.format(table))

		try:
			has_res = lib.exists_table(conn, 'basin_res_aa')
			has_yr_res = lib.exists_table(conn, 'reservoir_yr')
			has_project_config = lib.exists_table(conn, 'project_config')

			total_area = connect.Rout_unit_con.select(fn.Sum(connect.Rout_unit_con.area)).scalar()

			wb = waterbal.Basin_wb_aa.get_or_none()
			aqu = aquifer.Basin_aqu_aa.get_or_none()
			nb = nutbal.Basin_nb_aa.get_or_none()
			pw = plantwx.Basin_pw_aa.get_or_none()
			ls = losses.Basin_ls_aa.get_or_none()
			basin_cha = channel.Basin_sd_cha_aa.get_or_none()
			cha = channel.Channel_sd_aa.select()

			info = get_info(has_project_config)
			hydrology = get_hyd(wb, aqu)
			ncycle = get_ncycle(nb, pw, ls)
			pcycle = get_pcycle(nb, pw, ls)
			pg = get_pg(nb, pw)
			landscape = get_landscape(ls, ncycle, aqu)
			landuse = get_landuse()
			psrc = get_psrc(ls, total_area)
			res = get_res(has_res, has_yr_res)
			instream = get_instream(basin_cha, cha, wb, ls, total_area, psrc)
			sed = get_sed(instream, psrc, ls, wb)

			return {
				'setup': info.toJson(),
				'hydrology': hydrology.toJson(),
				'nitrogenCycle': ncycle.toJson(),
				'phosphorusCycle': pcycle.toJson(),
				'plantGrowth': pg.toJson(),
				'landscapeNutrientLosses': landscape.toJson(),
				'landUseSummary': landuse.toJson(),
				'pointSources': psrc.toJson(),
				'reservoirs': res.toJson(),
				'instreamProcesses': instream.toJson(),
				'sediment': sed.toJson()
			}
		except Exception as ex:
			abort(500, message='Error loading SWAT+ Check. Exception: {ex} {tb}'.format(ex=str(ex), tb=traceback.format_exc()))
