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
                     coordinates_file=None,
                     cluster_file=None):
    """
    Check files among themselves.
    """
    if cluster_file:
        if coordinates_file:
            cluster_file.compare_cell_names(coordinates_file)
        if expression_file:
            cluster_file.compare_cell_names(expression_file)
    if coordinates_file:
        if expression_file:
            coordinates_file.compare_cell_names(expression_file)


prsr_arguments = argparse.ArgumentParser(
    prog="verify_portal_file.py",
    description="Verify files for the single cell portal",
    conflict_handler="resolve",
    formatter_class=argparse.HelpFormatter)

prsr_arguments.add_argument("--coordinates_file",
                            default=None,
                            dest="coordinates_file",
                            type=str,
                            help="".join(["The file that holds the ",
                                          "coordinates for the main ",
                                          "visualization."]))

prsr_arguments.add_argument("--cluster_file",
                            default=None,
                            dest="cluster_file",
                            type=str,
                            help="".join(["The file that holds the clusters ",
                                          "for the main visualization."]))

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

prs_args = prsr_arguments.parse_args()

coordinates_portal_file = None
cluster_portal_file = None
expression_portal_file = None

if prs_args.coordinates_file:
    coordinates_portal_file = PortalFiles.CoordinatesFile(prs_args.coordinates_file,
                                              file_delimiter=prs_args.file_delimiter,
                                              expected_header=PortalFiles.c_COORDINATES_HEADER,
                                              demo_file_link="https://github.com/broadinstitute/single_cell_portal/blob/master/demo_data/cluster_coordinates_example.txt")
    coordinates_portal_file.check()

if prs_args.cluster_file:
    cluster_portal_file = PortalFiles.ClusterFile(prs_args.cluster_file,
                                      file_delimiter=prs_args.file_delimiter,
                                      expected_header=PortalFiles.c_CLUSTER_HEADER,
                                      demo_file_link="https://github.com/broadinstitute/single_cell_portal/blob/master/demo_data/cluster_assignments_example.txt")
    cluster_portal_file.check()

if prs_args.expression_file:
    expression_portal_file = PortalFiles.ExpressionFile(prs_args.expression_file,
                                            file_delimiter=prs_args.file_delimiter,
                                            demo_file_link="https://github.com/broadinstitute/single_cell_portal/blob/master/demo_data/expression_matrix_example.txt")
    expression_portal_file.check()

check_cell_names(expression_file=expression_portal_file,
                 coordinates_file=coordinates_portal_file,
                 cluster_file=cluster_portal_file)

# Deidentify all cell names (optionally) after all QC checks are made.
if prs_args.do_deidentify_cell:
    print("Deidentifying Cell Nams/Ids")

    # Holds the deidentified cell names if used
    deid_names = {}

    if prs_args.coordinates_file:
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
                                              expected_header=PortalFiles.c_COORDINATES_HEADER,
                                              demo_file_link="https://github.com/broadinstitute/single_cell_portal/blob/master/demo_data/cluster_coordinates_example.txt")
        coordinates_portal_file.check()

    if prs_args.cluster_file:
        deid_info = cluster_portal_file.deidentify_cell_names(deid_names)
        if not deid_info:
            exit(52)
        deid_file = deid_info["name"]
        deid_names = deid_info["mapping"]
        print(" ".join(["A version of the cluster/metadata file with",
                        "deidentifed cells names was named",
                        str(deid_file)]))
        print("Checking format of new file.")
        # Reset to deidentified file
        cluster_portal_file = PortalFiles.ClusterFile(deid_file,
                                      file_delimiter=prs_args.file_delimiter,
                                      expected_header=PortalFiles.c_CLUSTER_HEADER,
                                      demo_file_link="https://github.com/broadinstitute/single_cell_portal/blob/master/demo_data/cluster_assignments_example.txt")
        cluster_portal_file.check()

    if prs_args.expression_file:
        deid_info = expression_portal_file.deidentify_cell_names(deid_names)
        if not deid_info:
            exit(53)
        deid_file = deid_info["name"]
        deid_names = deid_info["mapping"]
        print(" ".join(["A version of the expressionon file with",
                        "deidentifed cells names was named",
                        str(deid_file)]))
        print("Checking format of new file.")
        # Reset to deidentified file
        expression_portal_file = PortalFiles.ExpressionFile(deid_file,
                                            file_delimiter=prs_args.file_delimiter,
                                            demo_file_link="https://github.com/broadinstitute/single_cell_portal/blob/master/demo_data/expression_matrix_example.txt")
        expression_portal_file.check()

    print("If multiple files are given, checking among files.")
    check_cell_names(expression_file=expression_portal_file,
                     coordinates_file=coordinates_portal_file,
                     cluster_file=cluster_portal_file)
print("Completed.")
