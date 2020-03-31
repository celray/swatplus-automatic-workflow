from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project import base as project_base
from database.project.setup import SetupProjectDatabase
from database.project.config import Project_config
from database.project import hru_parm_db

from database.datasets.setup import SetupDatasetsDatabase
from database.datasets import hru_parm_db as ds

plant_name = 'Plant'
fertilizer_name = 'Fertilizer'
tillage_name = 'Tillage'
pesticide_name = 'Pesticide'
urban_name = 'Urban'
septic_name = 'Septic'
snow_name = 'Snow'

""" Database Plants"""
class PlantsPltListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = hru_parm_db.Plants_plt
		list_name = 'plants'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class PlantsPltApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, hru_parm_db.Plants_plt, plant_name)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, hru_parm_db.Plants_plt, plant_name)

	def put(self, project_db, id):
		return self.base_put(project_db, id, hru_parm_db.Plants_plt, plant_name)


class PlantsPltUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, hru_parm_db.Plants_plt)

	def put(self, project_db):
		return self.base_put_many(project_db, hru_parm_db.Plants_plt, plant_name)		


class PlantsPltPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, hru_parm_db.Plants_plt, plant_name)


class PlantsPltDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Plants_plt, plant_name)

""" Database - Plants"""
""" Database - Fertilizer"""

class FertilizerFrtListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = hru_parm_db.Fertilizer_frt
		list_name = 'fertilizer'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class FertilizerFrtApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, hru_parm_db.Fertilizer_frt, fertilizer_name)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, hru_parm_db.Fertilizer_frt, fertilizer_name)

	def put(self, project_db, id):
		return self.base_put(project_db, id, hru_parm_db.Fertilizer_frt, fertilizer_name)


class FertilizerFrtUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, hru_parm_db.Fertilizer_frt)

	def put(self, project_db):
		return self.base_put_many(project_db, hru_parm_db.Fertilizer_frt, fertilizer_name)


class FertilizerFrtPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, hru_parm_db.Fertilizer_frt, fertilizer_name)


class FertilizerFrtDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Fertilizer_frt, fertilizer_name)

""" Database - Fertilizer"""
""" Database - Tillage"""

class TillageTilListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = hru_parm_db.Tillage_til
		list_name = 'tillage'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class TillageTilApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, hru_parm_db.Tillage_til, tillage_name)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, hru_parm_db.Tillage_til, tillage_name)

	def put(self, project_db, id):
		return self.base_put(project_db, id, hru_parm_db.Tillage_til, tillage_name)


class TillageTilUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, hru_parm_db.Tillage_til)

	def put(self, project_db):
		return self.base_put_many(project_db, hru_parm_db.Tillage_til, tillage_name)


class TillageTilPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, hru_parm_db.Tillage_til, tillage_name)


class TillageTilDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Tillage_til, tillage_name)

""" Database - Tillage"""

""" Database - Pesticide"""
class PesticidePstListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = hru_parm_db.Pesticide_pst
		list_name = 'pesticides'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class PesticidePstApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, hru_parm_db.Pesticide_pst, pesticide_name)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, hru_parm_db.Pesticide_pst, pesticide_name)

	def put(self, project_db, id):
		return self.base_put(project_db, id, hru_parm_db.Pesticide_pst, pesticide_name)


class PesticidePstUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, hru_parm_db.Pesticide_pst)

	def put(self, project_db):
		return self.base_put_many(project_db, hru_parm_db.Pesticide_pst, pesticide_name)


class PesticidePstPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, hru_parm_db.Pesticide_pst, pesticide_name)


class PesticidePstDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Pesticide_pst, pesticide_name)
""" Database - Pesticide"""

""" Database - Urban"""    

class UrbanUrbListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = hru_parm_db.Urban_urb
		list_name = 'urban'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class UrbanUrbApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, hru_parm_db.Urban_urb, urban_name)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, hru_parm_db.Urban_urb, urban_name)

	def put(self, project_db, id):
		return self.base_put(project_db, id, hru_parm_db.Urban_urb, urban_name)


class UrbanUrbUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, hru_parm_db.Urban_urb)

	def put(self, project_db):
		return self.base_put_many(project_db, hru_parm_db.Urban_urb, urban_name)


class UrbanUrbPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, hru_parm_db.Urban_urb, urban_name)


class UrbanUrbDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Urban_urb, urban_name)
""" Database - Urban"""

""" Database - Septic"""     

class SepticSepListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = hru_parm_db.Septic_sep
		list_name = 'septic'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class SepticSepApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, hru_parm_db.Septic_sep, septic_name)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, hru_parm_db.Septic_sep, septic_name)

	def put(self, project_db, id):
		return self.base_put(project_db, id, hru_parm_db.Septic_sep, septic_name)


class SepticSepUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, hru_parm_db.Septic_sep)

	def put(self, project_db):
		return self.base_put_many(project_db, hru_parm_db.Septic_sep, septic_name)


class SepticSepPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, hru_parm_db.Septic_sep, septic_name)


class SepticSepDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Septic_sep, septic_name)

""" Database - Septic"""
""" Database - Snow"""     

class SnowSnoListApi(BaseRestModel):
	def get(self, project_db, sort, reverse, page, items_per_page):
		table = hru_parm_db.Snow_sno
		list_name = 'snow'
		return self.base_paged_list(project_db, sort, reverse, page, items_per_page, table, list_name)


class SnowSnoApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, hru_parm_db.Snow_sno, snow_name)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, hru_parm_db.Snow_sno, snow_name)

	def put(self, project_db, id):
		return self.base_put(project_db, id, hru_parm_db.Snow_sno, snow_name)


class SnowSnoUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, hru_parm_db.Snow_sno)

	def put(self, project_db):
		return self.base_put_many(project_db, hru_parm_db.Snow_sno, snow_name)


class SnowSnoPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, hru_parm_db.Snow_sno, snow_name)


class SnowSnoDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Snow_sno, snow_name)

""" Database - Snow"""