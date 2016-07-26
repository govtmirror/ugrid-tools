FROM continuumio/anaconda

MAINTAINER ben.koziol@noaa.gov

ENV GDAL_DATA /opt/conda/share/gdal

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get -y install build-essential \
                       gfortran \
                       tree
RUN apt-get clean

RUN conda update -y --all
RUN conda install -y -c nesii/channel/dev-esmf -c nesii esmpy==HEAD ocgis nose setuptools click
RUN conda remove -y ocgis
RUN pip install ipdb logbook addict
RUN mkdir -p /tmp/deps && cd /tmp/deps
RUN git clone -b pmesh-ugrid-nfie https://github.com/NCPP/ocgis.git && cd ocgis && python setup.py install
RUN rm -r /tmp/deps

#COPY . /tmp/utools
#RUN cd /opt && git clone -b next /tmp/utools
#RUN rm -r /tmp/utools
RUN cd /opt && git clone -b master https://github.com/NESII/ugrid-tools.git
RUN cd /opt/fm-tools && bash test.sh
RUN python setup.py install
RUN utools_cli --help