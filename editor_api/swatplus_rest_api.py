from flask import Flask, request
from flask_restful import Resource, Api
from flask_cors import CORS

from rest import setup, simulation, auto_complete, climate, routing_unit, hru_parm_db, channel, definitions, aquifer, reservoir, hydrology, hru, exco, dr, lum, init, ops, basin, soils, regions, change, recall, decision_table, structural

from helpers.executable_api import Unbuffered
import sys
import argparse

from werkzeug.routing import PathConverter

class EverythingConverter(PathConverter):
    regex = '.*?'


app = Flask(__name__)
api = Api(app)
CORS(app)

app.url_map.converters['everything'] = EverythingConverter

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


class SwatPlusApi(Resource):
	def get(self):
		return {'SWATPlusEditor': 'API call working'}


class SwatPlusShutdownApi(Resource):
	def get(self):
		shutdown_server()
		return {'SWATPlusEditor': 'Server shutting down...'}


list_params = 'list/<sort>/<reverse>/<page>/<items_per_page>/<everything:project_db>'
post_params = 'post/<everything:project_db>'
get_params = '<id>/<everything:project_db>'
many_params = 'many/<everything:project_db>'
datasets_get_name_params = 'datasets/<name>/<everything:datasets_db>'

api.add_resource(SwatPlusApi, '/')
api.add_resource(SwatPlusShutdownApi, '/shutdown')

api.add_resource(setup.SetupApi, '/setup')
api.add_resource(setup.ConfigApi, '/setup/config/<everything:project_db>')
api.add_resource(setup.CheckImportConfigApi, '/setup/check-config/<everything:project_db>')
api.add_resource(setup.InputFilesSettingsApi, '/setup/inputfiles/<everything:project_db>')
api.add_resource(setup.SwatRunSettingsApi, '/setup/swatrun/<everything:project_db>')
api.add_resource(setup.SaveOutputReadSettingsApi, '/setup/outputread/<everything:project_db>')
api.add_resource(setup.InfoApi, '/setup/info/<everything:project_db>')

api.add_resource(auto_complete.AutoCompleteApi, '/autocomplete/<type>/<partial_name>/<everything:project_db>')
api.add_resource(auto_complete.AutoCompleteNoParmApi, '/autocomplete-np/<type>/<everything:project_db>')
api.add_resource(auto_complete.AutoCompleteIdApi, '/autocomplete/id/<type>/<name>/<everything:project_db>')
api.add_resource(auto_complete.SelectListApi, '/selectlist/<type>/<everything:project_db>')
api.add_resource(definitions.VarRangeApi, '/vars/<table>/<everything:db>')
api.add_resource(definitions.VarCodeApi, '/codes/<table>/<variable>/<everything:db>')

api.add_resource(simulation.TimeSimApi, '/sim/time/<everything:project_db>')
api.add_resource(simulation.PrintPrtApi, '/sim/print/<everything:project_db>')
api.add_resource(simulation.PrintPrtObjectApi, '/sim/print/objects/' + get_params)

api.add_resource(basin.ParametersBsnApi, '/basin/parameters/<everything:project_db>')
api.add_resource(basin.CodesBsnApi, '/basin/codes/<everything:project_db>')

api.add_resource(climate.WeatherStationListApi, '/climate/stations/' + post_params)
api.add_resource(climate.WeatherStationApi, '/climate/stations/' + get_params)
api.add_resource(climate.WeatherStationPageApi, '/climate/stations/' + list_params)
api.add_resource(climate.WeatherStationSaveDirApi, '/climate/stations/directory/<everything:project_db>')
api.add_resource(climate.WeatherFileAutoCompleteApi, '/climate/stations/files/<type>/<partial_name>/<everything:project_db>')

api.add_resource(climate.WgnListApi, '/climate/wgn/' + post_params)
api.add_resource(climate.WgnApi, '/climate/wgn/' + get_params)
api.add_resource(climate.WgnPageApi, '/climate/wgn/' + list_params)
api.add_resource(climate.WgnSaveImportDbApi, '/climate/wgn/db/<everything:project_db>')
api.add_resource(climate.WgnTablesAutoCompleteApi, '/climate/wgn/db/tables/autocomplete/<partial_name>/<everything:wgn_db>')
api.add_resource(climate.WgnAutoCompleteApi, '/climate/wgn/autocomplete/<partial_name>/<everything:project_db>')

api.add_resource(climate.WgnMonthListApi, '/climate/wgn/months/<wgn_id>/<everything:project_db>')
api.add_resource(climate.WgnMonthApi, '/climate/wgn/month/' + get_params)

api.add_resource(routing_unit.RoutUnitBoundariesApi, '/routing_unit/boundaries/<everything:project_db>')

""" Channels Modules   """
api.add_resource(channel.ChannelTypeApi, '/channels/get_type/<everything:project_db>')

