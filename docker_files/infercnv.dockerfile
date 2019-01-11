# Docker file for inferCNV
FROM ubuntu:xenial
MAINTAINER eweitz@broadinstitute.org
RUN echo "deb http://cran.rstudio.com/bin/linux/ubuntu xenial/" | tee -a /etc/apt/sources.list && \
gpg --keyserver keyserver.ubuntu.com --recv-key E084DAB9 && \
gpg -a --export E084DAB9 | apt-key add -
RUN apt-get update && \
apt-get -y install curl libssl-dev libcurl4-openssl-dev libxml2-dev r-base r-base-dev git python3
RUN echo "options(repos = c(CRAN = 'https://cran.rstudio.com'))" >.Rprofile && \
echo "install.packages(c('devtools','ape','RColorBrewer','optparse','logging', 'gplots', 'futile.logger', 'binhf', 'fastcluster', 'dplyr', 'coin'), dependencies = TRUE)" > install_devtools.r && \
echo "library('devtools')" >> install_devtools.r && R --no-save < install_devtools.r

WORKDIR /
RUN curl -OL "https://github.com/broadinstitute/inferCNV/archive/InferCNV-v0.8.2.tar.gz"
RUN tar -xvzf InferCNV-v0.8.2.tar.gz
RUN R CMD INSTALL inferCNV-InferCNV-v0.8.2
RUN mv inferCNV-InferCNV-v0.8.2/ inferCNV

# Delete extraneous inferCNV directories
WORKDIR /inferCNV
RUN rm -rf example/full_precision __simulations

# clean up installs
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Get script to convert inferCNV outputs to Ideogram.js annotations, then clean
WORKDIR /
RUN git clone https://github.com/broadinstitute/single_cell_portal scp
WORKDIR scp
RUN git checkout 547bed26cfa72614bd6ae7d916825e779a7a4d59
WORKDIR /
RUN mkdir -p single_cell_portal/scripts/ideogram
RUN mv scp/scripts/ideogram single_cell_portal/scripts/
RUN rm -rf scp

# set path
ENV PATH=${PATH}:/inferCNV/scripts:/single_cell_portal/scripts/ideogram

# install GMD from source
WORKDIR /
RUN curl https://cran.r-project.org/src/contrib/Archive/GMD/GMD_0.3.3.tar.gz > GMD_0.3.3.tar.gz
RUN R CMD INSTALL GMD_0.3.3.tar.gz

# clean up
RUN rm /GMD_0.3.3.tar.gz
RUN rm /InferCNV-v0.8.2.tar.gz
CMD inferCNV.R --help
