# Docker file for inferCNV
FROM ubuntu:xenial
MAINTAINER ttickle@broadinstitute.org
RUN echo "deb http://cran.rstudio.com/bin/linux/ubuntu xenial/" | tee -a /etc/apt/sources.list && \
gpg --keyserver keyserver.ubuntu.com --recv-key E084DAB9 && \
gpg -a --export E084DAB9 | apt-key add -
RUN apt-get update && \
apt-get -y install curl libssl-dev libcurl4-openssl-dev libxml2-dev r-base r-base-dev git
RUN echo "options(repos = c(CRAN = \"https://cran.rstudio.com\"))" >.Rprofile && \
echo "install.packages(c(\"devtools\",\"ape\",\"GMD\",\"RColorBrewer\",\"optparse\",\"logging\", \"gplots\"), dependencies =TRUE)" > install_devtools.r && \
echo "library(\"devtools\")" >> install_devtools.r && R --no-save < install_devtools.r

WORKDIR /
COPY ./infercnv_0.1.tar.gz /
RUN R CMD INSTALL infercnv_0.1.tar.gz

RUN apt-get update && apt-get install -y python3

# clean up installs
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN git clone https://github.com/broadinstitute/inferCNV.git
WORKDIR /inferCNV
RUN git checkout 9e1bfb9af3612eb34dac65cd6a1c3a388a4e805e
RUN chmod a+x /inferCNV/scripts/*.py
# remove extra copy of matrix_to_ideogram_annots.py from inferCNV/scripts
RUN rm /inferCNV/scripts/matrix_to_ideogram_annots.py

WORKDIR /
RUN git clone https://github.com/broadinstitute/single_cell_portal.git
WORKDIR /single_cell_portal
RUN git checkout a6ceea84fbc701289010976a0c678142ba5c8481
RUN chmod a+x /single_cell_portal/scripts/ideogram/*.py

# set path
ENV PATH=${PATH}:/inferCNV/scripts:/single_cell_portal/scripts/ideogram

# install GMD from source
WORKDIR /
RUN curl https://cran.r-project.org/src/contrib/Archive/GMD/GMD_0.3.3.tar.gz > GMD_0.3.3.tar.gz
RUN R CMD INSTALL GMD_0.3.3.tar.gz

# clean up
RUN rm /GMD_0.3.3.tar.gz
RUN rm /infercnv_0.1.tar.gz
CMD inferCNV.R --help