api.add_resource(channel.ChannelConListApi, '/channels/' + list_params)
api.add_resource(channel.ChannelConPostApi, '/channels/' + post_params)
api.add_resource(channel.ChannelConApi, '/channels/' + get_params)
api.add_resource(channel.ChannelConMapApi, '/channels/map/<everything:project_db>')
api.add_resource(channel.ChannelConOutPostApi, '/channels/out/' + post_params)
api.add_resource(channel.ChannelConOutApi, '/channels/out/' + get_params)

api.add_resource(channel.ChandegConListApi, '/channels-lte/' + list_params)
api.add_resource(channel.ChandegConPostApi, '/channels-lte/' + post_params)
api.add_resource(channel.ChandegConApi, '/channels-lte/' + get_params)
api.add_resource(channel.ChandegConMapApi, '/channels-lte/map/<everything:project_db>')
api.add_resource(channel.ChandegConOutPostApi, '/channels-lte/out/' + post_params)
api.add_resource(channel.ChandegConOutApi, '/channels-lte/out/' + get_params)

api.add_resource(channel.ChannelChaListApi, '/channels/properties/' + list_params)
api.add_resource(channel.ChannelChaPostApi, '/channels/properties/' + post_params)
api.add_resource(channel.ChannelChaUpdateManyApi, '/channels/properties/' + many_params)
api.add_resource(channel.ChannelChaApi, '/channels/properties/' + get_params)

api.add_resource(channel.InitialChaListApi, '/channels/initial/' + list_params)
api.add_resource(channel.InitialChaPostApi, '/channels/initial/' + post_params)
api.add_resource(channel.InitialChaUpdateManyApi, '/channels/initial/' + many_params)
api.add_resource(channel.InitialChaApi, '/channels/initial/' + get_params)

api.add_resource(channel.HydrologyChaListApi, '/channels/hydrology/' + list_params)
api.add_resource(channel.HydrologyChaPostApi, '/channels/hydrology/' + post_params)
api.add_resource(channel.HydrologyChaUpdateManyApi, '/channels/hydrology/' + many_params)
api.add_resource(channel.HydrologyChaApi, '/channels/hydrology/' + get_params)

api.add_resource(channel.SedimentChaListApi, '/channels/sediment/' + list_params)
api.add_resource(channel.SedimentChaPostApi, '/channels/sediment/' + post_params)
api.add_resource(channel.SedimentChaUpdateManyApi, '/channels/sediment/' + many_params)
api.add_resource(channel.SedimentChaApi, '/channels/sediment/' + get_params)

api.add_resource(channel.NutrientsChaListApi, '/channels/nutrients/' + list_params)
api.add_resource(channel.NutrientsChaPostApi, '/channels/nutrients/' + post_params)
api.add_resource(channel.NutrientsChaUpdateManyApi, '/channels/nutrients/' + many_params)
api.add_resource(channel.NutrientsChaApi, '/channels/nutrients/' + get_params)

api.add_resource(channel.ChannelLteChaListApi, '/channels-lte/properties/' + list_params)
api.add_resource(channel.ChannelLteChaPostApi, '/channels-lte/properties/' + post_params)
api.add_resource(channel.ChannelLteChaUpdateManyApi, '/channels-lte/properties/' + many_params)
api.add_resource(channel.ChannelLteChaApi, '/channels-lte/properties/' + get_params)

api.add_resource(channel.HydSedLteChaListApi, '/channels-lte/hydsed/' + list_params)
api.add_resource(channel.HydSedLteChaPostApi, '/channels-lte/hydsed/' + post_params)
api.add_resource(channel.HydSedLteChaUpdateManyApi, '/channels-lte/hydsed/' + many_params)
api.add_resource(channel.HydSedLteChaApi, '/channels-lte/hydsed/' + get_params)
""" Channels Modules   """

""" HRUs Modules   """
api.add_resource(hru.HruConListApi, '/hrus/' + list_params)
api.add_resource(hru.HruConPostApi, '/hrus/' + post_params)
api.add_resource(hru.HruConApi, '/hrus/' + get_params)
api.add_resource(hru.HruConMapApi, '/hrus/map/<everything:project_db>')
api.add_resource(hru.HruConOutPostApi, '/hrus/out/' + post_params)
api.add_resource(hru.HruConOutApi, '/hrus/out/' + get_params)

api.add_resource(hru.HruDataHruListApi, '/hrus/properties/' + list_params)
api.add_resource(hru.HruDataHruPostApi, '/hrus/properties/' + post_params)
api.add_resource(hru.HruDataHruUpdateManyApi, '/hrus/properties/' + many_params)
api.add_resource(hru.HruDataHruApi, '/hrus/properties/' + get_params)

api.add_resource(hru.HruLteConListApi, '/hrus-lte/' + list_params)
api.add_resource(hru.HruLteConPostApi, '/hrus-lte/' + post_params)
api.add_resource(hru.HruLteConApi, '/hrus-lte/' + get_params)
api.add_resource(hru.HruLteConMapApi, '/hrus-lte/map/<everything:project_db>')
api.add_resource(hru.HruLteConOutPostApi, '/hrus-lte/out/' + post_params)
api.add_resource(hru.HruLteConOutApi, '/hrus-lte/out/' + get_params)

