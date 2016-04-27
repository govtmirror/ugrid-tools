import click

from pmesh.logging import log_pmesh

DEFAULT_NODE_THRESHOLD = 10000


@click.group()
def pmesh_cli():
    pass


@pmesh_cli.command(help='Create ESMF unstructured file for polygon ESRI Shapefile.')
@click.option('-u', '--source_uid', required=True, help='Name of unique identifier in source shapefile.')
@click.option('-s', '--source', type=click.Path(exists=True), required=True,
              help='Path to input shapefile.')
@click.option('-e', '--esmf_format', type=click.Path(writable=True), required=True,
              help='Path to the output ESMF unstructured netCDF file.')
@click.option('-n', '--node-threshold', type=int, default=DEFAULT_NODE_THRESHOLD,
              help='(default={}) Approximate limit on the number of nodes in an element part. The default node threshold provides significant performance improvement.'.format(
                  DEFAULT_NODE_THRESHOLD))
def convert(source_uid, source, esmf_format, node_threshold):
    from pmesh.prep.prep_shapefiles import convert_to_esmf_format

    log_pmesh('info', 'Started converting shapefile to ESMF format: {}'.format(source), rank=0)
    convert_to_esmf_format(esmf_format, source, source_uid, node_threshold=node_threshold)
    log_pmesh('info', 'Finished converting shapefile to ESMF format: {}'.format(source), rank=0)


@pmesh_cli.command(help='Apply weights to a source variable.')
@click.option('-s', '--source', type=click.Path(exists=True), required=True,
              help='Path to source netCDF file containing field values.')
@click.option('-n', '--name', type=str, required=True,
              help='Name of the variable in the source netCDF file to weight.')
@click.option('-w', '--weights', type=click.Path(exists=True), required=True,
              help='Path to output weights netCDF file.')
@click.option('-e', '--esmf_format', type=click.Path(exists=True), required=True,
              help='Path to ESMF unstructured netCDF file.')
@click.option('-o', '--output', type=click.Path(writable=True), required=True,
              help='Path to the output file.')
def apply(source, name, weights, esmf_format, output):
    from pmesh.regrid.core_esmf import created_weighted_output

    log_pmesh('info', 'Starting weight application for "weights": {}'.format(weights), rank=0)
    created_weighted_output(esmf_format, source, weights, output, name)
    log_pmesh('info', 'Finished weight application for "weights": {}'.format(weights), rank=0)


if __name__ == '__main__':
    pmesh_cli()
