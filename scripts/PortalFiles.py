# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import abc
import argparse
import csv
import os

# Constants
# The expected header
c_CELL_ID = "cell"
c_COORDINATES_HEADER = ["CELL_NAME", "X", "Y"]
c_COORDINATES_HEADER_LENGTH = len(c_COORDINATES_HEADER)
c_CLUSTER_HEADER = ["CELL_NAME", "CLUSTER", "SUB-CLUSTER"]
c_CLUSTER_HEADER_LENGTH = len(c_CLUSTER_HEADER)
c_DEFAULT_DELIM = "\t"
c_DEID_POSTFIX = "_deidentifed"
c_EXPRESSION_00_ELEMENT = "GENE"
c_MAP_DELIM = "\t->\t"
c_MAP_POSTFIX = "_mapping"
c_REPORT_LINE_NUMBER_BLOCK = 500

# Demo links
c_CLUSTER_DEMO_LINK = "https://github.com/broadinstitute/single_cell_portal/blob/master/demo_data/cluster_assignments_example.txt"
c_COORDINATES_DEMO_LINK = "https://github.com/broadinstitute/single_cell_portal/blob/master/demo_data/cluster_coordinates_example.txt"
c_EXPRESSION_DEMO_LINK = "https://github.com/broadinstitute/single_cell_portal/blob/master/demo_data/expression_matrix_example.txt"

coordinates_file_has_error = False
coordinates_cell_names = []

cluster_file_has_error = False
cluster_cell_names = []

expression_file_has_error = False
expression_cell_names = []


class ParentPortalFile:

    def __init__(self, file_name, file_delimiter,
                 expected_header=None,
                 demo_file_link=None):
        """
        Create object. This is an objec that must be inherited
        due to abstract methods that are not implemented.
        Tested
        """
        self.file_has_error = False
        self.delimiter = file_delimiter
        self.demo_file = demo_file_link
        self.expected_header = expected_header
        self.expected_header_length = len(expected_header) if expected_header else 0
        self.file_name = file_name
        self.header = next(self.csv_handle)
        self.header_length = len(self.header)
        self.line_number = 1
        self.cell_names = None

    @property
    def csv_handle(self):
        """
        When the csv handle is given it is a
        fresh handle at the beginning of the file.
        Tested
        """
        return(csv.reader(open(self.file_name, 'r'), delimiter=self.delimiter))

    def check_header(self):
        """
        Check header of the file. If an error occurs set the object
        indicate an error occured. (file_has_error attribute).
        Tested
        """
        if len(self.expected_header) != self.header_length:
            self.file_has_error = True
            print(" ".join(["Error!\tExpected to receive a file with",
                            str(len(self.expected_header)),
                            "columns. Instead received",
                            str(self.header_length), "columns."]))

        if self.expected_header:
            for idx in range(self.header_length):
                if self.header[idx] != self.expected_header[idx]:
                    self.file_has_error = True
                    print("".join(["Error!\tExpected the column value \"",
                                   self.expected_header[idx],
                                   "\" but received \"",
                                   self.header[idx], "\"."]))
        return(self.file_has_error)

    @abc.abstractmethod
    def check_body(self):
        """
        Check body of the file. If an error occurs set the object
        indicate an error occured. (file_has_error attribute).
        Must be over written per file given files have different formats.
        """
        return()

    def check(self):
        """
        Checks the header and body of the file.
        Tested
        """
        print("Checking " + self.file_name)
        self.check_header()
        self.check_body()
        self.check_duplicate_cell_names()
        if self.file_has_error and self.demo_file:
            print(" ".join(["Error!\tThe provided file \"",
                            self.file_name,
                            "\"had errors.",
                            "An example file can be found at",
                            self.demo_file]))
        return(self.file_has_error)

    def get_duplicates(self, items):
        """
        Returns duplicates from an interable.
        Tested
        """
        visited = set()
        duplicates = set()
        for item in items:
            if item in visited:
                duplicates.add(item)
            else:
                visited.add(item)
        return(duplicates)

    def check_duplicate_cell_names(self):
        """
        Check for duplicate cell names.
        Tested
        """
        cell_count = len(self.cell_names)
        if cell_count != len(set(self.cell_names)):
            print(" ".join(["Error!\t",
                            self.file_name,
                            "file has duplicate cell names:"] + list(self.get_duplicates(self.cell_names))))
            self.file_has_error = True
        return(self.file_has_error)

    def compare_cell_names(self, portal_file):
        """
        Check cell names of this portal file wih another.
        Tested
        """
        print(" ".join(["Comparing", self.file_name,
                        "vs", portal_file.file_name]))
        compare_error = False
        if len(self.cell_names) != len(portal_file.cell_names):
            compare_error = True
            print(" ".join(["Error!\tExpected the same number of cells in the",
                            "files but this is not true.",
                            self.file_name, "had",
                            str(len(self.cell_names)), "unique cells.",
                            portal_file.file_name, "had",
                            str(len(portal_file.cell_names)),
                            "unique cells."]))
        # Check composition of lists
        difference = set(self.cell_names) - set(portal_file.cell_names)
        if len(difference) > 0:
            compare_error = True
            print(" ".join(["Gene names unique to",
                            self.file_name,
                            ":"]+list(difference)))
        difference = set(portal_file.cell_names) - set(self.cell_names)
        if len(difference) > 0:
            compare_error = True
            print(" ".join(["Gene names unique to",
                            portal_file.file_name,
                            ":"]+list(difference)))
        return(compare_error)

    def update_cell_names(self):
        """
        Update cell names from file.
        Tested
        """
        if not self.cell_names:
            self.cell_names = [line[0] for line in self.csv_handle][1:]

    @abc.abstractmethod
    def deidentify_cell_names(self):
        return()

    def __str__(self):
        """
        Create string representation of object.
        Tested
        """
        contents = []
        contents.append("Error:"+str(self.file_has_error))
        contents.append("Delim:"+str(self.delimiter))
        contents.append("Demo:"+str(self.demo_file))
        contents.append("ExpectedHeader:"+",".join(self.expected_header))
        contents.append("ExpectedHeaderLen:"+str(self.expected_header_length))
        contents.append("FileName:"+self.file_name)
        contents.append("Header:"+",".join(self.header))
        contents.append("HeaderLen:"+str(self.header_length))
        contents.append("LineNumber:"+str(self.line_number))
        contents.append("CellNames:"+str(self.cell_names))
        return("; ".join(contents))