api.add_resource(hru.HruLteListApi, '/hrus-lte/properties/' + list_params)
api.add_resource(hru.HruLtePostApi, '/hrus-lte/properties/' + post_params)
api.add_resource(hru.HruLteUpdateManyApi, '/hrus-lte/properties/' + many_params)
api.add_resource(hru.HruLteApi, '/hrus-lte/properties/' + get_params)
""" HRUs Modules   """

""" RoutingUnit Modules   """
api.add_resource(routing_unit.RoutingUnitConListApi, '/routing_unit/' + list_params)
api.add_resource(routing_unit.RoutingUnitConPostApi, '/routing_unit/' + post_params)
api.add_resource(routing_unit.RoutingUnitConApi, '/routing_unit/' + get_params)

api.add_resource(routing_unit.RoutingUnitConMapApi, '/routing_unit/map/<everything:project_db>')

api.add_resource(routing_unit.RoutingUnitConOutPostApi, '/routing_unit/out/' + post_params)
api.add_resource(routing_unit.RoutingUnitConOutApi, '/routing_unit/out/' + get_params)

api.add_resource(routing_unit.RoutingUnitRtuListApi, '/routing_unit/properties/' + list_params)
api.add_resource(routing_unit.RoutingUnitRtuPostApi, '/routing_unit/properties/' + post_params)
api.add_resource(routing_unit.RoutingUnitRtuUpdateManyApi, '/routing_unit/properties/' + many_params)
api.add_resource(routing_unit.RoutingUnitRtuApi, '/routing_unit/properties/' + get_params)

api.add_resource(routing_unit.RoutingUnitEleListApi, '/routing_unit/elements/' + list_params)
api.add_resource(routing_unit.RoutingUnitElePostApi, '/routing_unit/elements/' + post_params)
api.add_resource(routing_unit.RoutingUnitEleApi, '/routing_unit/elements/' + get_params)
""" RoutingUnit Modules   """

""" Aquifers Modules   """
api.add_resource(aquifer.AquiferConListApi, '/aquifers/' + list_params)
api.add_resource(aquifer.AquiferConPostApi, '/aquifers/' + post_params)
api.add_resource(aquifer.AquiferConApi, '/aquifers/' + get_params)
api.add_resource(aquifer.AquiferConMapApi, '/aquifers/map/<everything:project_db>')
api.add_resource(aquifer.AquiferConOutPostApi, '/aquifers/out/' + post_params)
api.add_resource(aquifer.AquiferConOutApi, '/aquifers/out/' + get_params)

api.add_resource(aquifer.AquiferAquListApi, '/aquifers/properties/' + list_params)
api.add_resource(aquifer.AquiferAquPostApi, '/aquifers/properties/' + post_params)
api.add_resource(aquifer.AquiferAquUpdateManyApi, '/aquifers/properties/' + many_params)
api.add_resource(aquifer.AquiferAquApi, '/aquifers/properties/' + get_params)

api.add_resource(aquifer.InitialAquListApi, '/aquifers/initial/' + list_params)
api.add_resource(aquifer.InitialAquPostApi, '/aquifers/initial/' + post_params)
api.add_resource(aquifer.InitialAquUpdateManyApi, '/aquifers/initial/' + many_params)
api.add_resource(aquifer.InitialAquApi, '/aquifers/initial/' + get_params)
""" Aquifers Modules   """

""" Reservoirs Modules   """
api.add_resource(reservoir.ReservoirConListApi, '/reservoirs/' + list_params)
api.add_resource(reservoir.ReservoirConPostApi, '/reservoirs/' + post_params)
api.add_resource(reservoir.ReservoirConApi, '/reservoirs/' + get_params)

api.add_resource(reservoir.ReservoirConMapApi, '/reservoirs/map/<everything:project_db>')

api.add_resource(reservoir.ReservoirConOutPostApi, '/reservoirs/out/' + post_params)
api.add_resource(reservoir.ReservoirConOutApi, '/reservoirs/out/' + get_params)

api.add_resource(reservoir.ReservoirResListApi, '/reservoirs/properties/' + list_params)
api.add_resource(reservoir.ReservoirResPostApi, '/reservoirs/properties/' + post_params)
api.add_resource(reservoir.ReservoirResUpdateManyApi, '/reservoirs/properties/' + many_params)
api.add_resource(reservoir.ReservoirResApi, '/reservoirs/properties/' + get_params)

api.add_resource(reservoir.InitialResListApi, '/reservoirs/initial/' + list_params)
api.add_resource(reservoir.InitialResPostApi, '/reservoirs/initial/' + post_params)
api.add_resource(reservoir.InitialResUpdateManyApi, '/reservoirs/initial/' + many_params)
api.add_resource(reservoir.InitialResApi, '/reservoirs/initial/' + get_params)

