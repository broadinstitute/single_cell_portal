# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import PortalFiles
import unittest

__author__ = "Timothy Tickle"
__copyright__ = "Copyright 2016"
__credits__ = ["Timothy Tickle", "Brian Haas"]
__license__ = "MIT"
__maintainer__ = "Timothy Tickle"
__email__ = "ttickle@broadinstitute.org"
__status__ = "Development"


def files_are_equivalent(file_path_1, file_path_2):
    """
    Returns if the contents of to files are the same.
    Errors if the files are missing.
    * str_file_path_1 : String
                        Path of the first of the files to compare to each other
    * str_file_path_2 : String
                        Path of the second of files to compare to each other
    * Return : Boolean
               True indicates the contents of the files are exact.
    """
    if not os.path.exists(file_path_1):
        raise IOError("Missing file: " + file_path_1)
    if not os.path.exists(file_path_2):
        raise IOError("Missing file: " + file_path_2)

    # Compare line by line and short circuit on a mismatched line.
    with open(file_path_1) as check_file_1:
        with open(file_path_2) as check_file_2:
            for line in check_file_1:
                compare_line = next(check_file_2)
                if not line == compare_line:
                    print("::"+line+"::")
                    print("::"+compare_line+"::")
                    return(False)
    return(True)


class CoordinatesFileTester(unittest.TestCase):
    """
    Tests the Coordinates File object.
    """

    def test_init(self):
        """
        Make sure init can occur
        """
        test_file = os.path.join("test_files", "coordinates.txt")
        PortalFiles.CoordinatesFile(test_file)
        self.assertTrue(True, 'Coordinates file can init.')

    def test_init_details(self):
        """
        Check internals on init.
        """
        test_file_name = os.path.join("test_files", "coordinates.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        has_error = False
        error_message = []
        if test_file.file_has_error:
            has_error = True
            error_message.append("Started with a false error state.")
        if not test_file.delimiter == PortalFiles.c_DEFAULT_DELIM:
            has_error = True
            error_message.append("Delimiter was not set correctly.")
        if not test_file.demo_file == PortalFiles.c_COORDINATES_DEMO_LINK:
            has_error = True
            error_message.append("Demo link was not set correctly.")
        if(not ".".join(test_file.expected_header) ==
               ".".join(PortalFiles.c_COORDINATES_HEADER)):
            has_error = True
            error_message.append("Started with a wrong expected header.")
        if not test_file.expected_header_length == PortalFiles.c_COORDINATES_HEADER_LENGTH:
            has_error = True
            error_message.append("Started with a false error state.")
        if not test_file.file_name == test_file_name:
            has_error = True
            error_message.append("File name incorrect.")
        if not test_file.header_length == 6:
            has_error = True
            error_message.append("File length incorrect.")
        if not test_file.line_number == 1:
            has_error = True
            error_message.append("Wrong initial file number.")
        if test_file.cell_names is None:
            has_error = True
            error_message.append("Incorrect cell names on init.")
        error_message.append(str(test_file))
        self.assertTrue(not has_error, error_message)

    def test_init_str(self):
        """
        Check str on init.
        """
        test_file_name = os.path.join("test_files", "coordinates.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        actual_str = str(test_file)
        correct_str = "; ".join(["Error:"+str(False),
                                 "Delim:"+PortalFiles.c_DEFAULT_DELIM,
                                 "Demo:"+PortalFiles.c_COORDINATES_DEMO_LINK,
                                 "ExpectedHeader:"+",".join(PortalFiles.c_COORDINATES_HEADER),
                                 "ExpectedHeaderLen:"+str(PortalFiles.c_COORDINATES_HEADER_LENGTH),
                                 "FileName:"+test_file_name,
                                 "Header:"+",".join(["NAME","X","Y","Z","Category","Intensity"]),
                                 "HeaderLen:"+str(6),
                                 "LineNumber:"+str(1),
                                 "CellNames:"+str(test_file.cell_names)])
        self.assertTrue(correct_str == actual_str,
                        "Expected="+correct_str+"\nReceived="+actual_str)

    def test_check_header_correct(self):
        """
        Check the header is called correct when it is.
        """
        test_file_name = os.path.join("test_files", "coordinates.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_header()
        self.assertTrue(not test_file.file_has_error,
                        "Should not have reached an error state.")

    def test_check_header_incorrect(self):
        """
        Check the header is called incorrect when position 00 is incorrect.
        """
        test_file_name = os.path.join("test_files",
                                      "coordinates_bad_header.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_header()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_header_for_duplicates(self):
        """
        Check the header is called incorrect when duplicates exist.
        """
        test_file_name = os.path.join("test_files",
                                      "coordinates_bad_header_duplicates.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_header()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_body_correct(self):
        """
        Check the body is called correct when it is.
        """
        test_file_name = os.path.join("test_files", "coordinates.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_body()
        self.assertTrue(not test_file.file_has_error,
                        "Should not have reached an error state.")

    def test_check_body_incorrect_type(self):
        """
        Check the body is called incorrect when it is incorrect.
        This file has a bad entry, wrong type.
        """
        test_file_name = os.path.join("test_files", "coordinates_bad_body.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_body()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_body_incorrect_type_2(self):
        """
        Check the body is called incorrect when it is incorrect.
        This file has a missing entry.
        """
        test_file_name = os.path.join("test_files",
                                      "coordinates_bad_body_2.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_body()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_get_duplicates_no_duplicates(self):
        """
        Get duplicates from file, no duplicates.
        """
        test_file_name = os.path.join("test_files", "coordinates.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        duplicates = test_file.get_duplicates(test_file.cell_names)
        self.assertTrue(len(duplicates) == 0,
                        "Should be empty with no duplicates.")

    def test_get_duplicates_with_duplicates(self):
        """
        Get duplicates from file, with 2 duplicates.
        """
        test_file_name = os.path.join("test_files",
                                      "coordinates_duplicates.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        duplicates = test_file.get_duplicates(test_file.cell_names)
        self.assertTrue(len(duplicates) == 2,
                        "Should have 2 duplicates.")

    def test_check_duplicate_cell_names_no_duplicates(self):
        """
        Check duplicates cell names in file, no duplicates.
        """
        test_file_name = os.path.join("test_files", "coordinates.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        original_len = len(test_file.cell_names)
        test_file.check_duplicate_cell_names()
        self.assertTrue(not test_file.file_has_error,
                        " ".join(["There are no duplicates,",
                                  "no error detected."]))

    def test_check_duplicate_cell_names_with_duplicates(self):
        """
        Check duplicates cell names in file, wirh 2 duplicates.
        """
        test_file_name = os.path.join("test_files",
                                      "coordinates_duplicates.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        original_len = len(test_file.cell_names)
        test_file.check_duplicate_cell_names()
        self.assertTrue(test_file.file_has_error,
                        " ".join(["There are 2 duplicates,",
                                  "error detected."]))

    def test_check_correct(self):
        """
        Check the file is called correct when it is.
        """
        test_file_name = os.path.join("test_files", "coordinates.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check()
        self.assertTrue(not test_file.file_has_error,
                        "Should not have reached an error state.")

    def test_check_correct_bad_header(self):
        """
        Check the file is called incorrect when a header is bad.
        """
        test_file_name = os.path.join("test_files",
                                      "coordinates_bad_header.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_correct_bad_body(self):
        """
        Check the file is called incorrect when the body is bad.
        """
        test_file_name = os.path.join("test_files", "coordinates_bad_body.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_correct_bad_body_duplicates(self):
        """
        Check the file is called incorrect when the body has duplicates.
        """
        test_file_name = os.path.join("test_files",
                                      "coordinates_duplicates.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_compare_cell_names_for_identical(self):
        """
        Check comparing cell names for two identical files.
        """
        test_file_name = os.path.join("test_files", "coordinates.txt")
        test_file_name_2 = os.path.join("test_files", "coordinates.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        test_file_2 = PortalFiles.CoordinatesFile(test_file_name_2)
        self.assertTrue((not test_file.file_has_error) and
                        (not test_file_2.file_has_error),
                        "Did not start test with a no error state.")
        compare_error = test_file.compare_cell_names(test_file_2)
        self.assertTrue(not compare_error,
                        "Should not have reached an error state.")

    def test_compare_cell_names_for_correct_files(self):
        """
        Check comparing cell names for two files with identical cell names.
        """
        test_file_name = os.path.join("test_files", "coordinates.txt")
        test_file_name_2 = os.path.join("test_files", "metadata.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        test_file_2 = PortalFiles.MetadataFile(test_file_name_2)
        self.assertTrue((not test_file.file_has_error) and
                        (not test_file_2.file_has_error),
                        "Did not start test with a no error state.")
        compare_error = test_file.compare_cell_names(test_file_2)
        self.assertTrue(not compare_error,
                        "Should not have reached an error state.")

    def test_compare_cell_names_for_incorrect_files(self):
        """
        Check comparing cell names for two files,
        this one with duplicate names.
        """
        test_file_name = os.path.join("test_files",
                                      "coordinates_duplicates.txt")
        test_file_name_2 = os.path.join("test_files", "metadata.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        test_file_2 = PortalFiles.MetadataFile(test_file_name_2)
        self.assertTrue((not test_file.file_has_error) and
                        (not test_file_2.file_has_error),
                        "Did not start test with a no error state.")
        compare_error = test_file.compare_cell_names(test_file_2)
        self.assertTrue(compare_error,
                        "Should have reached an error state.")

    def test_compare_cell_names_for_incorrect_compare_files(self):
        """
        Check comparing cell names for two files,
        the comparing file with duplicate names.
        """
        test_file_name = os.path.join("test_files",
                                      "coordinates.txt")
        test_file_name_2 = os.path.join("test_files", "metadata_duplicates.txt")
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        test_file_2 = PortalFiles.MetadataFile(test_file_name_2)
        self.assertTrue((not test_file.file_has_error) and
                        (not test_file_2.file_has_error),
                        "Did not start test with a no error state.")
        compare_error = test_file.compare_cell_names(test_file_2)
        self.assertTrue(compare_error,
                        "Should have reached an error state.")

    def test_update_cell_names_from_none(self):
        """
        Update cell names from a None value.
        """
        test_file = os.path.join("test_files", "coordinates.txt")
        test_file = PortalFiles.CoordinatesFile(test_file)
        names = ",".join(["CELL_0001","CELL_00010","CELL_00011",
                         "CELL_00012","CELL_00013","CELL_00014",
                         "CELL_00015","CELL_0002","CELL_0003",
                         "CELL_0004","CELL_0005","CELL_0006",
                         "CELL_0007","CELL_0008","CELL_0009"])
        test_file.cell_names = None
        test_file.update_cell_names()
        names_after = ",".join(sorted(test_file.cell_names))
        self.assertTrue(names == names_after,
                        "Updated cell names are correct.")

    def test_update_cell_names_from_init(self):
        """
        Update cell names from an init value.
        """
        test_file = os.path.join("test_files", "coordinates.txt")
        test_file = PortalFiles.CoordinatesFile(test_file)
        names = ",".join(["CELL_0001","CELL_00010","CELL_00011",
                         "CELL_00012","CELL_00013","CELL_00014",
                         "CELL_00015","CELL_0002","CELL_0003",
                         "CELL_0004","CELL_0005","CELL_0006",
                         "CELL_0007","CELL_0008","CELL_0009"])
        test_file.update_cell_names()
        test_file.update_cell_names()
        test_file.update_cell_names()
        names_after = ",".join(sorted(test_file.cell_names))
        self.assertTrue(names == names_after,
                        "Updated cell names are correct.")

    def test_deidentify_cells(self):
        """
        Test deidentify file.
        """
        test_file_name = os.path.join("test_files", "coordinates.txt")
        deid_file = os.path.join("test_files",
                                 "coordinates"+PortalFiles.c_DEID_POSTFIX+".txt")
        map_file = os.path.join("test_files",
                                "coordinates"+PortalFiles.c_MAP_POSTFIX+".txt")
        correct_file = os.path.join("test_files",
                                    "coordinates_deidentifed_correct.txt")
        correct_map = os.path.join("test_files",
                                   "coordinates_mapping_correct.txt")
        # Remove the test files if the exist
        if(os.path.exists(deid_file)):
            os.remove(deid_file)
        if(os.path.exists(map_file)):
            os.remove(map_file)
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        deid_file_name = test_file.deidentify_cell_names()["name"]
        self.assertTrue(files_are_equivalent(file_path_1=deid_file_name,
                                             file_path_2=correct_file) and
                        files_are_equivalent(file_path_1=map_file,
                                             file_path_2=correct_map),
                                             "Can not deidentify file.")

    def test_deidentify_cells_check_created_names(self):
        """
        Test deidentify file. Check to make sure cell
        names are created and passed.
        """
        test_file_name = os.path.join("test_files", "coordinates.txt")
        deid_file = os.path.join("test_files",
                                 "coordinates"+PortalFiles.c_DEID_POSTFIX+".txt")
        map_file = os.path.join("test_files",
                                "coordinates"+PortalFiles.c_MAP_POSTFIX+".txt")
        cell_mappings_truth = ["CELL_0001:cell_0", "CELL_0002:cell_1", "CELL_0003:cell_2",
                               "CELL_0004:cell_3", "CELL_0005:cell_4", "CELL_0006:cell_5",
                               "CELL_0007:cell_6", "CELL_0008:cell_7", "CELL_0009:cell_8",
                               "CELL_00010:cell_9", "CELL_00011:cell_10", "CELL_00012:cell_11",
                               "CELL_00013:cell_12", "CELL_00014:cell_13", "CELL_00015:cell_14"]
        cell_mappings_truth = ",".join(sorted(cell_mappings_truth))
        # Remove the test files if the exist
        if(os.path.exists(deid_file)):
            os.remove(deid_file)
        if(os.path.exists(map_file)):
            os.remove(map_file)
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        deid_info = test_file.deidentify_cell_names()
        deid_file_mapping = deid_info["mapping"]
        cell_mappings = []
        for sorted_key in deid_file_mapping.keys():
            cell_mappings.append(str(sorted_key)+":"+str(deid_file_mapping[sorted_key]))
        cell_mappings = ",".join(sorted(cell_mappings))
        self.assertTrue(cell_mappings == cell_mappings_truth,
                        "Returned mappings were not expected.="+cell_mappings)

    def test_deidentify_cells_precreated_names(self):
        """
        Test deidentify file with cell already made.
        """
        test_file_name = os.path.join("test_files", "coordinates.txt")
        deid_file = os.path.join("test_files",
                                 "coordinates"+PortalFiles.c_DEID_POSTFIX+".txt")
        map_file = os.path.join("test_files",
                                "coordinates"+PortalFiles.c_MAP_POSTFIX+".txt")
        correct_file = os.path.join("test_files",
                                    "coordinates_deidentifed_precreated_correct.txt")
        correct_map = os.path.join("test_files",
                                   "coordinates_mapping_precreated_correct.txt")
        # Remove the test files if the exist
        if(os.path.exists(deid_file)):
            os.remove(deid_file)
        if(os.path.exists(map_file)):
            os.remove(map_file)
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        names = dict(zip(test_file.cell_names, [str(i) for i in range(len(test_file.cell_names))]))
        deid_file_name = test_file.deidentify_cell_names(cell_names_change=names)["name"]
        self.assertTrue(files_are_equivalent(file_path_1=deid_file_name,
                                             file_path_2=correct_file) and
                        files_are_equivalent(file_path_1=map_file,
                                             file_path_2=correct_map),
                                             "Can not deidentify file.")

    def test_deidentify_cells_for_existing_files(self):
        """
        Test deidentify file but with the files that are to be made already
        there so an error should occur.
        """
        test_file_name = os.path.join("test_files", "coordinates.txt")
        deid_file = os.path.join("test_files",
                                 "coordinates"+PortalFiles.c_DEID_POSTFIX+".txt")
        map_file = os.path.join("test_files",
                                "coordinates"+PortalFiles.c_MAP_POSTFIX+".txt")
        correct_file = os.path.join("test_files",
                                    "coordinates_deidentifed_correct.txt")
        correct_map = os.path.join("test_files",
                                   "coordinates_mapping_correct.txt")
        # Make sure the files to be created exist so an error will occur
        if(not os.path.exists(deid_file)):
            with(open(deid_file, 'w')) as pre_exist_file:
                pre_exist_file.write(["    "])
        if(not os.path.exists(map_file)):
            with(open(map_file, 'w')) as pre_exist_file:
                pre_exist_file.write(["    "])
        test_file = PortalFiles.CoordinatesFile(test_file_name)
        deid_file_name = test_file.deidentify_cell_names()
        self.assertFalse((not deid_file_name is None) and
                          not files_are_equivalent(file_path_1=deid_file_name,
                                                   file_path_2=correct_file) and
                          not files_are_equivalent(file_path_1=map_file,
                                                   file_path_2=correct_map),
                          "Deidentify should not occur when the files being made exist.")


class ExpressionFileTester(unittest.TestCase):
    """
    Tests the expression file object.
    """

    def test_init(self):
        """
        Make sure init can occur.
        """
        test_file = os.path.join("test_files", "expression.txt")
        PortalFiles.ExpressionFile(test_file)
        self.assertTrue(True, "Expression File can init.")

    def test_check_header_correct(self):
        """
        Check the header is called correct when it is.
        """
        test_file_name = os.path.join("test_files", "expression.txt")
        test_file = PortalFiles.ExpressionFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_header()
        self.assertTrue(not test_file.file_has_error,
                        "Should not have reached an error state.")

    def test_check_header_incorrect_00(self):
        """
        Check the header is called incorrect when element 00 is wrong.
        """
        test_file_name = os.path.join("test_files",
                                      "expression_bad_header.txt")
        test_file = PortalFiles.ExpressionFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_header()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_header_incorrect_element_count(self):
        """
        Check the header is called incorrect when 00 is blank.
        """
        test_file_name = os.path.join("test_files",
                                      "expression_bad_header_2.txt")
        test_file = PortalFiles.ExpressionFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_header()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_body_correct(self):
        """
        Check the body is called correct when it is.
        """
        test_file_name = os.path.join("test_files", "expression.txt")
        test_file = PortalFiles.ExpressionFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_body()
        self.assertTrue(not test_file.file_has_error,
                        "Should not have reached an error state.")

    def test_check_body_incorrect_1(self):
        """
        Check the body is called incorrect when it has a missing element.
        """
        test_file_name = os.path.join("test_files",
                                      "expression_bad_body_1.txt")
        test_file = PortalFiles.ExpressionFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_body()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_body_incorrect_2(self):
        """
        Check the body is called incorrect when it has a wrong type element.
        """
        test_file_name = os.path.join("test_files",
                                      "expression_bad_body_2.txt")
        test_file = PortalFiles.ExpressionFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_body()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_update_cell_names_from_none(self):
        """
        Update cell names from a None value.
        """
        test_file = os.path.join("test_files", "expression.txt")
        test_file = PortalFiles.ExpressionFile(test_file)
        names = ",".join(sorted(test_file.cell_names))
        test_file.cell_names = None
        test_file.update_cell_names()
        names_after = ",".join(sorted(test_file.cell_names))
        self.assertTrue(names == names_after,
                        "Updated cell names are correct.")

    def test_update_cell_names_from_init(self):
        """
        Update cell names from an init value.
        """
        test_file = os.path.join("test_files", "expression.txt")
        test_file = PortalFiles.ExpressionFile(test_file)
        names = "".join(["CELL_0001,CELL_00010,CELL_00011,",
                         "CELL_00012,CELL_00013,CELL_00014,",
                         "CELL_00015,CELL_0002,CELL_0003,",
                         "CELL_0004,CELL_0005,CELL_0006,",
                         "CELL_0007,CELL_0008,CELL_0009"])
        test_file.update_cell_names()
        test_file.update_cell_names()
        test_file.update_cell_names()
        names_after = ",".join(sorted(test_file.cell_names))
        self.assertTrue(names == names_after,
                        "Updated cell names are correct.")

    def test_deidentify_cells(self):
        """
        Test deidentify file.
        """
        test_file_name = os.path.join("test_files", "expression.txt")
        deid_file = os.path.join("test_files",
                                 "expression"+PortalFiles.c_DEID_POSTFIX+".txt")
        map_file = os.path.join("test_files",
                                "expression"+PortalFiles.c_MAP_POSTFIX+".txt")
        correct_file = os.path.join("test_files",
                                    "expression_deidentifed_correct.txt")
        correct_map = os.path.join("test_files",
                                   "expression_mapping_correct.txt")
        # Remove the test files if the exist
        if(os.path.exists(deid_file)):
            os.remove(deid_file)
        if(os.path.exists(map_file)):
            os.remove(map_file)
        test_file = PortalFiles.ExpressionFile(test_file_name)
        deid_file_name = test_file.deidentify_cell_names()["name"]
        self.assertTrue(files_are_equivalent(file_path_1=deid_file_name,
                                             file_path_2=correct_file) and
                        files_are_equivalent(file_path_1=map_file,
                                             file_path_2=correct_map),
                                             "Can not deidentify file.")

    def test_deidentify_cells_check_created_names(self):
        """
        Test deidentify file. Check to make sure cell
        names are created and passed.
        """
        test_file_name = os.path.join("test_files", "expression.txt")
        deid_file = os.path.join("test_files",
                                 "expression"+PortalFiles.c_DEID_POSTFIX+".txt")
        map_file = os.path.join("test_files",
                                "expression"+PortalFiles.c_MAP_POSTFIX+".txt")
        cell_mappings_truth = sorted(["CELL_0001:cell_0", "CELL_0002:cell_1", "CELL_0003:cell_2",
                               "CELL_0004:cell_3", "CELL_0005:cell_4", "CELL_0006:cell_5",
                               "CELL_0007:cell_6", "CELL_0008:cell_7", "CELL_0009:cell_8",
                               "CELL_00010:cell_9", "CELL_00011:cell_10", "CELL_00012:cell_11",
                               "CELL_00013:cell_12", "CELL_00014:cell_13", "CELL_00015:cell_14"])
        cell_mappings_truth = ",".join(cell_mappings_truth)
        # Remove the test files if the exist
        if(os.path.exists(deid_file)):
            os.remove(deid_file)
        if(os.path.exists(map_file)):
            os.remove(map_file)
        test_file = PortalFiles.ExpressionFile(test_file_name)
        deid_info = test_file.deidentify_cell_names()
        deid_file_mapping = deid_info["mapping"]
        cell_mappings = []
        for sorted_key in deid_file_mapping.keys():
            cell_mappings.append(str(sorted_key)+":"+str(deid_file_mapping[sorted_key]))
        cell_mappings = ",".join(sorted(cell_mappings))
        self.assertTrue(cell_mappings == cell_mappings_truth,
                        "Returned mappings were not expected.="+cell_mappings)

    def test_deidentify_cells_precreated_names(self):
        """
        Test deidentify file with cell already made.
        """
        test_file_name = os.path.join("test_files", "expression.txt")
        deid_file = os.path.join("test_files",
                                 "expression"+PortalFiles.c_DEID_POSTFIX+".txt")
        map_file = os.path.join("test_files",
                                "expression"+PortalFiles.c_MAP_POSTFIX+".txt")
        correct_file = os.path.join("test_files",
                                    "expression_deidentifed_precreated_correct.txt")
        correct_map = os.path.join("test_files",
                                   "expression_mapping_precreated_correct.txt")
        # Remove the test files if the exist
        if(os.path.exists(deid_file)):
            os.remove(deid_file)
        if(os.path.exists(map_file)):
            os.remove(map_file)
        test_file = PortalFiles.ExpressionFile(test_file_name)
        names = dict(zip(test_file.cell_names, [str(i) for i in range(len(test_file.cell_names))]))
        deid_file_name = test_file.deidentify_cell_names(cell_names_change=names)["name"]
        self.assertTrue(files_are_equivalent(file_path_1=deid_file_name,
                                             file_path_2=correct_file) and
                        files_are_equivalent(file_path_1=map_file,
                                             file_path_2=correct_map),
                                             "Can not deidentify file.")

    def test_deidentify_cells_for_existing_files(self):
        """
        Test deidentify file but with the files that are to be made already
        there so an error should occur.
        """
        test_file_name = os.path.join("test_files", "expression.txt")
        deid_file = os.path.join("test_files",
                                 "expression"+PortalFiles.c_DEID_POSTFIX+".txt")
        map_file = os.path.join("test_files",
                                "expression"+PortalFiles.c_MAP_POSTFIX+".txt")
        correct_file = os.path.join("test_files",
                                    "expression_deidentifed_correct.txt")
        correct_map = os.path.join("test_files",
                                   "expression_mapping_correct.txt")
        # Make sure the files to be created exist so an error will occur
        if(not os.path.exists(deid_file)):
            with(open(deid_file, 'w')) as pre_exist_file:
                pre_exist_file.write(["    "])
        if(not os.path.exists(map_file)):
            with(open(map_file, 'w')) as pre_exist_file:
                pre_exist_file.write(["    "])
        test_file = PortalFiles.ExpressionFile(test_file_name)
        deid_file_name = test_file.deidentify_cell_names()
        self.assertFalse((not deid_file_name is None) and
                          not files_are_equivalent(file_path_1=deid_file_name,
                                                   file_path_2=correct_file) and
                          not files_are_equivalent(file_path_1=map_file,
                                                   file_path_2=correct_map),
                          "Deidentify should not occur when the files being made exist.")

    def test_get_gene_names(self):
        """
        Confirm that genes names are returned correctly from am good file.
        """
        expected_gene_names = ["Itm2a", "Sergef", "Chil5", "Fam109a",
                               "Dhx9", "Ssu72", "Olfr1018", "Fam71e2",
                               "Eif2b2", "1700061E18Rik", "Mks1",
                               "Gm12000", "Hebp2", "Gm14444", "Vps28",
                               "Setd6", "Gstm2", "Spn-ps", "Psma4"]
        test_file_name = os.path.join("test_files", "expression.txt")
        test_file = PortalFiles.ExpressionFile(test_file_name)
        str_truth = ",".join(sorted(expected_gene_names))
        str_received = ",".join(sorted(test_file.get_gene_names()))
        self.assertTrue(str_truth == str_received,
                        "Did not receive the expected gene names.")

class MetadataFileTester(unittest.TestCase):
    """
    Tests the Metadata File object.
    """

    def test_init(self):
        """
        Make sure init can occur
        """
        test_file = os.path.join("test_files", "metadata.txt")
        PortalFiles.MetadataFile(test_file)
        self.assertTrue(True, 'Metadata file can init.')

    def test_check_header_correct(self):
        """
        Check the header is called correct when it is.
        """
        test_file_name = os.path.join("test_files", "metadata.txt")
        test_file = PortalFiles.MetadataFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_header()
        self.assertTrue(not test_file.file_has_error,
                        "Should not have reached an error state.")

    def test_check_header_incorrect_00(self):
        """
        Check the header is called incorrect when element 00 is wrong.
        """
        test_file_name = os.path.join("test_files",
                                      "metadata_bad_header.txt")
        test_file = PortalFiles.MetadataFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_header()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_header_incorrect_element_count(self):
        """
        Check the header is called incorrect when 00 is blank.
        """
        test_file_name = os.path.join("test_files",
                                      "metadata_bad_header_2.txt")
        test_file = PortalFiles.MetadataFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_header()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_header_duplicate_id(self):
        """
        Check the header is called incorrect when a column is duplicate.
        """
        test_file_name = os.path.join("test_files",
                                      "metadata_bad_header_dup.txt")
        test_file = PortalFiles.MetadataFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_header()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_header_no_data_column(self):
        """
        Check the header is called incorrect when there are only id columns.
        """
        test_file_name = os.path.join("test_files",
                                      "metadata_bad_no_data.txt")
        test_file = PortalFiles.MetadataFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_header()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_type_row_correct(self):
        """
        Check the type row is called correct when it is.
        """
        test_file_name = os.path.join("test_files", "metadata.txt")
        test_file = PortalFiles.MetadataFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_type_row()
        self.assertTrue(not test_file.file_has_error,
                        "Should not have reached an error state.")

    def test_check_type_row_bad_type(self):
        """
        Check the type row is called error when one of the types are incorrect.
        """
        test_file_name = os.path.join("test_files", "metadata_bad_type.txt")
        test_file = PortalFiles.MetadataFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_type_row()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_type_row_bad_type_id(self):
        """
        Check the type row is called error when the type id is not correct
        """
        test_file_name = os.path.join("test_files", "metadata_bad_type_id.txt")
        test_file = PortalFiles.MetadataFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_type_row()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_type_row_bad_row_length(self):
        """
        Check the type row is called error when the type row is a wrong length
        """
        test_file_name = os.path.join("test_files", "metadata_bad_type_row_length.txt")
        test_file = PortalFiles.MetadataFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_type_row()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_body_correct(self):
        """ 
        Check the body is called correct when it is
        """ 
        test_file_name = os.path.join("test_files",
                                      "metadata.txt")
        test_file = PortalFiles.MetadataFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_body()
        self.assertTrue(not test_file.file_has_error,
                        "Should have not reached an error state.")

    def test_check_body_incorrect_1(self):
        """ 
        Check the body is called incorrect when it has a missing element.
        """ 
        test_file_name = os.path.join("test_files",
                                      "metadata_bad_body_1.txt")
        test_file = PortalFiles.MetadataFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_body()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_body_incorrect_2(self):
        """ 
        Check the body is called incorrect when it has a wrong type element.
        """ 
        test_file_name = os.path.join("test_files",
                                      "metadata_bad_body_2.txt")
        test_file = PortalFiles.MetadataFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_body()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_update_cell_names_from_none(self):
        """
        Update cell names from a None value.
        """
        test_file = os.path.join("test_files", "metadata.txt")
        test_file = PortalFiles.MetadataFile(test_file)
        names = ",".join(sorted(test_file.cell_names))
        test_file.cell_names = None
        test_file.update_cell_names()
        names_after = ",".join(sorted(test_file.cell_names))
        self.assertTrue(names == names_after,
                        "Updated cell names are correct.")

    def test_update_cell_names_from_init(self):
        """
        Update cell names from an init value.
        """
        test_file = os.path.join("test_files", "metadata.txt")
        test_file = PortalFiles.MetadataFile(test_file)
        names = "".join(["CELL_0001,CELL_00010,CELL_00011,",
                         "CELL_00012,CELL_00013,CELL_00014,",
                         "CELL_00015,CELL_0002,CELL_0003,",
                         "CELL_0004,CELL_0005,CELL_0006,",
                         "CELL_0007,CELL_0008,CELL_0009"])
        test_file.update_cell_names()
        test_file.update_cell_names()
        test_file.update_cell_names()
        names_after = ",".join(sorted(test_file.cell_names))
        self.assertTrue(names == names_after,
                        "Updated cell names are correct.")

    def test_deidentify_cells(self):
        """
        Test deidentify file.
        """
        test_file_name = os.path.join("test_files", "metadata.txt")
        deid_file = os.path.join("test_files",
                                 "metadata"+PortalFiles.c_DEID_POSTFIX+".txt")
        map_file = os.path.join("test_files",
                                "metadata"+PortalFiles.c_MAP_POSTFIX+".txt")
        correct_file = os.path.join("test_files",
                                    "metadata_deidentifed_correct.txt")
        correct_map = os.path.join("test_files",
                                   "metadata_mapping_correct.txt")
        # Remove the test files if the exist
        if(os.path.exists(deid_file)):
            os.remove(deid_file)
        if(os.path.exists(map_file)):
            os.remove(map_file)
        test_file = PortalFiles.MetadataFile(test_file_name)
        deid_file_name = test_file.deidentify_cell_names()["name"]
        self.assertTrue(files_are_equivalent(file_path_1=deid_file_name,
                                             file_path_2=correct_file) and
                        files_are_equivalent(file_path_1=map_file,
                                             file_path_2=correct_map),
                                             "Can not deidentify file.")

    def test_deidentify_cells_check_created_names(self):
        """
        Test deidentify file. Check to make sure cell
        names are created and passed.
        """
        test_file_name = os.path.join("test_files", "metadata.txt")
        deid_file = os.path.join("test_files",
                                 "metadata"+PortalFiles.c_DEID_POSTFIX+".txt")
        map_file = os.path.join("test_files",
                                "metadata"+PortalFiles.c_MAP_POSTFIX+".txt")
        cell_mappings_truth = sorted(["CELL_0001:cell_0", "CELL_0002:cell_1", "CELL_0003:cell_2",
                               "CELL_0004:cell_3", "CELL_0005:cell_4", "CELL_0006:cell_5",
                               "CELL_0007:cell_6", "CELL_0008:cell_7", "CELL_0009:cell_8",
                               "CELL_00010:cell_9", "CELL_00011:cell_10", "CELL_00012:cell_11",
                               "CELL_00013:cell_12", "CELL_00014:cell_13", "CELL_00015:cell_14"])
        cell_mappings_truth = ",".join(cell_mappings_truth)
        # Remove the test files if the exist
        if(os.path.exists(deid_file)):
            os.remove(deid_file)
        if(os.path.exists(map_file)):
            os.remove(map_file)
        test_file = PortalFiles.MetadataFile(test_file_name)
        deid_info = test_file.deidentify_cell_names()
        deid_file_mapping = deid_info["mapping"]
        cell_mappings = []
        for sorted_key in deid_file_mapping.keys():
            cell_mappings.append(str(sorted_key)+":"+str(deid_file_mapping[sorted_key]))
        cell_mappings = ",".join(sorted(cell_mappings))
        self.assertTrue(cell_mappings == cell_mappings_truth,
                        "Returned mappings were not expected.="+cell_mappings)

    def test_deidentify_cells_precreated_names(self):
        """
        Test deidentify file with cell already made.
        """
        test_file_name = os.path.join("test_files", "metadata.txt")
        deid_file = os.path.join("test_files",
                                 "metadata"+PortalFiles.c_DEID_POSTFIX+".txt")
        map_file = os.path.join("test_files",
                                "metadata"+PortalFiles.c_MAP_POSTFIX+".txt")
        correct_file = os.path.join("test_files",
                                    "metadata_deidentifed_precreated_correct.txt")
        correct_map = os.path.join("test_files",
                                   "metadata_mapping_precreated_correct.txt")
        # Remove the test files if the exist
        if(os.path.exists(deid_file)):
            os.remove(deid_file)
        if(os.path.exists(map_file)):
            os.remove(map_file)
        test_file = PortalFiles.MetadataFile(test_file_name)
        names = dict(zip(test_file.cell_names, [str(i) for i in range(len(test_file.cell_names))]))
        deid_file_name = test_file.deidentify_cell_names(cell_names_change=names)["name"]
        self.assertTrue(files_are_equivalent(file_path_1=deid_file_name,
                                             file_path_2=correct_file) and
                        files_are_equivalent(file_path_1=map_file,
                                             file_path_2=correct_map),
                                             "Can not deidentify file.")

    def test_deidentify_cells_for_existing_files(self):
        """
        Test deidentify file but with the files that are to be made already
        there so an error should occur.
        """
        test_file_name = os.path.join("test_files", "metadata.txt")
        deid_file = os.path.join("test_files",
                                 "metadata"+PortalFiles.c_DEID_POSTFIX+".txt")
        map_file = os.path.join("test_files",
                                "metadata"+PortalFiles.c_MAP_POSTFIX+".txt")
        correct_file = os.path.join("test_files",
                                    "metadata_deidentifed_correct.txt")
        correct_map = os.path.join("test_files",
                                   "metadata_mapping_correct.txt")
        # Make sure the files to be created exist so an error will occur
        if(not os.path.exists(deid_file)):
            with(open(deid_file, 'w')) as pre_exist_file:
                pre_exist_file.write(["    "])
        if(not os.path.exists(map_file)):
            with(open(map_file, 'w')) as pre_exist_file:
                pre_exist_file.write(["    "])
        test_file = PortalFiles.MetadataFile(test_file_name)
        deid_file_name = test_file.deidentify_cell_names()
        self.assertFalse((not deid_file_name is None) and
                          not files_are_equivalent(file_path_1=deid_file_name,
                                                   file_path_2=correct_file) and
                          not files_are_equivalent(file_path_1=map_file,
                                                   file_path_2=correct_map),
                          "Deidentify should not occur when the files being made exist.")

    def test_get_labels_correct(self):
        """ 
        Check to make sure labels are returned correctly with a good file
        """ 
        test_file_name = os.path.join("test_files",
                                      "metadata.txt")
        truth = ["CLST_A", "CLST_B", "CLST_C",
                 "CLST_A_1", "CLST_A_2", "CLST_B_1",
                 "CLST_B_2", "CLST_C_1", "CLST_C_2"]
        test_file = PortalFiles.MetadataFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        received_labels = test_file.get_labels()
        truth_str = ",".join(sorted(truth))
        received_str = ",".join(sorted(received_labels))
        self.assertTrue(truth_str == received_str,
                        "Did not receive the expected labels.")


class GeneListFileTester(unittest.TestCase):
    """
    Tests the Gene list file object.
    """

    def test_get_gene_names(self):
        """
        Confirm that genes names are returned correctly from am good file.
        """
        expected_gene_names = ["Itm2a", "Sergef", "Chil5", "Fam109a",
                               "Dhx9", "Ssu72", "Olfr1018", "Fam71e2",
                               "Eif2b2", "1700061E18Rik", "Mks1",
                               "Gm12000", "Hebp2", "Gm14444", "Vps28",
                               "Setd6", "Gstm2", "Spn-ps", "Psma4"]
        test_file_name = os.path.join("test_files", "gene_list.txt")
        test_file = PortalFiles.GeneListFile(test_file_name)
        str_truth = ",".join(sorted(expected_gene_names))
        str_received = ",".join(sorted(test_file.get_gene_names()))
        self.assertTrue(str_truth == str_received,
                        "Did not receive the expected gene names.")

    def test_check_header_correct(self):
        """
        Check the header is called correct when it is.
        """
        test_file_name = os.path.join("test_files", "gene_list.txt")
        test_file = PortalFiles.GeneListFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_header()
        self.assertTrue(not test_file.file_has_error,
                        "Should not have reached an error state.")

    def test_check_header_bad_00(self):
        """
        Check the header is called error when the 00 element is wrong.
        """
        test_file_name = os.path.join("test_files", "gene_list_bad_header.txt")
        test_file = PortalFiles.GeneListFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_header()
        self.assertTrue(test_file.file_has_error,
                        "Should not have reached an error state.")

    def test_check_body_correct(self):
        """ 
        Check the body is called correct when it is correct.
        """ 
        test_file_name = os.path.join("test_files",
                                      "gene_list.txt")
        test_file = PortalFiles.GeneListFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_body()
        self.assertTrue(not test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_body_incorrect_type(self):
        """ 
        Check the body is called correct when it is correct.
        """ 
        test_file_name = os.path.join("test_files",
                                      "gene_list_bad_type.txt")
        test_file = PortalFiles.GeneListFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_body()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_body_incorrect_value_empty(self):
        """ 
        Check the body is called correct when one value is empty.
        """ 
        test_file_name = os.path.join("test_files",
                                      "gene_list_bad_empty_value.txt")
        test_file = PortalFiles.GeneListFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_body()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_check_body_incorrect_row_length(self):
        """ 
        Check the body is called correct when one row is too long.
        """ 
        test_file_name = os.path.join("test_files",
                                      "gene_list_bad_row_length.txt")
        test_file = PortalFiles.GeneListFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.check_body()
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_deidentify_cells(self):
        """
        Test deidentify file.
        """
        test_file_name = os.path.join("test_files", "gene_list.txt")
        test_file = PortalFiles.GeneListFile(test_file_name)
        deid_result = test_file.deidentify_cell_names()
        self.assertTrue((deid_result["name"] is None) and
                        (deid_result["mapping"] is None), 
                        "Should not have attempted to deid file, there are no cell names.")

    def test_compare_gene_names_for_good(self):
        """ 
        Check compare gene names for a good file.
        """ 
        test_file_name = os.path.join("test_files",
                                      "gene_list.txt")
        test_expression_file_name = os.path.join("test_files", "expression.txt")
        test_file = PortalFiles.GeneListFile(test_file_name)
        expr_file = PortalFiles.ExpressionFile(test_expression_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.compare_gene_names(expr_file)
        self.assertTrue(not test_file.file_has_error,
                        "Should have reached an error state.")

    def test_compare_gene_names_for_good_2(self):
        """ 
        Check compare gene names for a good file, expression file having more genes then gene list.
        """ 
        test_file_name = os.path.join("test_files",
                                      "gene_list_minus_one.txt")
        test_expression_file_name = os.path.join("test_files", "expression.txt")
        test_file = PortalFiles.GeneListFile(test_file_name)
        expr_file = PortalFiles.ExpressionFile(test_expression_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.compare_gene_names(expr_file)
        self.assertTrue(not test_file.file_has_error,
                        "Should have reached an error state.")

    def test_compare_gene_names_for_none_expression(self):
        """ 
        Check compare gene names for a none expression file.
        """ 
        test_file_name = os.path.join("test_files",
                                      "gene_list.txt")
        test_file = PortalFiles.GeneListFile(test_file_name)
        expr_file = None
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.compare_gene_names(expr_file)
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_compare_gene_names_for_missing_in_expression(self):
        """ 
        Check compare gene names for an expression file missing a gene in the gene list.
        """ 
        test_file_name = os.path.join("test_files",
                                      "gene_list_plus_one.txt")
        test_expression_file_name = os.path.join("test_files", "expression.txt")
        test_file = PortalFiles.GeneListFile(test_file_name)
        expr_file = PortalFiles.ExpressionFile(test_expression_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.compare_gene_names(expr_file)
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_compare_cluster_labels_for_good(self):
        """ 
        Check compare cluster labels for good files
        """ 
        test_file_name = os.path.join("test_files",
                                      "gene_list.txt")
        test_metadata_file_name = os.path.join("test_files", "metadata.txt")
        test_file = PortalFiles.GeneListFile(test_file_name)
        meta_file = PortalFiles.MetadataFile(test_metadata_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.compare_cluster_labels(meta_file)
        self.assertTrue(not test_file.file_has_error,
                        "Should not have reached an error state.")

    def test_compare_cluster_labels_for_missing_label(self):
        """ 
        Check compare cluster labels for a missing
        label that is only found in the gene list file.
        """ 
        test_file_name = os.path.join("test_files",
                                      "gene_list_additional_label.txt")
        test_metadata_file_name = os.path.join("test_files", "metadata.txt")
        test_file = PortalFiles.GeneListFile(test_file_name)
        meta_file = PortalFiles.MetadataFile(test_metadata_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        test_file.compare_cluster_labels(meta_file)
        self.assertTrue(test_file.file_has_error,
                        "Should have reached an error state.")

    def test_get_labels_correct(self):
        """ 
        Check to make sure labels are returned correctly with a good file
        """ 
        test_file_name = os.path.join("test_files",
                                      "gene_list.txt")
        truth = ["CLST_B", "CLST_C", "CLST_A"]
        test_file = PortalFiles.GeneListFile(test_file_name)
        if test_file.file_has_error:
            self.assertTrue(False, "Did not start test with a no error state.")
        received_labels = test_file.get_labels()
        truth_str = ",".join(sorted(truth))
        received_str = ",".join(sorted(received_labels))
        self.assertTrue(truth_str == received_str,
                        "Did not receive the expected labels.")

# Creates a suite of tests
def suite():
    loader = unittest.TestLoader()
    tests = loader.loadTestsFromTestCase(CoordinatesFileTester)
    tests.addTests(loader.loadTestsFromTestCase(ExpressionFileTester))
    tests.addTests(loader.loadTestsFromTestCase(MetadataFileTester))
    tests.addTests(loader.loadTestsFromTestCase(GeneListFileTester))
    return(tests)
