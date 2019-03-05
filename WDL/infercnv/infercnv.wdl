workflow infercnv {
    File matrix_path
    File gene_pos_path
    File metadata_path
    String output_dir
    String diskSpace
    String delimiter
    String cluster_names
    File cluster_paths
    String reference_cell_annotation
    String observation_cell_annotation
    
    call run_infercnv {
    	input:
        matrix_path = matrix_path,
        gene_pos_path = gene_pos_path,
        output_dir = output_dir,
        diskSpace = diskSpace,
        delimiter = delimiter,
        cluster_paths = cluster_paths,
        metadata_path = metadata_path,
        reference_cell_annotation = reference_cell_annotation,
        observation_cell_annotation = observation_cell_annotation
    }
    
    call run_matrix_to_ideogram_annots {
    	input:
        matrix_path = run_infercnv.observations,
        delimiter = delimiter,
        gene_pos_path = gene_pos_path,
        cluster_names = cluster_names,
        cluster_paths = cluster_paths,
        metadata_path = metadata_path,
        diskSpace = diskSpace,
        output_dir = output_dir
    }
}

task run_infercnv {
    File matrix_path
    File gene_pos_path
    String output_dir
    String diskSpace
    String delimiter
    File cluster_paths
    File metadata_path
    String reference_cell_annotation
    String observation_cell_annotation

    command <<<
        if [ ! -d ${output_dir} ]; then
            mkdir -p ${output_dir}
        fi
        
        # Convert SCP files into inferCNV annotations file
        python3 /single_cell_portal/scripts/scp_to_infercnv.py \
            --metadata-path ${metadata_path} \
            --reference-cluster-path ${cluster_paths} \
            --reference-group-name ${reference_cell_annotation} \
            --observation-group-name ${observation_cell_annotation} \
            --output-dir ${output_dir}
            
        # Convert matrix as needed
        python3 /inferCNV/scripts/check_matrix_format.py \
            --input_matrix ${matrix_path} \
            --delimiter $'${delimiter}' \
            --output_name "${output_dir}/expression.r_format.txt"
            
        # Run inferCNV
        inferCNV.R \
            --raw_counts_matrix "${output_dir}/expression.r_format.txt" \
            --annotations_file "${output_dir}/infercnv_annots_from_scp.tsv" \
            --gene_order_file ${gene_pos_path} \
            --ref_group_names "`cat ${output_dir}/infercnv_reference_cell_labels_from_scp.tsv`" \
            --cutoff 1 \
            --delim $'${delimiter}' \
            --out_dir ${output_dir} \
            --cluster_by_groups \
            --denoise
        >>>
    output {
        File figure = "${output_dir}/infercnv.png"
        File observations="${output_dir}/infercnv.observations.txt"
    }

    runtime {
        docker: "singlecellportal/infercnv:0-8-2-rc6"
        memory: "8 GB"
        bootDiskSizeGb: 12
        disks: "local-disk ${diskSpace} HDD"
        cpu: 8
        preemptible: 2
    }
}

task run_matrix_to_ideogram_annots {
	  File matrix_path
    String delimiter
    File gene_pos_path
    String cluster_names
    File cluster_paths
    File metadata_path
    String output_dir
    String diskSpace
    
    command <<<
        if [ ! -d ${output_dir} ]; then
           mkdir -p ${output_dir}
        fi

        # Convert processed matrix output from inferCNV to summary Ideogram.js annotations
        python3 /single_cell_portal/scripts/ideogram/matrix_to_ideogram_annots.py \
            --matrix-path ${matrix_path} \
            --matrix-delimiter $'${delimiter}' \
            --gen-pos-file ${gene_pos_path} \
            --cluster-names "${sep='" "' cluster_names}" \
            --ref-cluster-names "`cat ${output_dir}/infercnv_reference_cell_labels_from_scp.tsv`" \
            --cluster-paths ${sep=' ' cluster_paths} \
            --metadata-path ${metadata_path} \
            --output-dir ${output_dir}
    >>>
    
	output {
    File output_annotations = "${output_dir}/ideogram_exp_means.tar.gz"
  }

	runtime {
        docker: "singlecellportal/infercnv:0-8-2-rc6"
        memory: "8 GB"
        bootDiskSizeGb: 12
        disks: "local-disk ${diskSpace} HDD"
        cpu: 8
        preemptible: 2
    }
}