api.add_resource(reservoir.HydrologyResListApi, '/reservoirs/hydrology/' + list_params)
api.add_resource(reservoir.HydrologyResPostApi, '/reservoirs/hydrology/' + post_params)
api.add_resource(reservoir.HydrologyResUpdateManyApi, '/reservoirs/hydrology/' + many_params)
api.add_resource(reservoir.HydrologyResApi, '/reservoirs/hydrology/' + get_params)

api.add_resource(reservoir.SedimentResListApi, '/reservoirs/sediment/' + list_params)
api.add_resource(reservoir.SedimentResPostApi, '/reservoirs/sediment/' + post_params)
api.add_resource(reservoir.SedimentResUpdateManyApi, '/reservoirs/sediment/' + many_params)
api.add_resource(reservoir.SedimentResApi, '/reservoirs/sediment/' + get_params)

api.add_resource(reservoir.NutrientsResListApi, '/reservoirs/nutrients/' + list_params)
api.add_resource(reservoir.NutrientsResPostApi, '/reservoirs/nutrients/' + post_params)
api.add_resource(reservoir.NutrientsResUpdateManyApi, '/reservoirs/nutrients/' + many_params)
api.add_resource(reservoir.NutrientsResApi, '/reservoirs/nutrients/' + get_params)

api.add_resource(reservoir.WetlandsWetListApi, '/reservoirs/wetlands/' + list_params)
api.add_resource(reservoir.WetlandsWetPostApi, '/reservoirs/wetlands/' + post_params)
api.add_resource(reservoir.WetlandsWetUpdateManyApi, '/reservoirs/wetlands/' + many_params)
api.add_resource(reservoir.WetlandsWetApi, '/reservoirs/wetlands/' + get_params)

api.add_resource(reservoir.HydrologyWetListApi, '/reservoirs/wetlands_hydrology/' + list_params)
api.add_resource(reservoir.HydrologyWetPostApi, '/reservoirs/wetlands_hydrology/' + post_params)
api.add_resource(reservoir.HydrologyWetUpdateManyApi, '/reservoirs/wetlands_hydrology/' + many_params)
api.add_resource(reservoir.HydrologyWetApi, '/reservoirs/wetlands_hydrology/' + get_params)
""" Reservoirs Modules   """

""" Exco Modules   """
api.add_resource(exco.ExcoConListApi, '/exco/' + list_params)
api.add_resource(exco.ExcoConPostApi, '/exco/' + post_params)
api.add_resource(exco.ExcoConApi, '/exco/' + get_params)

api.add_resource(exco.ExcoConMapApi, '/exco/map/<everything:project_db>')

api.add_resource(exco.ExcoConOutPostApi, '/exco/out/' + post_params)
api.add_resource(exco.ExcoConOutApi, '/exco/out/' + get_params)

api.add_resource(exco.ExcoExcListApi, '/exco/properties/' + list_params)
api.add_resource(exco.ExcoExcPostApi, '/exco/properties/' + post_params)
api.add_resource(exco.ExcoExcUpdateManyApi, '/exco/properties/' + many_params)
api.add_resource(exco.ExcoExcApi, '/exco/properties/' + get_params)

api.add_resource(exco.ExcoOMListApi, '/exco/om/' + list_params)
api.add_resource(exco.ExcoOMPostApi, '/exco/om/' + post_params)
api.add_resource(exco.ExcoOMUpdateManyApi, '/exco/om/' + many_params)
api.add_resource(exco.ExcoOMApi, '/exco/om/' + get_params)
""" Exco Modules   """

""" Delratio Modules   """
api.add_resource(dr.DelratioConListApi, '/dr/' + list_params)
api.add_resource(dr.DelratioConPostApi, '/dr/' + post_params)
api.add_resource(dr.DelratioConApi, '/dr/' + get_params)

api.add_resource(dr.DelratioConMapApi, '/dr/map/<everything:project_db>')

api.add_resource(dr.DelratioConOutPostApi, '/dr/out/' + post_params)
api.add_resource(dr.DelratioConOutApi, '/dr/out/' + get_params)

api.add_resource(dr.DelratioDelListApi, '/dr/properties/' + list_params)
api.add_resource(dr.DelratioDelPostApi, '/dr/properties/' + post_params)
api.add_resource(dr.DelratioDelUpdateManyApi, '/dr/properties/' + many_params)
api.add_resource(dr.DelratioDelApi, '/dr/properties/' + get_params)

api.add_resource(dr.DelratioOMListApi, '/dr/om/' + list_params)
api.add_resource(dr.DelratioOMPostApi, '/dr/om/' + post_params)
api.add_resource(dr.DelratioOMUpdateManyApi, '/dr/om/' + many_params)
api.add_resource(dr.DelratioOMApi, '/dr/om/' + get_params)
""" Delratio Modules   """

