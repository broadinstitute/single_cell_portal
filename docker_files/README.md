# Docker Files

Various Docker Files

## File Mappings

File Name     	    | Use                         | Docker Hub Link                   											 | Relevant Files
------------------- | --------------------------- | ---------------------------------------------------------------------------- | ----------------------------
scRNAseq_orchestra  | Orchestra WDL Docker Image  | [Docker Hub](https://hub.docker.com/r/singlecellportal/scrna-seq_orchestra/) | [orchestra_methods.py](https://github.com/broadinstitute/single_cell_portal/blob/master/scripts/orchestra_methods.py)
cell-ranger-count-2.0.2 | Cellranger Count Docker Image | [Docker Hub](https://hub.docker.com/r/singlecellportal/cell-ranger-count-2.0.2/) | [SortSparseMatrix.py](https://github.com/broadinstitute/single_cell_portal/blob/master/scripts/SortSparseMatrix.py), [cell_ranger_to_scp.py](https://github.com/broadinstitute/single_cell_portal/blob/master/scripts/cell_ranger_to_scp.py) 
inferCNV-alpha  | inferCNV (alpha) Docker Image | [Docker Hub](https://hub.docker.com/r/singlecellportal/infercnv/) | [cluster_groups.py](https://github.com/broadinstitute/single_cell_portal/blob/master/scripts/ideogram/cluster_groups.py), [matrix_to_ideogram_annots.py](https://github.com/broadinstitute/single_cell_portal/blob/master/scripts/ideogram/matrix_to_ideogram_annots.py),[infercnv_0.1.tar.gz](https://github.com/broadinstitute/single_cell_portal/blob/master/docker_files/infercnv_0.1.tar.gz)

