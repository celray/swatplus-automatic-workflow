import json

class CheckBase:
	def toJson(self):
		return json.loads(json.dumps(self, default=lambda o: o.__dict__))

class CheckInfo(CheckBase):
	def __init__(self):
		self.simulationLength = 0
		self.warmUp = 0
		self.hrus = 0
		self.subbasins = 0
		self.lsus = 0
		self.weatherMethod = 'simulated'
		self.watershedArea = 0
		self.swatVersion = 'development'


class CheckHydrology(CheckBase):
	def __init__(self):
		self.warnings = []
		self.et = 0
		self.etPlant = 0
		self.etSoil = 0
		self.pet = 0
		self.precipitation = 0
		self.averageCn = 0
		self.surfaceRunoff = 0
		self.lateralFlow = 0
		self.returnFlow = 0
		self.percolation = 0
		self.revap = 0
		self.recharge = 0
		self.streamflowPrecipitation = 0
		self.baseflowTotalFlow = 0
		self.surfaceRunoffTotalFlow = 0
		self.percolationPrecipitation = 0
		self.deepRechargePrecipitation = 0
		self.etPrecipitation = 0
		self.monthlyBasinValues = []
		self.irrigation = 0
		self.tile = 0


class CheckSediment(CheckBase):
	def __init__(self):
		self.warnings = []
		self.surfaceRunoff = 0
		self.maxUplandSedimentYield = 0
		self.avgUplandSedimentYield = 0
		self.inletSediment = 0
		self.inStreamSedimentChange = 0


class CheckNitrogenCycle(CheckBase):
	def __init__(self):
		self.warnings = []
		self.initialNO3 = 0
		self.finalNO3 = 0
		self.initialOrgN = 0
		self.finalOrgN = 0
		self.volatilization = 0
		self.denitrification = 0
		self.nH4InOrgNFertilizer = 0
		self.nO3InOrgNFertilizer = 0
		self.plantUptake = 0
		self.nitrification = 0
		self.mineralization = 0
		self.totalFertilizerN = 0
		self.orgNFertilizer = 0
		self.activeToStableOrgN = 0
		self.residueMineralization = 0
		self.nFixation = 0


class CheckPhosphorusCycle(CheckBase):
	def __init__(self):
		self.warnings = []
		self.initialMinP = 0
		self.finalMinP = 0
		self.initialOrgP = 0
		self.finalOrgP = 0
		self.totalFertilizerP = 0
		self.inOrgPFertilizer = 0
		self.plantUptake = 0
		self.orgPFertilizer = 0
		self.residueMineralization = 0
		self.mineralization = 0
		self.activeSolution = 0
		self.stableActive = 0


class CheckPlantGrowth(CheckBase):
	def __init__(self):
		self.warnings = []
		self.tempStressDays = 0
		self.waterStressDays = 0
		self.nStressDays = 0
		self.pStressDays = 0
		self.avgBiomass = 0
		self.avgYield = 0
		self.nRemoved = 0
		self.pRemoved = 0
		self.totalFertilizerN = 0
		self.totalFertilizerP = 0
		self.plantUptakeN = 0
		self.plantUptakeP = 0
		self.soilAirStressDays = 0


class CheckNitrogenLosses(CheckBase):
	def __init__(self):
		self.totalLoss = 0
		self.orgN = 0
		self.surfaceRunoff = 0
		self.leached = 0
		self.lateralFlow = 0
		self.groundwaterYield = 0
		self.solubilityRatio = 0


class CheckPhosphorusLosses(CheckBase):
	def __init__(self):
		self.totalLoss = 0
		self.orgP = 0
		self.surfaceRunoff = 0
		self.solubilityRatio = 0


class CheckLandscapeLosses(CheckBase):
	def __init__(self):
		self.warnings = []
		self.nLosses = None
		self.pLosses = None


class CheckLandUseRow(CheckBase):
	def __init__(self):
		self.landUse = ''
		self.area = 0
		self.cn = 0
		self.awc = 0
		self.usle_ls = 0
		self.irr = 0
		self.prec = 0
		self.surq = 0
		self.gwq = 0
		self.et = 0
		self.sed = 0
		self.no3 = 0
		self.orgn = 0
		self.biom = 0
		self.yld = 0


class CheckLandUseSummary(CheckBase):
	def __init__(self):
		self.warnings = []
		self.hruLevelWarnings = []
		self.landUseRows = []


class CheckReach(CheckBase):
	def __init__(self):
		self.id = ''
		self.sediment = 0
		self.phosphorus = 0
		self.nitrogen = 0


class CheckInstreamProcesses(CheckBase):
	def __init__(self):
		self.warnings = []
		self.reaches = []
		self.uplandSedimentYield = 0
		self.instreamSedimentChange = 0
		self.channelErosion = 0
		self.channelDeposition = 0
		self.totalN = 0
		self.totalP = 0
		self.totalStreamflowLosses = 0
		self.evaporationLoss = 0
		self.seepageLoss = 0


class CheckPointSourcesLoad(CheckBase):
	def __init__(self):
		self.flow = 0
		self.sediment = 0
		self.nitrogen = 0
		self.phosphorus = 0


class CheckPointSources(CheckBase):
	def __init__(self):
		self.warnings = []
		self.subbasinLoad = None
		self.pointSourceInletLoad = None
		self.fromInletAndPointSource = None


class CheckReservoirRow(CheckBase):
	def __init__(self):
		self.id = ''
		self.sediment = 0
		self.phosphorus = 0
		self.nitrogen = 0
		self.volumeRatio = 0
		self.fractionEmpty = 0
		self.seepage = 0
		self.evapLoss = 0


class CheckAvgTrappingEfficiency(CheckBase):
	def __init__(self):
		self.sediment = 0
		self.phosphorus = 0
		self.nitrogen = 0


class CheckAvgWaterLoss(CheckBase):
	def __init__(self):
		self.totalRemoved = 0
		self.evaporation = 0
		self.seepage = 0


class CheckAvgReservoirTrend(CheckBase):
	def __init__(self):
		self.numberReservoirs = 0
		self.maxVolume = 0
		self.minVolume = 0
		self.fractionEmpty = 0


class CheckReservoirs(CheckBase):
	def __init__(self):
		self.warnings = []
		self.reservoirRows = []
		self.avgTrappingEfficiencies = None
		self.avgWaterLosses = None
		self.avgReservoirTrends = None