""" Recall Modules   """
api.add_resource(recall.RecallConListApi, '/recall/' + list_params)
api.add_resource(recall.RecallConPostApi, '/recall/' + post_params)
api.add_resource(recall.RecallConApi, '/recall/' + get_params)

api.add_resource(recall.RecallConMapApi, '/recall/map/<everything:project_db>')

api.add_resource(recall.RecallConOutPostApi, '/recall/out/' + post_params)
api.add_resource(recall.RecallConOutApi, '/recall/out/' + get_params)

api.add_resource(recall.RecallRecListApi, '/recall/data/' + list_params)
api.add_resource(recall.RecallRecPostApi, '/recall/data/' + post_params)
api.add_resource(recall.RecallRecApi, '/recall/data/' + get_params)

api.add_resource(recall.RecallDatPostApi, '/recall/data/item/' + post_params)
api.add_resource(recall.RecallDatApi, '/recall/data/item/' + get_params)
""" Recall Modules   """

""" Landuse Modules """
api.add_resource(lum.LanduseLumListApi, '/landuse/' + list_params)
api.add_resource(lum.LanduseLumPostApi, '/landuse/' + post_params)
api.add_resource(lum.LanduseLumUpdateManyApi, '/landuse/' + many_params)
api.add_resource(lum.LanduseLumApi, '/landuse/' + get_params)

api.add_resource(lum.CntableLumListApi, '/cntable/' + list_params)
api.add_resource(lum.CntableLumPostApi, '/cntable/' + post_params)
api.add_resource(lum.CntableLumUpdateManyApi, '/cntable/' + many_params)
api.add_resource(lum.CntableLumApi, '/cntable/' + get_params)
api.add_resource(lum.CntableLumDatasetsApi, '/cntable/' + datasets_get_name_params)

api.add_resource(lum.OvntableLumListApi, '/ovntable/' + list_params)
api.add_resource(lum.OvntableLumPostApi, '/ovntable/' + post_params)
api.add_resource(lum.OvntableLumUpdateManyApi, '/ovntable/' + many_params)
api.add_resource(lum.OvntableLumApi, '/ovntable/' + get_params)
api.add_resource(lum.OvntableLumDatasetsApi, '/ovntable/' + datasets_get_name_params)

api.add_resource(lum.ConsPracLumListApi, '/cons_prac/' + list_params)
api.add_resource(lum.ConsPracLumPostApi, '/cons_prac/' + post_params)
api.add_resource(lum.ConsPracLumUpdateManyApi, '/cons_prac/' + many_params)
api.add_resource(lum.ConsPracLumApi, '/cons_prac/' + get_params)
api.add_resource(lum.ConsPracLumDatasetsApi, '/cons_prac/' + datasets_get_name_params)

api.add_resource(lum.ManagementSchListApi, '/mgt_sch/' + list_params)
api.add_resource(lum.ManagementSchPostApi, '/mgt_sch/' + post_params)
api.add_resource(lum.ManagementSchApi, '/mgt_sch/' + get_params)
""" Landuse Modules """

""" Operations Modules """
api.add_resource(ops.GrazeOpsListApi, '/ops/graze/' + list_params)
api.add_resource(ops.GrazeOpsPostApi, '/ops/graze/' + post_params)
api.add_resource(ops.GrazeOpsUpdateManyApi, '/ops/graze/' + many_params)
api.add_resource(ops.GrazeOpsApi, '/ops/graze/' + get_params)
api.add_resource(ops.GrazeOpsDatasetsApi, '/ops/graze/' + datasets_get_name_params)

api.add_resource(ops.HarvOpsListApi, '/ops/harvest/' + list_params)
api.add_resource(ops.HarvOpsPostApi, '/ops/harvest/' + post_params)
api.add_resource(ops.HarvOpsUpdateManyApi, '/ops/harvest/' + many_params)
api.add_resource(ops.HarvOpsApi, '/ops/harvest/' + get_params)
api.add_resource(ops.HarvOpsDatasetsApi, '/ops/harvest/' + datasets_get_name_params)

api.add_resource(ops.ChemAppOpsListApi, '/ops/chemapp/' + list_params)
api.add_resource(ops.ChemAppOpsPostApi, '/ops/chemapp/' + post_params)
api.add_resource(ops.ChemAppOpsUpdateManyApi, '/ops/chemapp/' + many_params)
api.add_resource(ops.ChemAppOpsApi, '/ops/chemapp/' + get_params)
api.add_resource(ops.ChemAppOpsDatasetsApi, '/ops/chemapp/' + datasets_get_name_params)

api.add_resource(ops.IrrOpsListApi, '/ops/irrigation/' + list_params)
api.add_resource(ops.IrrOpsPostApi, '/ops/irrigation/' + post_params)
api.add_resource(ops.IrrOpsUpdateManyApi, '/ops/irrigation/' + many_params)
api.add_resource(ops.IrrOpsApi, '/ops/irrigation/' + get_params)
api.add_resource(ops.IrrOpsDatasetsApi, '/ops/irrigation/' + datasets_get_name_params)

