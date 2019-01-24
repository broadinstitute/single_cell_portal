# Single Cell Portal scRNA-Seq Orchestra
FROM regevlab/cellranger-2.1.1

RUN mkdir -p /software/scripts
ADD https://raw.githubusercontent.com/broadinstitute/single_cell_portal/master/scripts/orchestra_methods.py /software/scripts/orchestra_methods.py
ADD https://raw.githubusercontent.com/broadinstitute/single_cell_portal/master/scripts/monitoring/monitor_script.sh /software/scripts/monitor_script.sh

RUN chmod a+x /software/scripts/orchestra_methods.py
RUN chmod u+x /software/scripts/monitor_script.sh

ENV PATH "$PATH:/software/scripts"

RUN apt-get -y update && apt-get -y install procps