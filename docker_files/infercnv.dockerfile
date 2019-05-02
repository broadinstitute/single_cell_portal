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
# note: installing Java openjdk-8-jdk, needed for Cromwell

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


# Checkout and install inferCNV
# update to 2019-04-26 commit (Fix observations heatmap chromosome labels)
RUN git clone https://github.com/broadinstitute/inferCNV && cd inferCNV && \
      git checkout master && git checkout 60c7edc5590ad74b4f8354b4426cff496fc74c99 && \
      R CMD INSTALL . && rm -rf example/full_precision __simulations .git
# Delete extraneous inferCNV directories

# Set up workflow test directory
WORKDIR /workflow

# update to 2019-04-17 commit (note num_threads fix but prepare_sparsematrix.R still broken)
# Get script to convert inferCNV outputs to Ideogram.js annotations, then clean up
WORKDIR /
RUN git clone https://github.com/broadinstitute/single_cell_portal scp && cd scp && \
      git checkout ew-refine-infercnv && git checkout 82fd214e93f8c3d761164ad7b6f4290055348bb8
RUN mkdir -p single_cell_portal/scripts && mv scp/scripts/ideogram single_cell_portal/scripts/ && \
      mv scp/scripts/scp_to_infercnv.py single_cell_portal/scripts/ && mv scp/WDL/infercnv/* workflow/ \
      && rm -rf scp
RUN curl -SLo - https://github.com/broadinstitute/infercnv/raw/master/inst/extdata/oligodendroglioma_expression_downsampled.counts.matrix.gz | gunzip > workflow/test_data/oligodendroglioma_expression_downsampled.counts.matrix

# set path
ENV PATH=${PATH}:/inferCNV/scripts:/single_cell_portal/scripts

WORKDIR /
CMD inferCNV.R --help