api.add_resource(ops.FireOpsListApi, '/ops/fire/' + list_params)
api.add_resource(ops.FireOpsPostApi, '/ops/fire/' + post_params)
api.add_resource(ops.FireOpsUpdateManyApi, '/ops/fire/' + many_params)
api.add_resource(ops.FireOpsApi, '/ops/fire/' + get_params)
api.add_resource(ops.FireOpsDatasetsApi, '/ops/fire/' + datasets_get_name_params)

api.add_resource(ops.SweepOpsListApi, '/ops/sweep/' + list_params)
api.add_resource(ops.SweepOpsPostApi, '/ops/sweep/' + post_params)
api.add_resource(ops.SweepOpsUpdateManyApi, '/ops/sweep/' + many_params)
api.add_resource(ops.SweepOpsApi, '/ops/sweep/' + get_params)
api.add_resource(ops.SweepOpsDatasetsApi, '/ops/sweep/' + datasets_get_name_params)

""" Operations Modules """

""" Hydrology Modules   """
api.add_resource(hydrology.HydrologyHydListApi, '/hydrology/' + list_params)
api.add_resource(hydrology.HydrologyHydPostApi, '/hydrology/' + post_params)
api.add_resource(hydrology.HydrologyHydUpdateManyApi, '/hydrology/' + many_params)
api.add_resource(hydrology.HydrologyHydApi, '/hydrology/' + get_params)

api.add_resource(hydrology.TopographyHydListApi, '/topography/' + list_params)
api.add_resource(hydrology.TopographyHydPostApi, '/topography/' + post_params)
api.add_resource(hydrology.TopographyHydUpdateManyApi, '/topography/' + many_params)
api.add_resource(hydrology.TopographyHydApi, '/topography/' + get_params)

api.add_resource(hydrology.FieldFldListApi, '/fields/' + list_params)
api.add_resource(hydrology.FieldFldPostApi, '/fields/' + post_params)
api.add_resource(hydrology.FieldFldUpdateManyApi, '/fields/' + many_params)
api.add_resource(hydrology.FieldFldApi, '/fields/' + get_params)
""" Hydrology Modules   """

""" Initialization Data Modules   """
api.add_resource(init.SoilPlantListApi, '/soil_plant/' + list_params)
api.add_resource(init.SoilPlantPostApi, '/soil_plant/' + post_params)
api.add_resource(init.SoilPlantUpdateManyApi, '/soil_plant/' + many_params)
api.add_resource(init.SoilPlantApi, '/soil_plant/' + get_params)

api.add_resource(init.OMWaterListApi, '/om_water/' + list_params)
api.add_resource(init.OMWaterPostApi, '/om_water/' + post_params)
api.add_resource(init.OMWaterUpdateManyApi, '/om_water/' + many_params)
api.add_resource(init.OMWaterApi, '/om_water/' + get_params)

api.add_resource(init.PlantIniListApi, '/plant_ini/' + list_params)
api.add_resource(init.PlantIniPostApi, '/plant_ini/' + post_params)
api.add_resource(init.PlantIniApi, '/plant_ini/' + get_params)
api.add_resource(init.PlantIniItemPostApi, '/plant_ini/item/' + post_params)
api.add_resource(init.PlantIniItemApi, '/plant_ini/item/' + get_params)
""" Initialization Data Modules   """

""" Databases - Modules   """
api.add_resource(hru_parm_db.PlantsPltListApi, '/db/plants/' + list_params)
api.add_resource(hru_parm_db.PlantsPltPostApi, '/db/plants/' + post_params)
api.add_resource(hru_parm_db.PlantsPltUpdateManyApi, '/db/plants/' + many_params)
api.add_resource(hru_parm_db.PlantsPltApi, '/db/plants/' + get_params)
api.add_resource(hru_parm_db.PlantsPltDatasetsApi, '/db/plants/' + datasets_get_name_params)

api.add_resource(hru_parm_db.FertilizerFrtListApi, '/db/fertilizer/' + list_params)
api.add_resource(hru_parm_db.FertilizerFrtPostApi, '/db/fertilizer/' + post_params)
api.add_resource(hru_parm_db.FertilizerFrtUpdateManyApi, '/db/fertilizer/' + many_params)
api.add_resource(hru_parm_db.FertilizerFrtApi, '/db/fertilizer/' + get_params)
api.add_resource(hru_parm_db.FertilizerFrtDatasetsApi, '/db/fertilizer/' + datasets_get_name_params)

api.add_resource(hru_parm_db.TillageTilListApi, '/db/tillage/' + list_params)
api.add_resource(hru_parm_db.TillageTilPostApi, '/db/tillage/' + post_params)
api.add_resource(hru_parm_db.TillageTilUpdateManyApi, '/db/tillage/' + many_params)
api.add_resource(hru_parm_db.TillageTilApi, '/db/tillage/' + get_params)
api.add_resource(hru_parm_db.TillageTilDatasetsApi, '/db/tillage/' + datasets_get_name_params)