class CoordinatesFile(ParentPortalFile):

    def __init__(self, file_name, file_delimiter=c_DEFAULT_DELIM,
                 expected_header=c_COORDINATES_HEADER,
                 demo_file_link=c_COORDINATES_DEMO_LINK):
        """
        Represents a coordinate file used for visualizations in the portal.
        Tested
        """
        ParentPortalFile.__init__(self, file_name, file_delimiter,
                                  expected_header=expected_header,
                                  demo_file_link=demo_file_link)
        self.update_cell_names()

    def check_body(self):
        """
        Check body of file.
        Tested.
        """
        check_handle = self.csv_handle
        # Need to skip the header
        next(check_handle)
        for file_line in check_handle:
            self.line_number += 1
            if len(file_line) != self.expected_header_length:
                self.file_has_error = True
                print(" ".join(["Error!\tLine:",
                                str(self.line_number),
                                "Expected", str(self.expected_header_length),
                                "columns but received",
                                str(len(file_line)), "."]))

            for token in file_line[1:3]:
                try:
                    float(token)
                except ValueError:
                    self.file_has_error = True
                    print(" ".join(["Error!\tExpected a float. Line:",
                                    str(self.line_number),
                                    "Value:", token]))

    def deidentify_cell_names(self, cell_names_change=None):
        """
        Deidentify cell names. Create a new file that is deidentified and
        write a mapping file of the names. Do not change the original file.
        If cell names is given, those mappings will be used.
        """
        new_file_lines = []
        self.update_cell_names()
        update_names = {c_COORDINATES_HEADER[0]: c_COORDINATES_HEADER[0]}
        if not cell_names_change:
            cell_names_change = {}
        if not len(cell_names_change):
            for name in self.cell_names:
                cell_names_change.setdefault(name,
                                             "_".join([c_CELL_ID,
                                                       str(len(cell_names_change))]))
        update_names.update(cell_names_change)
        deid_file_name, deid_file_ext = os.path.splitext(self.file_name)
        # New deidentified file, check to make sure it does not exist
        new_deid_file = deid_file_name + c_DEID_POSTFIX + deid_file_ext
        if os.path.exists(new_deid_file):
            print(" ".join(["ERROR: Can not deidentify file, the file to be",
                            "written already exists. Please move or",
                            "rename the file:",
                            os.path.abspath(new_deid_file)]))
            return(None)
        # Mapping file, check to make sure it does not exist
        new_mapping_file = deid_file_name + c_MAP_POSTFIX + deid_file_ext
        if os.path.exists(new_mapping_file):
            print(" ".join(["ERROR: Can not deidentify file, the mapping",
                            "file already exists. Please move or",
                            "rename the file:",
                            os.path.abspath(new_mapping_file)]))
            return(None)

        # Write deidentified file
        with open(deid_file_name + c_DEID_POSTFIX + deid_file_ext, 'w') as deid_file:
            write_deid = self.csv_handle
            for file_line in write_deid:
                new_file_lines.append(self.delimiter.join([update_names[file_line[0]]]+file_line[1:]))
            deid_file.write("\n".join(new_file_lines))
        # Write mapping file
        with open(new_mapping_file, 'w') as map_file:
            map_file.write("\n".join(sorted([name_key+c_MAP_DELIM+name_value
                                      for name_key, name_value
                                      in update_names.items()])))
        return({"name": deid_file.name, "mapping": cell_names_change})


