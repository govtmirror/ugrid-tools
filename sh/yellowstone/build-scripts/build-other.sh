#!/usr/bin/env bash


module load python/2.7.7 numpy/1.10.1 netcdf4python/1.2.1 shapely/1.5.1 gdal cython/0.23.4

export PYTHONPATH=${PYTHONPATH}:/glade/u/home/benkoz/src/click/build/lib:/glade/u/home/benkoz/src/logbook/build/lib:/glade/u/home/benkoz/src/click-plugins/build/lib:/glade/u/home/benkoz/src/Fiona/build/lib.linux-x86_64-2.7
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/glade/apps/opt/gdal/1.10.0/intel/default/lib:/glade/apps/opt/netcdf/4.3.0/intel/12.1.5/lib:/glade/apps/opt/hdf5/1.8.9/intel/12.1.4/lib

cd ~/src
git clone https://github.com/pallets/click.git
cd click
git checkout 6.3
python setup.py build

cd ~/src
git clone https://github.com/click-contrib/click-plugins.git
cd click-plugins
python setup.py build

cd ~/src
git clone https://github.com/Toblerity/Fiona.git
cd Fiona
git checkout 1.6.3
export GDAL_CONFIG=/glade/apps/opt/gdal/1.10.0/intel/12.1.5/bin/gdal-config
python setup.py build
#$PYTHON setup.py build_ext -I$PREFIX/include -L$PREFIX/lib -lgdal install --single-version-externally-managed --record record.txt
