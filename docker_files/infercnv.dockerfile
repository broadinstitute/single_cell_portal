# Docker file for inferCNV
FROM bioconductor/devel_base2

LABEL org.label-schema.license="BSD-3-Clause" \
      org.label-schema.vendor="Broad Institute" \
      maintainer="Eric Weitz <eweitz@broadinstitute.org>"

RUN apt-get update
RUN apt-get -y install curl libssl-dev libcurl4-openssl-dev libxml2-dev git python3 jags
RUN echo "options(repos = c(CRAN = 'https://cran.rstudio.com'))" >.Rprofile
RUN apt-get install -y r-cran-rjags
RUN R -e "install.packages('devtools', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('KernSmooth', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('lattice', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('Matrix', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('survival', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('MASS', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('TH.data', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('nlme', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('ape', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('fitdistrplus', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('multcomp', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('coin', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('binhf', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('caTools', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('coda', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('dplyr', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('doparallel', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('fastcluster', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('foreach', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('futile.logger', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('future', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('gplots', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('ggplot2', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('HiddenMarkov', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('reshape', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('rjags', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('RColorBrew', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('doParallel', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('tidyr', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('gridExtra', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('argparse', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('knitr', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('rmarkdown', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('testthat', repos = 'http://cran.us.r-project.org')"
RUN R -e "BiocManager::install(c('BiocGenerics', 'edgeR', 'SingleCellExperiment', 'SummarizedExperiment', 'BiocStyle', 'BiocCheck'), version = \"3.9\")"


RUN R -e "install.packages('optparse', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('logging', repos = 'http://cran.us.r-project.org')"

# Install Java, needed for Cromwell
# RUN apt-get install -y openjdk-8-jdk # Comment out for production build

RUN mkdir /workflow

WORKDIR /
# RUN echo "Clear Docker cache (3)"
# RUN curl -OL "https://github.com/broadinstitute/infercnv/archive/InferCNV-v0.99.0.tar.gz"
# RUN tar -xvzf InferCNV-v0.99.0.tar.gz
# RUN R CMD INSTALL infercnv-InferCNV-v0.99.0
# RUN mv infercnv-InferCNV-v0.99.0/ inferCNV

RUN echo "Clear Docker cache (6)"
RUN git clone https://github.com/broadinstitute/inferCNV
WORKDIR inferCNV
RUN git checkout master
# Checkout code as of 2019-04-17
RUN git checkout 2498bb8f2dddb84bf3b935bf7de1f926b598f490
RUN R CMD INSTALL .

# Delete extraneous inferCNV directories
WORKDIR /inferCNV
RUN rm -rf example/full_precision __simulations .git

# clean up installs
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Get script to convert inferCNV outputs to Ideogram.js annotations, then clean
RUN echo "Clearing Docker cache (3)"
WORKDIR /
RUN git clone https://github.com/broadinstitute/single_cell_portal scp
WORKDIR scp
RUN git checkout ew-refine-infercnv
# Checkout code as of 2019-03-26
RUN git checkout 443843ef95497d2474afbdbfd792e96246eac562
WORKDIR /
RUN mkdir -p single_cell_portal/scripts
RUN mv scp/scripts/ideogram single_cell_portal/scripts/
RUN mv scp/scripts/scp_to_infercnv.py single_cell_portal/scripts/
RUN mv scp/WDL/infercnv/* /workflow/
RUN rm -rf scp

# set path
ENV PATH=${PATH}:/inferCNV/scripts:/single_cell_portal/scripts

# Finish setting up workflow test scaffolding
WORKDIR /workflow
ADD https://github.com/broadinstitute/cromwell/releases/download/39/cromwell-39.jar .
RUN cp -p /inferCNV/example/oligodendroglioma_expression_downsampled.counts.matrix test_data/

WORKDIR /

#RUN rm /InferCNV-v0.8.2.tar.gz
CMD inferCNV.R --help

RUN R -e "install.packages('data.table', repos = 'http://cran.us.r-project.org')"