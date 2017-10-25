#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import csv
import os
import PortalFiles


def check_cell_names(expression_files=None,
                     coordinates_file_group=None,
                     metadata_file=None):
    """
    Check files among themselves.
    """
    if metadata_file:
        if coordinates_file_group:
            for coordinates_file in coordinates_file_group:
                metadata_file.compare_cell_names(coordinates_file)
        if expression_files:
            for exp_file in expression_files:
                metadata_file.compare_cell_names(exp_file)
    if coordinates_file_group:
        if expression_files:
            for coordinates_file in coordinates_file_group:
                for exp_file in expression_files:
                    coordinates_file.compare_cell_names(exp_file)

def check_gene_names(expression_files=None,
                     gene_files=None):
    """
    Check gene names among files.
    """

    if gene_files and expression_files:
        for gene_list in gene_files:
            for exp_file in expression_files:
                if gene_list and exp_file:
                    print(" ".join(["Comparing gene names in",
                                    gene_list.file_name,
                                    "with the expression file:",
                                    exp_file.file_name]))
                    gene_list.compare_gene_names(exp_file)

prsr_arguments = argparse.ArgumentParser(
    prog="verify_portal_file.py",
    description="Verify files for the single cell portal",
    conflict_handler="resolve",
    formatter_class=argparse.HelpFormatter)

prsr_arguments.add_argument("--coordinates_file",
                            default=None,
                            dest="coordinates_file_group",
                            type=str,
                            nargs="*",
                            help="".join(["The file that holds the ",
                                          "coordinates for the main ",
                                          "visualization."]))

prsr_arguments.add_argument("--expression_files",
                            default=None,
                            dest="expression_file",
                            type=str,
                            nargs="*",
                            help="".join(["The file that holds the ",
                                          "expression data."]))

prsr_arguments.add_argument("--delimiter",
                            default="\t",
                            dest="file_delimiter",
                            type=str,
                            help="".join(["File delimiter for files.."]))

prsr_arguments.add_argument("--deid_cells",
                            default=False,
                            action="store_true",
                            dest="do_deidentify_cell",
                            help="".join(["Change cell ids in file to a ",
                                          "random name, keeping cell names ",
                                          "consistent between files"]))

prsr_arguments.add_argument("--coordinates_file",
                            default=None,
                            dest="coordinates_file_group",
                            type=str,
                            nargs="*",
                            help="".join(["The file that holds the ",
                                          "coordinates for the main ",
                                          "visualization."]))

prsr_arguments.add_argument("--gene_list",
                            default=None,
                            dest="gene_list_group",
                            type=str,
                            nargs="*",
                            help="".join(["Lists of genes and measurement ",
                                          "for each gene within a cluster of cells."]))

prsr_arguments.add_argument("--metadata_file",
                            default=None,
                            dest="metadata_file",
                            type=str,
                            help="".join(["The file that holds the ",
                                          "metadata_file data."]))

prsr_arguments.add_argument("--subsample",
                            default=None,
                            dest="subsample",
                            type=int,
                            help="The total number of cells to subsample.")

prsr_arguments.add_argument("--sampling_metadata",
                            default=None,
                            dest="subsample_metadata",
                            type=str,
                            help="The metadata to use to sample within, currently only supporting factors not numeric metadata.")

prsr_arguments.add_argument("--subsample_cells_list",
                            default=None,
                            dest="subsample_list",
                            type=str,
                            help="A list of cell names to keep when subsampling. Allows one to specifically indicate which cells to subsample to. This take precident over random sampling; if this is specified no random sampling can occur.")

prsr_arguments.add_argument("--no_checking",
                            default=True,
                            dest="check_files",
                            action="store_false",
                            help="Turn off checking of files.")

prsr_arguments.add_argument("--add_gene_keyword",
                            default=False,
                            dest="add_expression_header_keyword",
                            action="store_true",
                            help="Adds the keyword in the 0,0 element of expression matrices to a copy of the expression matrices and then exists.")

prs_args = prsr_arguments.parse_args()


# Holds the file objects a opposed to the file names
coordinates_files = []
metadata_portal_file = None
expression_portal_files = []
gene_list_files = []

if prs_args.coordinates_file_group:
    for coordinates_file in prs_args.coordinates_file_group:
        coordinates_portal_file = PortalFiles.CoordinatesFile(coordinates_file,
                                              file_delimiter=prs_args.file_delimiter,
                                              expected_header=PortalFiles.c_COORDINATES_HEADER)
        if prs_args.check_files:
            coordinates_portal_file.check()
        coordinates_files.append(coordinates_portal_file)

if prs_args.metadata_file:
    metadata_portal_file = PortalFiles.MetadataFile(prs_args.metadata_file,
                                      file_delimiter=prs_args.file_delimiter)
    if prs_args.check_files:
        metadata_portal_file.check()

if prs_args.expression_file:
    for expression_file in prs_args.expression_file:
        expression_portal_file = PortalFiles.ExpressionFile(expression_file,
                                            file_delimiter=prs_args.file_delimiter)

        if prs_args.add_expression_header_keyword:
            expression_portal_file.add_expression_header_keyword()
        else:
            if prs_args.check_files:
                expression_portal_file.check()
            expression_portal_files.append(expression_portal_file)
    if prs_args.add_expression_header_keyword:
        exit(0)

if prs_args.gene_list_group:
    for gene_list in prs_args.gene_list_group:
        gene_list_file = PortalFiles.GeneListFile(gene_list,
                                                  file_delimiter=prs_args.file_delimiter)
        if prs_args.check_files:
            gene_list_file.check()
        gene_list_files.append(gene_list_file)

