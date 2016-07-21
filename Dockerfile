FROM continuumio/anaconda

MAINTAINER ben.koziol@noaa.gov

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get -y install build-essential \
                       gfortran \
                       tree
RUN apt-get clean

RUN conda update -y --all
RUN conda install -y -c nesii/channel/dev-esmf -c nesii esmpy==HEAD ocgis nose
RUN conda remove -y ocgis
RUN pip install ipdb logbook addict
RUN git clone -b pmesh-ugrid-nfie https://github.com/NCPP/ocgis.git && cd ocgis && python setup.py install
RUN git clone -b flexible-mesh https://github.com/NESII/pyugrid.git && cd pyugrid && python setup.py install

COPY . /tmp/fmtools
RUN cd /opt && git clone -b next /tmp/fmtools
RUN rm -r /tmp/fmtools

RUN cd /opt/fmtools && bash test.sh