api.add_resource(hru_parm_db.PesticidePstListApi, '/db/pesticides/' + list_params)
api.add_resource(hru_parm_db.PesticidePstPostApi, '/db/pesticides/' + post_params)
api.add_resource(hru_parm_db.PesticidePstUpdateManyApi, '/db/pesticides/' + many_params)
api.add_resource(hru_parm_db.PesticidePstApi, '/db/pesticides/' + get_params)
api.add_resource(hru_parm_db.PesticidePstDatasetsApi, '/db/pesticides/' + datasets_get_name_params)

api.add_resource(hru_parm_db.UrbanUrbListApi, '/db/urban/' + list_params)
api.add_resource(hru_parm_db.UrbanUrbPostApi, '/db/urban/' + post_params)
api.add_resource(hru_parm_db.UrbanUrbUpdateManyApi, '/db/urban/' + many_params)
api.add_resource(hru_parm_db.UrbanUrbApi, '/db/urban/' + get_params)
api.add_resource(hru_parm_db.UrbanUrbDatasetsApi, '/db/urban/' + datasets_get_name_params)

api.add_resource(hru_parm_db.SepticSepListApi, '/db/septic/' + list_params)
api.add_resource(hru_parm_db.SepticSepPostApi, '/db/septic/' + post_params)
api.add_resource(hru_parm_db.SepticSepUpdateManyApi, '/db/septic/' + many_params)
api.add_resource(hru_parm_db.SepticSepApi, '/db/septic/' + get_params)
api.add_resource(hru_parm_db.SepticSepDatasetsApi, '/db/septic/' + datasets_get_name_params)

api.add_resource(hru_parm_db.SnowSnoListApi, '/db/snow/' + list_params)
api.add_resource(hru_parm_db.SnowSnoPostApi, '/db/snow/' + post_params)
api.add_resource(hru_parm_db.SnowSnoUpdateManyApi, '/db/snow/' + many_params)
api.add_resource(hru_parm_db.SnowSnoApi, '/db/snow/' + get_params)
api.add_resource(hru_parm_db.SnowSnoDatasetsApi, '/db/snow/' + datasets_get_name_params)
""" Databases - Modules   """

""" Soils Modules """
api.add_resource(soils.SoilsSolListApi, '/soils/' + list_params)
api.add_resource(soils.SoilsSolPostApi, '/soils/' + post_params)
api.add_resource(soils.SoilsSolApi, '/soils/' + get_params)
api.add_resource(soils.SoilsSolLayerPostApi, '/soils/layer/' + post_params)
api.add_resource(soils.SoilsSolLayerApi, '/soils/layer/' + get_params)

api.add_resource(soils.NutrientsSolListApi, '/soil-nutrients/' + list_params)
api.add_resource(soils.NutrientsSolPostApi, '/soil-nutrients/' + post_params)
api.add_resource(soils.NutrientsSolUpdateManyApi, '/soil-nutrients/' + many_params)
api.add_resource(soils.NutrientsSolApi, '/soil-nutrients/' + get_params)

api.add_resource(soils.SoilsLteSolListApi, '/soils-lte/' + list_params)
api.add_resource(soils.SoilsLteSolPostApi, '/soils-lte/' + post_params)
api.add_resource(soils.SoilsLteSolUpdateManyApi, '/soils-lte/' + many_params)
api.add_resource(soils.SoilsLteSolApi, '/soils-lte/' + get_params)
""" Soils Modules """

""" Landscape Units Modules """
api.add_resource(regions.LsUnitDefListApi, '/ls_units/' + list_params)
api.add_resource(regions.LsUnitDefPostApi, '/ls_units/' + post_params)
api.add_resource(regions.LsUnitDefApi, '/ls_units/' + get_params)

api.add_resource(regions.LsUnitEleListApi, '/ls_units/elements/' + list_params)
api.add_resource(regions.LsUnitElePostApi, '/ls_units/elements/' + post_params)
api.add_resource(regions.LsUnitEleApi, '/ls_units/elements/' + get_params)
""" Landscape Units Modules """

""" Change Modules """
api.add_resource(change.CodesSftApi, '/change/codes/<everything:project_db>')

api.add_resource(change.CalParmsCalListApi, '/change/cal_parms/' + list_params)
api.add_resource(change.CalParmsCalApi, '/change/cal_parms/' + get_params)
api.add_resource(change.CalParmsTypesApi, '/change/cal_parms/types/<everything:project_db>')

api.add_resource(change.CalibrationCalListApi, '/change/calibration/' + list_params)
api.add_resource(change.CalibrationCalPostApi, '/change/calibration/' + post_params)
api.add_resource(change.CalibrationCalApi, '/change/calibration/' + get_params)

api.add_resource(change.WbParmsSftListApi, '/change/soft/parms/wb/' + list_params)
api.add_resource(change.WbParmsSftPostApi, '/change/soft/parms/wb/' + post_params)
api.add_resource(change.WbParmsSftApi, '/change/soft/parms/wb/' + get_params)

