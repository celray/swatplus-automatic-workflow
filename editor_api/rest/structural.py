from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project import base as project_base
from database.project.setup import SetupProjectDatabase
from database.project.config import Project_config
from database.project import structural

from database.datasets.setup import SetupDatasetsDatabase
from database.datasets import structural as ds

bmpuser_name = 'Best management practice'
tiledrain_name = 'Tile drains'
septic_name = 'Septic Systems'
filter_name = 'Filter Strip'
grassedww_name = 'Grassed Waterways'

""" Structural - Tile Drain """
class TiledrainStrListApi(BaseRestModel):
	def get(self, project_db):
		table = structural.Tiledrain_str
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols)


class TiledrainStrApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, structural.Tiledrain_str, tiledrain_name)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, structural.Tiledrain_str, tiledrain_name)

	def put(self, project_db, id):
		return self.base_put(project_db, id, structural.Tiledrain_str, tiledrain_name)


class TiledrainStrPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, structural.Tiledrain_str, tiledrain_name)


class TiledrainStrUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, structural.Tiledrain_str)

	def put(self, project_db):
		return self.base_put_many(project_db, structural.Tiledrain_str, tiledrain_name)


class TiledrainStrDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Tiledrain_str, tiledrain_name)
""" Structural -Tile Drains"""


""" Structural - Septic System """
class SepticStrListApi(BaseRestModel):
	def get(self, project_db):
		table = structural.Septic_str
		filter_cols = [table.name]
		return self.base_paged_list(project_db, table, filter_cols)


class SepticStrApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, structural.Septic_str, septic_name)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, structural.Septic_str, septic_name)

	def put(self, project_db, id):
		return self.base_put(project_db, id, structural.Septic_str, septic_name)


class SepticStrPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, structural.Septic_str, septic_name)


class SepticStrUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, structural.Septic_str)

	def put(self, project_db):
		return self.base_put_many(project_db, structural.Septic_str, septic_name)
	   

class SepticStrDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Septic_str, septic_name)
""" Structural - User Septic System """


""" Structural - Filter Strips """
class FilterstripStrListApi(BaseRestModel):
	def get(self, project_db):
		table = structural.Filterstrip_str
		filter_cols = [table.name, table.description]
		return self.base_paged_list(project_db, table, filter_cols)


class FilterstripStrApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, structural.Filterstrip_str, filter_name)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, structural.Filterstrip_str, filter_name)

	def put(self, project_db, id):
		return self.base_put(project_db, id, structural.Filterstrip_str, filter_name)


class FilterstripStrPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, structural.Filterstrip_str, filter_name)


class FilterstripStrUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, structural.Filterstrip_str)

	def put(self, project_db):
		return self.base_put_many(project_db, structural.Filterstrip_str, filter_name)


class FilterstripStrDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Filterstrip_str, filter_name)
""" Structural - User Filter Strips """

""" Structural - Grassed Waterways """
class GrassedwwStrListApi(BaseRestModel):
	def get(self, project_db):
		table = structural.Grassedww_str
		filter_cols = [table.name, table.description]
		return self.base_paged_list(project_db, table, filter_cols)


class GrassedwwStrApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, structural.Grassedww_str, grassedww_name)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, structural.Grassedww_str, grassedww_name)

	def put(self, project_db, id):
		return self.base_put(project_db, id, structural.Grassedww_str, grassedww_name)


class GrassedwwStrPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, structural.Grassedww_str, grassedww_name)


class GrassedwwStrUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, structural.Grassedww_str)

	def put(self, project_db):
		return self.base_put_many(project_db, structural.Grassedww_str, grassedww_name)


class GrassedwwStrDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Grassedww_str, grassedww_name)
""" Structural - User Grassed Waterways """

""" Structural - User BMPs """
class BmpuserStrListApi(BaseRestModel):
	def get(self, project_db):
		table = structural.Bmpuser_str
		filter_cols = [table.name, table.description]
		return self.base_paged_list(project_db, table, filter_cols)


class BmpuserStrApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, structural.Bmpuser_str, bmpuser_name)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, structural.Bmpuser_str, bmpuser_name)

	def put(self, project_db, id):
		return self.base_put(project_db, id, structural.Bmpuser_str, bmpuser_name)


class BmpuserStrPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, structural.Bmpuser_str, bmpuser_name)


class BmpuserStrUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, structural.Bmpuser_str)

	def put(self, project_db):
		return self.base_put_many(project_db, structural.Bmpuser_str, bmpuser_name)


class BmpuserStrDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds.Bmpuser_str, bmpuser_name)
""" Structural - User BMPs """