if prs_args.check_files:
    check_cell_names(expression_files=expression_portal_files,
                     coordinates_file_group=coordinates_files,
                     metadata_file=metadata_portal_file)

    check_gene_names(expression_files=expression_portal_files,
                     gene_files=gene_list_files)

# Subsample based on metadatum
if not prs_args.subsample is None or not prs_args.subsample_metadata is None or not prs_args.subsample_list is None:
    if (prs_args.subsample is None or prs_args.subsample_metadata is None) and prs_args.subsample_list is None:
        print("".join(["In order to subsample please provide both an amount",
                       "to subsample and a metadata to use in subsampling"]))
    else:
        print("Starting subsampling.")
        sampled_expression_files = []
        sampled_coordinates_files = []

        print("Sampling cells.")
        sampled_cells = []
        if not prs_args.subsample_list is None:
            with open(prs_args.subsample_list,'r') as gene_name_reader:
                for line in csv.reader(gene_name_reader,delimiter=prs_args.file_delimiter):
                    sampled_cells.extend(line)
        else:
            sampled_cells = metadata_portal_file.select_subsample_cells(prs_args.subsample,prs_args.subsample_metadata)
            with open(metadata_portal_file.create_safe_file_name("sampled_cells.txt"),'wb') as write_sampled_cells:
                csv.writer(write_sampled_cells).writerows([[cell] for cell in sampled_cells])
        if len(sampled_cells) < 1:
            print("No sampling occured.")
        else:
            print("Subsampling metadata file.")
            if prs_args.metadata_file:
                metadata_portal_file_name = metadata_portal_file.subset_cells(sampled_cells)
                metadata_portal_file = PortalFiles.MetadataFile(metadata_portal_file_name,
                                              file_delimiter=prs_args.file_delimiter)
            for expression_file in expression_portal_files:
                print("Subsampling expression matrix: "+expression_file.file_name)
                sampled_expression_file = expression_file.subset_cells(sampled_cells)
                expression_sample_file = PortalFiles.ExpressionFile(sampled_expression_file,
                                                    file_delimiter=prs_args.file_delimiter)
                sampled_expression_files.append(expression_sample_file)
            for cluster in coordinates_files:
                print("Subsampling cluster file: "+ cluster.file_name)
                sampled_coordinate_file = cluster.subset_cells(sampled_cells)
                coordinates_portal_file = PortalFiles.CoordinatesFile(sampled_coordinate_file,
                                                      file_delimiter=prs_args.file_delimiter,
                                                      expected_header=PortalFiles.c_COORDINATES_HEADER)
                sampled_coordinates_files.append(coordinates_portal_file)

            expression_portal_files = sampled_expression_files
            coordinates_files = sampled_coordinates_files
            print("Subsampling complete without error.")

# Deidentify all cell names (optionally) after all QC checks are made.
if prs_args.do_deidentify_cell:
    print("Deidentifying Cell Names/Ids")

    deid_coordinates_files = []
    deid_metadata_portal_file = None
    deid_expression_portal_files = []

    # Holds the deidentified cell names if used
    deid_names = {}

    if coordinates_files:
        for coordinates_portal_file in coordinates_files:
            deid_info = coordinates_portal_file.deidentify_cell_names(deid_names)
            if not deid_info:
                exit(51)
            deid_file = deid_info["name"]
            deid_names = deid_info["mapping"]
            print(" ".join(["A version of the coordinates file with",
                            "deidentifed cells names was named",
                            str(deid_file)]))
            print("Checking format of new file.")
            # Reset to deidentified file
            coordinates_portal_file = PortalFiles.CoordinatesFile(deid_file,
                                                  file_delimiter=prs_args.file_delimiter,
                                                  expected_header=PortalFiles.c_COORDINATES_HEADER)
            coordinates_portal_file.check()
            deid_coordinates_files.append(coordinates_portal_file)

    if metadata_portal_file:
        deid_info = metadata_portal_file.deidentify_cell_names(deid_names)
        if not deid_info:
            exit(52)
        deid_file = deid_info["name"]
        deid_names = deid_info["mapping"]
        print(" ".join(["A version of the metadata file with",
                        "deidentifed cells names was named",
                        str(deid_file)]))
        print("Checking format of new file.")
        # Reset to deidentified file
        deid_metadata_portal_file = PortalFiles.MetadataFile(deid_file,
                                      file_delimiter=prs_args.file_delimiter)
        metadata_portal_file.check()

    if expression_portal_files:
        for expression_portal_file in expression_portal_files:
            deid_info = expression_portal_file.deidentify_cell_names(deid_names)
            if not deid_info:
                exit(53)
            deid_file = deid_info["name"]
            deid_names = deid_info["mapping"]
            print(" ".join(["A version of the expression file with",
                            "deidentifed cells names was named",
                            str(deid_file)]))
            print("Checking format of new file.")
            # Reset to deidentified file
            deid_expression_portal_file = PortalFiles.ExpressionFile(deid_file,
                                            file_delimiter=prs_args.file_delimiter)
            deid_expression_portal_file.check()
            deid_expression_portal_files.append(deid_expression_portal_file)

    if prs_args.check_files:
        print("If multiple files are given, checking among files.")
        check_cell_names(expression_files=deid_expression_portal_files,
                         coordinates_file_group=deid_coordinates_files,
                         metadata_file=deid_metadata_portal_file)
print("Completed.")