api.add_resource(change.ChsedParmsSftListApi, '/change/soft/parms/chsed/' + list_params)
api.add_resource(change.ChsedParmsSftPostApi, '/change/soft/parms/chsed/' + post_params)
api.add_resource(change.ChsedParmsSftApi, '/change/soft/parms/chsed/' + get_params)

api.add_resource(change.PlantParmsSftListApi, '/change/soft/parms/plant/' + list_params)
api.add_resource(change.PlantParmsSftPostApi, '/change/soft/parms/plant/' + post_params)
api.add_resource(change.PlantParmsSftApi, '/change/soft/parms/plant/' + get_params)

api.add_resource(change.WaterBalanceSftListApi, '/change/soft/regions/wb/' + list_params)
api.add_resource(change.WaterBalanceSftPostApi, '/change/soft/regions/wb/' + post_params)
api.add_resource(change.WaterBalanceSftApi, '/change/soft/regions/wb/' + get_params)

api.add_resource(change.ChsedBudgetSftListApi, '/change/soft/regions/chsed/' + list_params)
api.add_resource(change.ChsedBudgetSftPostApi, '/change/soft/regions/chsed/' + post_params)
api.add_resource(change.ChsedBudgetSftApi, '/change/soft/regions/chsed/' + get_params)

api.add_resource(change.PlantGroSftListApi, '/change/soft/regions/plant/' + list_params)
api.add_resource(change.PlantGroSftPostApi, '/change/soft/regions/plant/' + post_params)
api.add_resource(change.PlantGroSftApi, '/change/soft/regions/plant/' + get_params)
""" Change Modules """

""" Decision Table Modules """
api.add_resource(decision_table.DTableDtlListApi, '/decision_table/<table_type>/' + list_params)
api.add_resource(decision_table.DTableDtlApi, '/decision_table/' + get_params)
""" Decision Table """

""" Structural Modules """
api.add_resource(structural.BmpuserStrListApi, '/structural/bmpuser/' + list_params)
api.add_resource(structural.BmpuserStrPostApi, '/structural/bmpuser/' + post_params)
api.add_resource(structural.BmpuserStrUpdateManyApi, '/structural/bmpuser/' + many_params)
api.add_resource(structural.BmpuserStrApi, '/structural/bmpuser/' + get_params)
api.add_resource(structural.BmpuserStrDatasetsApi, '/structural/bmpuser/' + datasets_get_name_params)

api.add_resource(structural.TiledrainStrListApi, '/structural/tiledrain/' + list_params)
api.add_resource(structural.TiledrainStrPostApi, '/structural/tiledrain/' + post_params)
api.add_resource(structural.TiledrainStrUpdateManyApi, '/structural/tiledrain/' + many_params)
api.add_resource(structural.TiledrainStrApi, '/structural/tiledrain/' + get_params)
api.add_resource(structural.TiledrainStrDatasetsApi, '/structural/tiledrain/' + datasets_get_name_params)

api.add_resource(structural.SepticStrListApi, '/structural/septic/' + list_params)
api.add_resource(structural.SepticStrPostApi, '/structural/septic/' + post_params)
api.add_resource(structural.SepticStrUpdateManyApi, '/structural/septic/' + many_params)
api.add_resource(structural.SepticStrApi, '/structural/septic/' + get_params)
api.add_resource(structural.SepticStrDatasetsApi, '/structural/septic/' + datasets_get_name_params)

api.add_resource(structural.FilterstripStrListApi, '/structural/filterstrip/' + list_params)
api.add_resource(structural.FilterstripStrPostApi, '/structural/filterstrip/' + post_params)
api.add_resource(structural.FilterstripStrUpdateManyApi, '/structural/filterstrip/' + many_params)
api.add_resource(structural.FilterstripStrApi, '/structural/filterstrip/' + get_params)
api.add_resource(structural.FilterstripStrDatasetsApi, '/structural/filterstrip/' + datasets_get_name_params)

api.add_resource(structural.GrassedwwStrListApi, '/structural/grassedww/' + list_params)
api.add_resource(structural.GrassedwwStrPostApi, '/structural/grassedww/' + post_params)
api.add_resource(structural.GrassedwwStrUpdateManyApi, '/structural/grassedww/' + many_params)
api.add_resource(structural.GrassedwwStrApi, '/structural/grassedww/' + get_params)
api.add_resource(structural.GrassedwwStrDatasetsApi, '/structural/grassedww/' + datasets_get_name_params)
""" Structural Modules """

if __name__ == '__main__':
	sys.stdout = Unbuffered(sys.stdout)
	parser = argparse.ArgumentParser(description="SWAT+ Editor REST API")
	parser.add_argument("port", type=str, help="port number to run API", default=5000, nargs="?")
	args = parser.parse_args()
	app.run(port=int(args.port))
