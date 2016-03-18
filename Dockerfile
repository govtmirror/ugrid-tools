FROM continuumio/anaconda

MAINTAINER ben.koziol@noaa.gov

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get -y install build-essential \
                       gfortran
RUN apt-get clean

RUN conda update -y --all
RUN conda install -y -c nesii/channel/dev-esmf -c nesii esmpy==HEAD ocgis pytest
RUN pip install ipdb logbook
