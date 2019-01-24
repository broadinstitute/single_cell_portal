workflow infercnv {
    File expression_file
    File gene_pos_file
    File metadata_path
    String output_dir
    String diskSpace
    String delimiter
    Array[String] cluster_names
    Array[File] cluster_paths
    
    call run_infercnv {
    	input:
        tmp_expression_file = expression_file,
        tmp_gen_pos_file = gene_pos_file,
        tmp_output_dir = output_dir,
        diskSpace = diskSpace,
        expression_delimiter = delimiter
    }
    
    call run_matrix_to_ideogram_annots {
    	input:
        matrix_path = run_infercnv.pre_expression,
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

    command <<<
    	if [ ! -d ${tmp_output_dir} ]; then
           mkdir -p ${tmp_output_dir}
        fi
        python3 /inferCNV/scripts/check_matrix_format.py \
        	--input_matrix ${tmp_expression_file} \
            --delimiter $'${expression_delimiter}' \
            --output_name "${tmp_output_dir}/expression.r_format.txt"
        inferCNV.R \
            --cutoff 4.5 \
            --delim $'${expression_delimiter}' \
            --log "${tmp_output_dir}/infercnv.log" \
            --noise_filter 0.3 \
            --output_dir ${tmp_output_dir} \
            --window 101 \
            ${tmp_output_dir}/expression.r_format.txt ${tmp_gen_pos_file}
        >>>
    output {
        File log = "${tmp_output_dir}/infercnv.log"
        File figure = "${tmp_output_dir}.infercnv.pdf"
        File post_expression ="${tmp_output_dir}_expression_post_viz_transform.txt"
        File pre_expression="${tmp_output_dir}/expression_pre_vis_transform.txt"
        File observations="${tmp_output_dir}/observations.txt"
    }

    runtime {
        docker: "singlecellportal/infercnv:0.8.2-rc1"
        memory: "8 GB"
        bootDiskSizeGb: 12
        disks: "local-disk ${diskSpace} HDD"
        cpu: 8
        preemptible: 2
    }
}

task run_matrix_to_ideogram_annots {
    File matrix_path
    String matrix_delimiter
    File gene_positions
    Array[String] input_cluster_names
    Array[File] input_cluster_paths
    File input_metadata_path
    String output_dir_name
    String diskSpace
    
    command <<<
        if [ ! -d ${output_dir_name} ]; then
           mkdir -p ${output_dir_name}
        fi
        python3 /single_cell_portal/scripts/ideogram/matrix_to_ideogram_annots.py \
            --matrix_path ${matrix_path} \
            --matrix_delimiter $'${matrix_delimiter}' \
            --gen_pos_file ${gene_positions} \
            --cluster_names "${sep='" "' input_cluster_names}" \
            --cluster_paths ${sep=' ' input_cluster_paths} \
            --metadata_path ${input_metadata_path} \
            --output_dir ${output_dir_name}
    >>>
    
	output {
    	File output_annotations = "${output_dir_name}/ideogram_exp_means.tar.gz"
    }

	runtime {
        docker: "singlecellportal/infercnv:0.8.2-rc1"
        memory: "8 GB"
        bootDiskSizeGb: 12
        disks: "local-disk ${diskSpace} HDD"
        cpu: 8
        preemptible: 2
    }
}