class ClusterFile(ParentPortalFile):

    def __init__(self, file_name, file_delimiter=c_DEFAULT_DELIM,
                 expected_header=c_CLUSTER_HEADER,
                 demo_file_link=c_CLUSTER_DEMO_LINK):
        """
        Represents a cluster / metadata file used for visualizations.
        Tested
        """
        ParentPortalFile.__init__(self, file_name, file_delimiter,
                                  expected_header=expected_header,
                                  demo_file_link=demo_file_link)
        self.update_cell_names()

    def check_body(self):
        """
        Check body of file.
        Tested.
        """
        check_handle = self.csv_handle
        # Need to skip the header
        next(check_handle)
        for file_line in check_handle:
            self.line_number = self.line_number + 1
            if len(file_line) != self.expected_header_length:
                self.file_has_error = True
                print(" ".join(["Error!\tLine:",
                                str(self.line_number),
                                "Expected",
                                str(self.expected_header_length),
                                "columns but received",
                                str(len(file_line)), "."]))

    def deidentify_cell_names(self, cell_names_change=None):
        """
        Deidentify cell names. Create a new file that is deidentified and
        write a mapping file of the names. Do not change the original file.
        If cell names is given, those mappings will be used.
        """
        new_file_lines = []
        self.update_cell_names()
        update_names = {c_CLUSTER_HEADER[0]: c_CLUSTER_HEADER[0]}
        if not cell_names_change:
            cell_names_change = {}
        if not len(cell_names_change):
            for name in self.cell_names:
                cell_names_change.setdefault(name,
                                             "_".join([c_CELL_ID,
                                                       str(len(cell_names_change))]))
        update_names.update(cell_names_change)
        deid_file_name, deid_file_ext = os.path.splitext(self.file_name)
        # New deidentified file, check to make sure it does not exist
        new_deid_file = deid_file_name + c_DEID_POSTFIX + deid_file_ext
        if os.path.exists(new_deid_file):
            print(" ".join(["ERROR: Can not deidentify file, the file to be",
                            "written already exists. Please move or",
                            "rename the file:",
                            os.path.abspath(new_deid_file)]))
            return(None)
        # Mapping file, check to make sure it does not exist
        new_mapping_file = deid_file_name + c_MAP_POSTFIX + deid_file_ext
        if os.path.exists(new_mapping_file):
            print(" ".join(["ERROR: Can not deidentify file, the mapping",
                            "file already exists. Please move or",
                            "rename the file:",
                            os.path.abspath(new_mapping_file)]))
            return(None)

        # Write deidentified file
        with open(deid_file_name + c_DEID_POSTFIX + deid_file_ext, 'w') as deid_file:
            write_deid = self.csv_handle
            for file_line in write_deid:
                new_file_lines.append(self.delimiter.join([update_names[file_line[0]]]+file_line[1:]))
            deid_file.write("\n".join(new_file_lines))
        # Write mapping file
        with open(new_mapping_file, 'w') as map_file:
            map_file.write("\n".join(sorted([name_key+c_MAP_DELIM+name_value
                                      for name_key, name_value
                                      in update_names.items()])))
        return({"name": deid_file.name, "mapping": cell_names_change})


