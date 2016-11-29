#!/usr/bin/env python

import os
from ConfigParser import SafeConfigParser

import click
import osgeo

from utools.constants import UgridToolsConstants
from utools.logging import log_entry, log


@click.group()
def utools_cli():
    pass


@utools_cli.command(help='Create ESMF unstructured NetCDF files from supported geometry containers (ESRI Shapefile, '
                         'ESRI File Geodatabase).')
@click.option('-u', '--source_uid', required=True, help='Name of unique identifier in source geometry container.')
@click.option('-s', '--source', type=click.Path(exists=True, dir_okay=True), required=True,
              help='Path to input geometry container.')
@click.option('-e', '--esmf_format', type=click.Path(writable=True), required=True,
              help='Path to the output ESMF unstructured NetCDF file.')
@click.option('--feature-class', type=str, required=False,
              help='Feature class name in source ESRI File Geodatabase. Required when converting file geodatabases.')
@click.option('--config-path', type=click.Path(exists=True), required=False,
              help='Path to configuration file containing arguments difficult to format in terminals (CRS WKT). '
                   'Required for CRS conversions.')
@click.option('--dest_crs_index', type=str, nargs=1,
              help='The key name with optional section for pulling the CRS WKT from file. No spaces in option and/or '
                   'section names. With a section: "section,option". Without a section: "option". See {} for example '
                   'format.'.format('http://bit.ly/2bgKMU9'))
@click.option('-n', '--node-threshold', type=int, default=UgridToolsConstants.NODE_THRESHOLD,
              help='(default={}) Approximate limit on the number of nodes in an element part. The default node '
                   'threshold provides significant performance improvement.'.format(UgridToolsConstants.NODE_THRESHOLD))
@click.option('--debug/--no-debug', required=False, default=False,
              help='If "--debug", execute in debug mode converting only the first record of the geometry container.')
def convert(source_uid, source, esmf_format, feature_class, config_path, dest_crs_index, node_threshold, debug):
    from utools.prep.prep_shapefiles import convert_to_esmf_format

    log_entry('info', 'Started converting to ESMF format: {}'.format(source), rank=0)

    # Set the feature class name even if it is None. Feature class name is required for a file geodatabase.
    driver_kwargs = {'feature_class': feature_class}

    # If there is a destination CRS, read in the value and convert to a spatial reference object for the geometry
    # manager.
    if dest_crs_index is not None:
        log.debug(('dest_crs_index', dest_crs_index))
        dest_crs_index = dest_crs_index.split(',')
        if len(dest_crs_index) == 1:
            crs_section = None
            crs_option = dest_crs_index[0]
        elif len(dest_crs_index) == 2:
            crs_section, crs_option = dest_crs_index
        else:
            raise NotImplementedError(len(dest_crs_index))
        sp = SafeConfigParser()
        sp.read(config_path)
        crs_wkt = sp.get(crs_section, crs_option)
        dest_crs = osgeo.osr.SpatialReference()
        dest_crs.ImportFromWkt(crs_wkt)
    else:
        dest_crs = None

    convert_to_esmf_format(esmf_format, source, source_uid, node_threshold=node_threshold, driver_kwargs=driver_kwargs,
                           debug=debug, dest_crs=dest_crs)
    log_entry('info', 'Finished converting to ESMF format: {}'.format(source), rank=0)


@utools_cli.command(help='Create a merged ESMF weights file.')
@click.option('-c', '--catchment-directory', required=True,
              help='Path to the directory containing the ESMF unstructured files.')
@click.option('-w', '--weight-directory', type=click.Path(exists=True), required=True,
              help='Path to the directory containing the weights files.')
@click.option('-m', '--master-path', type=click.Path(writable=True), required=True,
              help='Path to the output merged weight file.')
def merge(catchment_directory, weight_directory, master_path):
    from utools.regrid.core_ocgis import create_merged_weights

    weight_files = []
    esmf_unstructured = []

    def _collect_and_sort_(seq, directory, startswith):
        for l in os.listdir(directory):
            if l.startswith(startswith):
                seq.append(os.path.join(directory, l))
        seq.sort()

    _collect_and_sort_(weight_files, weight_directory, 'weights_')
    _collect_and_sort_(esmf_unstructured, catchment_directory, 'catchments_esmf_')

    log_entry('info', 'Started merging netCDF files', rank=0)
    create_merged_weights(weight_files, esmf_unstructured, master_path)
    log_entry('info', 'Finished merging netCDF files', rank=0)


@utools_cli.command(help='Apply weights to a source variable.')
@click.option('-s', '--source', type=click.Path(exists=True), required=True,
              help='Path to source NetCDF file containing field values.')
@click.option('-n', '--name', type=str, required=True,
              help='Name of the variable in the source NetCDF file to weight.')
@click.option('-w', '--weights', type=click.Path(exists=True), required=True,
              help='Path to output weights NetCDF file.')
@click.option('-e', '--esmf_format', type=click.Path(exists=True), required=True,
              help='Path to ESMF unstructured NetCDF file.')
@click.option('-o', '--output', type=click.Path(writable=True), required=True,
              help='Path to the output file.')
def apply(source, name, weights, esmf_format, output):
    from utools.regrid.core_esmf import create_weighted_output

    log_entry('info', 'Starting weight application for "weights": {}'.format(weights), rank=0)
    create_weighted_output(esmf_format, source, weights, output, name)
    log_entry('info', 'Finished weight application for "weights": {}'.format(weights), rank=0)


if __name__ == '__main__':
    utools_cli()
