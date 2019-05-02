# Docker file for inferCNV
FROM bioconductor/devel_base2

LABEL org.label-schema.license="BSD-3-Clause" \
      org.label-schema.vendor="Broad Institute" \
      maintainer="Eric Weitz <eweitz@broadinstitute.org>"

RUN apt-get update && apt-get -y install curl libssl-dev libcurl4-openssl-dev \
                                        libxml2-dev git python3 jags \
                                        r-cran-rjags && \
                      apt-get clean && rm -rf /var/tmp/* \
                                          /tmp/* /var/lib/apt/lists/*

# Install R and Bioconductor packages
RUN echo "options(repos = c(CRAN = 'https://cran.rstudio.com'))" >.Rprofile
RUN R -e "install.packages(c('devtools','KernSmooth', 'lattice', 'Matrix', \
                             'survival', 'MASS', 'TH.data', 'nlme', 'ape', \
                             'fitdistrplus', 'multcomp', 'coin', 'binhf', \
                             'caTools', 'coda', 'dplyr', 'doparallel', \
                             'fastcluster', 'foreach', 'futile.logger', \
                             'future', 'gplots', 'ggplot2', 'HiddenMarkov', \
                             'reshape', 'rjags', 'RColorBrew', 'doParallel', \
                             'tidyr', 'gridExtra', 'argparse', 'knitr', \
                             'rmarkdown', 'testthat', 'optparse', 'logging', \
                             'data.table'), repos = 'http://cran.us.r-project.org')"
RUN R -e "BiocManager::install(c('BiocGenerics', 'edgeR', 'SingleCellExperiment', \
            'SummarizedExperiment', 'BiocStyle', 'BiocCheck'), version = \"3.9\")"


# Checkout inferCNV code as of 2019-05-01, and install it
RUN git clone https://github.com/broadinstitute/inferCNV && cd inferCNV && \
      git checkout experimental && git checkout e80ae2b893468b50735e51b4543611c4507927bd && \
      R CMD INSTALL . && rm -rf example/full_precision __simulations .git
# TODO: Extract everything above here into inferCNV base image.

# update single_cell_portal checkout to 2019-05-01 commit 
# Get scripts to pre-process SCP files content to inferCNV input formal
# and post-process to convert inferCNV outputs to Ideogram.js annotations, then clean up
WORKDIR /
RUN git clone https://github.com/broadinstitute/single_cell_portal scp && cd scp && \
      git checkout jlc_infercnv && git checkout 2950174e71b281417b07181a8a4af9251207fc5d
RUN mkdir -p single_cell_portal/scripts && mv scp/scripts/ideogram single_cell_portal/scripts/ && \
      mv scp/scripts/scp_to_infercnv.py single_cell_portal/scripts/ && rm -rf scp

# set path
ENV PATH=${PATH}:/inferCNV/scripts:/single_cell_portal/scripts

WORKDIR /
CMD inferCNV.R --help