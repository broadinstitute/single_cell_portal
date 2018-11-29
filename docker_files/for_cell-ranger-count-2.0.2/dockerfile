# Single Cell Portal Cell Ranger Count (2.0.2)
FROM regevlab/cellranger-2.0.2

RUN mkdir /software/scripts
ADD https://raw.githubusercontent.com/broadinstitute/single_cell_portal/master/scripts/cell_ranger_to_scp.py /software/scripts/cell_ranger_to_scp.py
ADD https://raw.githubusercontent.com/broadinstitute/single_cell_portal/master/scripts/SortSparseMatrix.py /software/scripts/SortSparseMatrix.py

RUN pip install pandas

ENV PATH "$PATH:/software/scripts"

RUN chmod -R a+x /software/scripts