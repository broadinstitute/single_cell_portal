# Docker file for inferCNV
FROM rocker/r-ver:3.4.4
MAINTAINER ttickle@broadinstitute.org

RUN apt-get update && \
apt-get -y install curl libssl-dev libcurl4-openssl-dev libxml2-dev git python3 zlib1g-dev
RUN echo "options(repos = c(CRAN = \"https://cran.rstudio.com\"))" >.Rprofile && \
echo "install.packages(c(\"devtools\",\"ape\",\"RColorBrewer\",\"optparse\",\"logging\", \"gplots\", \"futile.logger\", \"binhf\", \"fastcluster\", \"dplyr\", \"coin\"), dependencies = TRUE)" > install_devtools.r && \
echo "library(\"devtools\")" >> install_devtools.r && R --no-save < install_devtools.r

WORKDIR /
RUN curl -OL "https://github.com/broadinstitute/inferCNV/archive/InferCNV-v0.8.2.tar.gz"
RUN tar -xvzf InferCNV-v0.8.2.tar.gz
RUN R CMD INSTALL inferCNV-InferCNV-v0.8.2
RUN mv inferCNV-InferCNV-v0.8.2/ inferCNV

# Delete extraneous inferCNV examples (64 MB)
WORKDIR /inferCNV
RUN rm -rf examples/

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
