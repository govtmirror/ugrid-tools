import os

import click

from utools.logging import log_entry

DEFAULT_NODE_THRESHOLD = 10000


@click.group()
def fmtools_cli():
    pass


@fmtools_cli.command(help='Create ESMF unstructured NetCDF files from polygon ESRI Shapefiles.')
@click.option('-u', '--source_uid', required=True, help='Name of unique identifier in source shapefile.')
@click.option('-s', '--source', type=click.Path(exists=True), required=True,
              help='Path to input shapefile.')
@click.option('-e', '--esmf_format', type=click.Path(writable=True), required=True,
              help='Path to the output ESMF unstructured NetCDF file.')
@click.option('-n', '--node-threshold', type=int, default=DEFAULT_NODE_THRESHOLD,
              help='(default={}) Approximate limit on the number of nodes in an element part. The default node '
                   'threshold provides significant performance improvement.'.format(DEFAULT_NODE_THRESHOLD))
def convert(source_uid, source, esmf_format, node_threshold):
    from utools.prep.prep_shapefiles import convert_to_esmf_format

    log_entry('info', 'Started converting shapefile to ESMF format: {}'.format(source), rank=0)
    convert_to_esmf_format(esmf_format, source, source_uid, node_threshold=node_threshold)
    log_entry('info', 'Finished converting shapefile to ESMF format: {}'.format(source), rank=0)


@fmtools_cli.command(help='Create a merged ESMF weights file.')
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


@fmtools_cli.command(help='Apply weights to a source variable.')
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
    from utools.regrid.core_esmf import created_weighted_output

    log_entry('info', 'Starting weight application for "weights": {}'.format(weights), rank=0)
    created_weighted_output(esmf_format, source, weights, output, name)
    log_entry('info', 'Finished weight application for "weights": {}'.format(weights), rank=0)


if __name__ == '__main__':
    fmtools_cli()
