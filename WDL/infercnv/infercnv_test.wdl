workflow infercnv {
    File expression_file
    File gene_pos_file
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
        tmp_expression_file = expression_file,
        tmp_gen_pos_file = gene_pos_file,
        tmp_output_dir = output_dir,
        diskSpace = diskSpace,
        expression_delimiter = delimiter,
        input_cluster_paths = cluster_paths,
        input_metadata_path = metadata_path,
        reference_cell_annotation = reference_cell_annotation,
        observation_cell_annotation = observation_cell_annotation
    }
    
    call run_matrix_to_ideogram_annots {
    	input:
        matrix_path = run_infercnv.observations,
        matrix_delimiter = delimiter,
        gene_positions = gene_pos_file,
        input_cluster_names = cluster_names,
        input_cluster_paths = cluster_paths,
        input_metadata_path = metadata_path,
        diskSpace = diskSpace,
        output_dir_name = output_dir
    }
}

task run_infercnv {
    File tmp_expression_file
    File tmp_gen_pos_file
    String tmp_output_dir
    String diskSpace
    String expression_delimiter
    File input_cluster_paths
    File input_metadata_path
    String reference_cell_annotation
    String observation_cell_annotation

    command <<<
    	if [ ! -d ${tmp_output_dir} ]; then
           mkdir -p ${tmp_output_dir}
        fi
        
        # Convert SCP files into inferCNV annotations file
        python3 /single_cell_portal/scripts/scp_to_infercnv.py \
            --metadata-path ${input_metadata_path} \
            --reference-cluster-path ${input_cluster_paths} \
            --reference-group-name ${reference_cell_annotation} \
            --observation-group-name ${observation_cell_annotation} \
            --output-dir ${tmp_output_dir}
            
        # Convert matrix as needed
        python3 /inferCNV/scripts/check_matrix_format.py \
        	--input_matrix ${tmp_expression_file} \
            --delimiter $'${expression_delimiter}' \
            --output_name "${tmp_output_dir}/expression.r_format.txt"
            
        # Run inferCNV
        inferCNV.R \
            --raw_counts_matrix "${tmp_output_dir}/expression.r_format.txt" \
            --annotations_file "${tmp_output_dir}/infercnv_annots_from_scp.tsv" \
            --gene_order_file ${tmp_gen_pos_file} \
            --ref_group_names "`cat ${tmp_output_dir}/infercnv_reference_cell_labels_from_scp.tsv`" \
            --cutoff 1 \
            --delim $'${expression_delimiter}' \
            --out_dir ${tmp_output_dir} \
            --cluster_by_groups \
            --denoise
        >>>
    output {
        File figure = "${tmp_output_dir}/infercnv.png"
        File observations="${tmp_output_dir}/infercnv.observations.txt"
    }

    # runtime {
    #     docker: "singlecellportal/infercnv:0-8-2-rc5"
    #     memory: "8 GB"
    #     bootDiskSizeGb: 12
    #     disks: "local-disk ${diskSpace} HDD"
    #     cpu: 8
    #     preemptible: 2
    # }
}

task run_matrix_to_ideogram_annots {
	File matrix_path
    String matrix_delimiter
    File gene_positions
    String input_cluster_names
    File input_cluster_paths
    File input_metadata_path
    String output_dir_name
    String diskSpace
    
    command <<<
        if [ ! -d ${output_dir_name} ]; then
           mkdir -p ${output_dir_name}
        fi
        python3 /single_cell_portal/scripts/ideogram/matrix_to_ideogram_annots.py \
            --matrix-path ${matrix_path} \
            --matrix-delimiter $'${matrix_delimiter}' \
            --gen-pos-file ${gene_positions} \
            --cluster-names "${sep='" "' input_cluster_names}" \
            --ref-cluster-names "`cat ${output_dir_name}/infercnv_reference_cell_labels_from_scp.tsv`" \
            --cluster-paths ${sep=' ' input_cluster_paths} \
            --metadata-path ${input_metadata_path} \
            --output-dir ${output_dir_name}
    >>>
    
	output {
    	File output_annotations = "${output_dir_name}/ideogram_exp_means.tar.gz"
    }

	# runtime {
  #       docker: "singlecellportal/infercnv:0-8-2-rc5"
  #       memory: "8 GB"
  #       bootDiskSizeGb: 12
  #       disks: "local-disk ${diskSpace} HDD"
  #       cpu: 8
  #       preemptible: 2
  #   }
}