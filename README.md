[![Build Status](https://travis-ci.org/NESII/ugrid-tools.svg?branch=next)](https://travis-ci.org/NESII/ugrid-tools)

Provides set of command line Python tools for manipulating unstructured grid (flexible meshes) data files and associated derivative products.

# Convert Geometry Files to ESMF Unstructured Files

```
Usage: utools_cli convert [OPTIONS]

  Create ESMF unstructured NetCDF files from supported geometry containers
  (ESRI Shapefile, ESRI File Geodatabase).

Options:
  -u, --source_uid TEXT         Name of unique identifier in source geometry
                                container.  [required]
  -s, --source PATH             Path to input geometry container.  [required]
  -e, --esmf_format PATH        Path to the output ESMF unstructured NetCDF
                                file.  [required]
  --feature-class TEXT          Feature class name in source ESRI File
                                Geodatabase. Required when converting file
                                geodatabases.
  --config-path PATH            Path to configuration file containing
                                arguments difficult to format in terminals
                                (CRS WKT). Required for CRS conversions.
  --dest_crs_index TEXT         The key name with optional section for pulling
                                the CRS WKT from file. No spaces in option
                                and/or section names. With a section:
                                "section,option". Without a section: "option".
                                See http://bit.ly/2bgKMU9 for example format.
  -n, --node-threshold INTEGER  (default=5000) Approximate limit on the number
                                of nodes in an element part. The default node
                                threshold provides significant performance
                                improvement.
  --debug / --no-debug          If "--debug", execute in debug mode converting
                                only the first record of the geometry
                                container.
  --help                        Show this message and exit.
```

# Apply Weights From File

```
Usage: utools_cli apply [OPTIONS]

  Apply weights to a source variable.

Options:
  -s, --source PATH       Path to source NetCDF file containing field values.
                          [required]
  -n, --name TEXT         Name of the variable in the source NetCDF file to
                          weight.  [required]
  -w, --weights PATH      Path to output weights NetCDF file.  [required]
  -e, --esmf_format PATH  Path to ESMF unstructured NetCDF file.  [required]
  -o, --output PATH       Path to the output file.  [required]
  --help                  Show this message and exit.
```

# Merge Weight Files

```
$ utools_cli merge --help
Usage: utools_cli merge [OPTIONS]

  Create a merged ESMF weights file.

Options:
  -c, --catchment-directory TEXT  Path to the directory containing the ESMF
                                  unstructured files.  [required]
  -w, --weight-directory PATH     Path to the directory containing the weights
                                  files.  [required]
  -m, --master-path PATH          Path to the output merged weight file.
                                  [required]
  --help                          Show this message and exit.
```
