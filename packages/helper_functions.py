'''
date        : 31/03/2020
description : this module is a list of functions used in the workflow

author      : Celray James CHAWANDA
contact     : celray.chawanda@outlook.com
licence     : MIT 2020
'''
# importance
import os
import sys
import shutil
from glob import glob
from shutil import copyfile, copytree
import pickle
import xml.etree.ElementTree as ET
from osgeo import gdal
from osgeo import ogr
from osgeo import gdalconst

def copy_directory(src, parent_dst, core_count):
    try:
        shutil.copytree(
            src, "{dst_parent}/{core_number}".format(
                core_number=core_count,
                dst_parent=parent_dst))
        return True
    except:
        return False


def write_to(filename, text_to_write, report_=False):
    try:
        g = open(filename, 'w')
        g.write(text_to_write)
        g.close
        if report_:
            print('\n\t> file saved to ' + filename)
        return True
    except:
        return False


def raster_statistics(tif_file):
    ds = gdal.Open(tif_file)
    minimum, maximum, mean, std_dev = ds.GetRasterBand(1).GetStatistics(0, 1)

    class gdal_stats:
        def __init__(self, mn, mx, mean, std_dev):
            self.minimum = mn
            self.maximum = mx
            self.mean = mean
            self.stdev = std_dev

        def __repr__(self):
            return 'min: {0}, max: {1}, mean: {2}, sdev: {3}'.format(
                self.minimum, self.maximum,  self.mean, self.stdev)

    all_stats = gdal_stats(minimum, maximum, mean, std_dev)
    return all_stats


def list_folders(directory):
    """
    directory: string or pathlike object
    """
    all_dirs = os.listdir(directory)
    dirs = [dir_ for dir_ in all_dirs if os.path.isdir(
        os.path.join(directory, dir_))]
    return dirs


def xml_children_attributes(xml_file_name, x_path):
    root = ET.parse(xml_file_name).getroot()
    result = {}
    for element in root.findall(x_path):
        for child in element:
            result[child.tag] = child.text
    return result


def list_files(folder, extension="*"):
    if folder.endswith("/"):
        if extension == "*":
            list_of_files = glob(folder + "*")
        else:
            list_of_files = glob(folder + "*." + extension)
    else:
        if extension == "*":
            list_of_files = glob(folder + "/*")
        else:
            list_of_files = glob(folder + "/*." + extension)
    return list_of_files


def copy_file(src, dst):
    if not os.path.isdir(os.path.dirname(dst)):
        os.makedirs(os.path.dirname(dst))
    copyfile(src, dst)


def file_name(path_, extension=True):
    if extension:
        fn = os.path.basename(path_)
    else:
        fn = os.path.basename(path_).split(".")[0]
    return(fn)

def rasterise(shapefile, column, raster_template, destination):
    '''
    adapted from https://gis.stackexchange.com/questions/212795/rasterizing-shapefiles-with-gdal-and-python#212812

    '''
    data = gdal.Open(raster_template, gdalconst.GA_ReadOnly)
    prj_wkt = data.GetProjection()
    geo_transform = data.GetGeoTransform()
    #source_layer = data.GetLayer()
    x_min = geo_transform[0]
    y_max = geo_transform[3]
    x_max = x_min + geo_transform[1] * data.RasterXSize
    y_min = y_max + geo_transform[5] * data.RasterYSize
    x_res = data.RasterXSize
    y_res = data.RasterYSize
    polygon_data = ogr.Open(shapefile)
    layer_data = polygon_data.GetLayer()
    pixel_width = geo_transform[1]
    target_ds = gdal.GetDriverByName('GTiff').Create(destination, x_res, y_res, 1, gdal.GDT_Float32)
    target_ds.SetGeoTransform((x_min, pixel_width, 0, y_min, 0, pixel_width))
    target_ds.SetProjection(prj_wkt)
    band = target_ds.GetRasterBand(1)
    NoData_value = -999
    band.SetNoDataValue(NoData_value)
    band.FlushCache()
    gdal.RasterizeLayer(target_ds, [1], layer_data, options=["ATTRIBUTE={col}".format(col = column)])
    target_ds = None
    return True

def clear_directory(dir_path, fail_message = "cannot delete folder"):
    try:
        if os.path.isdir(dir_path):
            shutil.rmtree(dir_path)
            os.makedirs(dir_path)
    except:
        print("\t! {fail_message}".format(fail_message = fail_message))

def python_variable(filename):

    with open(filename, "rb") as f:
        variable = pickle.load(f)

    return variable


def get_extents(raster):
    src = gdal.Open(raster)
    upper_lef_x, xres, xskew, upper_left_y, yskew, yres = src.GetGeoTransform()
    lower_right_x = upper_lef_x + (src.RasterXSize * xres)
    lower_right_y = upper_left_y + (src.RasterYSize * yres)
    return upper_lef_x, lower_right_y, lower_right_x, upper_left_y


def read_from(filename):
    try:
        g = open(filename, 'r')
    except:
        print(
            "\t ! error reading {0}, make sure the file exists".format(filename))
        return
    file_text = g.readlines()
    g.close
    return file_text


def show_progress(count, end_val, string_before="percent complete", string_after="", bar_length=30):
    percent = float(count) / end_val
    hashes = "#" * int(round(percent * bar_length))
    spaces = '_' * (bar_length - len(hashes))
    sys.stdout.write("\r{str_b} [{bar}] {pct}% {str_after}\t\t".format(
        str_b=string_before,
        bar=hashes + spaces,
        pct='{0:.2f}'.format(percent * 100),
        str_after=string_after))
    sys.stdout.flush()
