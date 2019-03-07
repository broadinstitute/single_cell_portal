# Docker file for inferCNV
FROM r-base:3.5.2
MAINTAINER eweitz@broadinstitute.org
RUN apt-get update && \
apt-get -y install curl libssl-dev libcurl4-openssl-dev libxml2-dev git python3
RUN echo "options(repos = c(CRAN = 'https://cran.rstudio.com'))" >.Rprofile && \
echo "install.packages(c('devtools','ape','RColorBrewer','optparse','logging', 'gplots', 'futile.logger', 'binhf', 'fastcluster', 'dplyr', 'coin', 'rmarkdown', 'doParallel', 'future'), dependencies = TRUE)" > install_devtools.r && \
echo "install.packages('BiocManager')" >> install_devtools.r && \
echo "BiocManager::install('SingleCellExperiment', version = '3.8')" >> install_devtools.r && \
echo "BiocManager::install('BiocStyle', version = '3.8')" >> install_devtools.r && \
echo "BiocManager::install('edgeR', version = '3.8')" >> install_devtools.r && \
echo "install.packages(c('HiddenMarkov', 'fitdistrplus', 'fastcluster', 'Matrix', 'stats', 'gplots', 'utils', 'methods', 'knitr', 'testthat'), dependencies = TRUE)" >> install_devtools.r && \
echo "library('devtools')" >> install_devtools.r && R --no-save < install_devtools.r

RUN mkdir /workflow

WORKDIR /
# RUN curl -OL "https://github.com/broadinstitute/inferCNV/archive/InferCNV-v0.8.2.tar.gz"
# RUN tar -xvzf InferCNV-v0.8.2.tar.gz
# RUN R CMD INSTALL inferCNV-InferCNV-v0.8.2
# RUN mv inferCNV-InferCNV-v0.8.2/ inferCNV
# Get script to convert inferCNV outputs to Ideogram.js annotations, then clean
WORKDIR /
RUN rm -rf infercnv
RUN git clone https://github.com/broadinstitute/inferCNV
WORKDIR inferCNV
RUN git checkout update-cli-example
# Checkout code as of 2019-03-01
RUN git checkout 33b72be4ce88a21dde35d89997ec833e7b029269
RUN R CMD INSTALL .

# Delete extraneous inferCNV directories
WORKDIR /inferCNV
RUN rm -rf example/full_precision __simulations .git

# Install Java
RUN apt-get install -y openjdk-8-jdk

# clean up installs
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Get script to convert inferCNV outputs to Ideogram.js annotations, then clean
RUN echo "Clearing Docker cache (2)"
WORKDIR /
RUN git clone https://github.com/broadinstitute/single_cell_portal scp
WORKDIR scp
RUN git checkout ew-infercnv-beta
# Checkout code as of 2019-03-07
RUN git checkout 7c16d2cc47ef1ade0965f904992b08f0b10de0a4
WORKDIR /
RUN mkdir -p single_cell_portal/scripts
RUN mv scp/scripts/ideogram single_cell_portal/scripts/
RUN mv scp/scripts/scp_to_infercnv.py single_cell_portal/scripts/
RUN mv scp/WDL/infercnv/* /workflow/
RUN rm -rf scp

# set path
ENV PATH=${PATH}:/inferCNV/scripts:/single_cell_portal/scripts

# install GMD from source
WORKDIR /
RUN curl https://cran.r-project.org/src/contrib/Archive/GMD/GMD_0.3.3.tar.gz > GMD_0.3.3.tar.gz
RUN R CMD INSTALL GMD_0.3.3.tar.gz

# Finish setting up workflow test scaffolding
WORKDIR /workflow
ADD https://github.com/broadinstitute/cromwell/releases/download/36.1/cromwell-36.1.jar .
RUN cp -p /inferCNV/example/oligodendroglioma_expression_downsampled.counts.matrix test_data/

# clean up
RUN rm /GMD_0.3.3.tar.gz
#RUN rm /InferCNV-v0.8.2.tar.gz
CMD inferCNV.R --help
