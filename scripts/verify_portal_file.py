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


def check_cell_names(expression_file=None,
                     coordinates_file_group=None,
                     metadata_file=None):
    """
    Check files among themselves.
    """
    if metadata_file:
        if coordinates_file_group:
            for coordinates_file in coordinates_file_group:
                metadata_file.compare_cell_names(coordinates_file)
        if expression_file:
            metadata_file.compare_cell_names(expression_file)
    if coordinates_file_group:
        if expression_file:
            for coordinates_file in coordinates_file_group:
                coordinates_file.compare_cell_names(expression_file)

def check_gene_names(expression_file=None,
                     gene_files=None):
    """
    Check gene names among files.
    """

    if gene_files and expression_file:
        for gene_list in gene_files:
            if gene_list:
                print(" ".join(["Comparing gene names in",
                                gene_list.file_name,
                                "with the expression file:",
                                expression_file.file_name]))
                gene_list.compare_gene_names(expression_file)

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

prsr_arguments.add_argument("--expression_file",
                            default=None,
                            dest="expression_file",
                            type=str,
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

prs_args = prsr_arguments.parse_args()

# Holds the file objects a opposed to the file names
coordinates_files = []
metadata_portal_file = None
expression_portal_file = None
gene_list_files = []

if prs_args.coordinates_file_group:
    for coordinates_file in prs_args.coordinates_file_group:
        coordinates_portal_file = PortalFiles.CoordinatesFile(coordinates_file,
                                              file_delimiter=prs_args.file_delimiter,
                                              expected_header=PortalFiles.c_COORDINATES_HEADER)
        coordinates_portal_file.check()
        coordinates_files.append(coordinates_portal_file)

if prs_args.metadata_file:
    metadata_portal_file = PortalFiles.MetadataFile(prs_args.metadata_file,
                                      file_delimiter=prs_args.file_delimiter)
    metadata_portal_file.check()

if prs_args.expression_file:
    expression_portal_file = PortalFiles.ExpressionFile(prs_args.expression_file,
                                            file_delimiter=prs_args.file_delimiter)
    expression_portal_file.check()

if prs_args.gene_list_group:
    for gene_list in prs_args.gene_list_group:
        gene_list_file = PortalFiles.GeneListFile(gene_list,
                                                  file_delimiter=prs_args.file_delimiter)
        gene_list_file.check()
        gene_list_files.append(gene_list_file)

check_cell_names(expression_file=expression_portal_file,
                 coordinates_file_group=coordinates_files,
                 metadata_file=metadata_portal_file)

check_gene_names(expression_file=expression_portal_file,
                 gene_files=gene_list_files)

# Deidentify all cell names (optionally) after all QC checks are made.
if prs_args.do_deidentify_cell:
    print("Deidentifying Cell Names/Ids")

    deid_coordinates_files = []
    deid_metadata_portal_file = None
    deid_expression_portal_file = None

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

    if expression_portal_file:
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
        expression_portal_file.check()

    print("If multiple files are given, checking among files.")
    check_cell_names(expression_file=deid_expression_portal_file,
                     coordinates_file_group=deid_coordinates_files,
                     metadata_file=deid_metadata_portal_file)
print("Completed.")