class ExpressionFile(ParentPortalFile):

    def __init__(self, file_name, file_delimiter=c_DEFAULT_DELIM,
                 expected_header=None,
                 demo_file_link=c_EXPRESSION_DEMO_LINK):
        """
        Represents an expression file holding measurements.
        Tested
        """
        ParentPortalFile.__init__(self, file_name, file_delimiter,
                                  expected_header=expected_header,
                                  demo_file_link=demo_file_link)
        self.update_cell_names()

    def check_header(self):
        """
        Check header of the file. If an error occurs set the object
        indicate an error occured. (file_has_error attribute).
        Tested
        """
        if self.header[0] != c_EXPRESSION_00_ELEMENT:
            self.file_has_error = True
            print(" ".join(["Error!\tExpected the first column,",
                            "first row position to be",
                            c_EXPRESSION_00_ELEMENT,
                            "but is was", self.header[0], "."]))

    def check_body(self):
        """
        Check body of the file. If an error occurs set the object
        indicate an error occured. (file_has_error attribute).
        Tested
        """
        check_handle = self.csv_handle
        # Need to skip the header
        next(check_handle)
        for file_line in check_handle:
            self.line_number += 1
            if len(file_line) != self.header_length:
                self.file_has_error = True
                print(" ".join(["Error!\tLine: ",
                                str(self.line_number),
                                ". Expected", str(self.header_length),
                                "columns but received",
                                str(len(file_line)), "."]))

            for token in file_line[1:]:
                try:
                    float(token)
                except ValueError:
                    self.file_has_error = True
                    print(" ".join(["Error!\tLine: ",
                                    str(self.line_number),
                                    ". Unexpected value: ",
                                    token, "."]))
            if self.line_number % c_REPORT_LINE_NUMBER_BLOCK == 0:
                print("    Process update: Line " + str(self.line_number))

    def update_cell_names(self):
        """
        Update cell names from file.
        Tested
        """
        if not self.cell_names:
            self.cell_names = self.header[1:self.header_length+1]

    def deidentify_cell_names(self, cell_names_change=None):
        """
        Deidentify cell names. Create a new file that is deidentified and
        write a mapping file of the names. Do not change the original file.
        If cell names is given, those mappings will be used.
        Tested
        """
        new_file_lines = []
        self.update_cell_names()
        update_names = {c_EXPRESSION_00_ELEMENT: c_EXPRESSION_00_ELEMENT}
        if not cell_names_change:
            cell_names_change = {}
        if not len(cell_names_change):
            for name in self.cell_names:
                cell_names_change.setdefault(name,
                                             "_".join([c_CELL_ID,
                                                       str(len(cell_names_change))]))
        update_names.update(cell_names_change)

        deid_file_name, deid_file_ext = os.path.splitext(self.file_name)
        # New deidentified file, check to make sure it does not exist
        new_deid_file = deid_file_name + c_DEID_POSTFIX + deid_file_ext
        if os.path.exists(new_deid_file):
            print(" ".join(["ERROR: Can not deidentify file, the file to be",
                            "written already exists. Please move or",
                            "rename the file:",
                            os.path.abspath(new_deid_file)]))
            return(None)
        # Mapping file, check to make sure it does not exist
        new_mapping_file = deid_file_name + c_MAP_POSTFIX + deid_file_ext
        if os.path.exists(new_mapping_file):
            print(" ".join(["ERROR: Can not deidentify file, the mapping",
                            "file already exists. Please move or",
                            "rename the file:",
                            os.path.abspath(new_mapping_file)]))
            return(None)

        # Write deidentified file
        with open(new_deid_file, 'w') as deid_file:
            write_deid = self.csv_handle
            new_file_lines.append(self.delimiter.join([update_names[name]
                                  for name in next(write_deid)]))
            for file_line in write_deid:
                new_file_lines.append(self.delimiter.join(file_line))
            deid_file.write("\n".join(new_file_lines))

        # Write mapping file
        with open(new_mapping_file, 'w') as map_file:
            map_file.write("\n".join(sorted([name_key+c_MAP_DELIM+name_value
                                      for name_key, name_value
                                      in update_names.items()])))
        return({"name": deid_file.name, "mapping": cell_names_change})
