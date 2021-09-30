#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Command-line interface for managing studies in Single Cell Portal (SCP)

DESCRIPTION
This CLI exposes SCP functionality via several subparsers, e.g. "list-study",
"upload-study".  You can invoke this functionality by passing a subparser name
into your command-line call, as shown in the EXAMPLES section below.

PREREQUISITES
To use this tool, you must have Google Cloud SDK installed and initialized.
See https://cloud.google.com/sdk/docs/ for details.

See https://github.com/broadinstitute/single_cell_portal#convenience-scripts
for other requirements.

EXAMPLES
# First, sign in and assign access token
gcloud auth login
ACCESS_TOKEN=`gcloud auth print-access-token`

# List studies in SCP
python manage_study.py list-studies

# Get number of studies in SCP, using token to bypass browser log-in
python manage_study.py --token=$ACCESS_TOKEN list-studies --summary

# Get help for "create-study"
python manage_study.py create-study --help

# Create a study named "CLI test"
python3 manage_study.py --token=$ACCESS_TOKEN create-study --study-name "CLI test"

# Upload an expression matrix
python3 manage_study.py --token=$ACCESS_TOKEN upload-expression --file ../demo_data/expression_example.txt --study-name "CLI test" --species "human" --genome "GRCh38"

# Upload a metadata file (without validating against the metadata convention)
python3 manage_study.py --token=$ACCESS_TOKEN upload-metadata --study-name "CLI test" --file ../demo_data/metadata_example.txt

# Upload a metadata file with metadata convention validation prior to upload
python3 manage_study.py upload-metadata --study-name "CLI test" --file ../../scp-ingest-pipeline/tests/data/valid_no_array_v2.0.0.tsv --use-convention

# Upload a cluster file
python3 manage_study.py --token=$ACCESS_TOKEN upload-cluster --study-name "${STUDY_NAME}" --file ../demo_data/cluster_example.txt  --cluster-name 'Test cluster' --description test

# Edit study description
python3 manage_study.py --token-$ACCESS_TOKEN edit-study-description --study-name "${STUDY_NAME}" --new-description "This is a test."

# Create an external resource
python3 manage_study.py --token-$ACCESS_TOKEN create-study-external-resource --study-name "${STUDY_NAME}" --title "External_Link" \
--url "https://singlecell.broadinstitute.org/single_cell" --description "This sends you home."

# Print a study attribute (eg. cell_count)
python3 manage_study.py --token-$ACCESS_TOKEN get-study-attribute --study-name "${STUDY_NAME}" --attribute cell_count

# Avoid sending a user-agent string while obtaining the number of studies in SCP
python manage_study.py --no-user-agent --token=$ACCESS_TOKEN list-studies --summary

EXIT CODES
# TODO: replace with python error handling and logging (SCP-2790)
79  incompatible scp-ingest-pipeline package version detected
80  exit-file-already-exists-in-study-bucket
81  exit-file-not-found-in-study-bucket
82  exit-failed-to-gsutil-delete-file
83  exit-uploaded-file-deleted
84  exit-no-file-cleanup-needed
85  exit-file-not-found-in-remote-bucket
"""

import argparse
import json
import os
from bson.objectid import ObjectId
import pkg_resources

from google.cloud import storage
from ingest.ingest_pipeline import IngestPipeline
from ingest.cell_metadata import CellMetadata
from ingest.validation.validate_metadata import (
    report_issues,
    serialize_issues,
    exit_if_errors,
    validate_input_metadata,
)

try:
    # Used when importing internally and in tests
    import Commandline
    import scp_api
    from cli_parser import *
except ImportError:
    # Used when importing as external package
    from . import Commandline
    from . import scp_api
    from .cli_parser import *

env_origin_map = {
    "development": "https://localhost",
    "staging": "https://singlecell-staging.broadinstitute.org",
    "production": "https://singlecell.broadinstitute.org",
}


def get_api_base(parsed_args):
    return env_origin_map[parsed_args.environment] + "/single_cell/api/v1/"


def manage_call_return(call_return, verbose=False):
    """
    Accesses the error codes in the underlying library and check the return code.

    :param call_return: Dict returned from scp_api call with REST call return info
    :return: No return will exit on error
    """
    # Print error code and describe code then exit if not success
    if verbose:
        print("HTTP status code = " + str(call_return[scp_api.c_CODE_RET_KEY]))
        print(
            scp_api.SCPAPIManager.describe_status_code(
                call_return[scp_api.c_CODE_RET_KEY]
            )
        )
    if not call_return[scp_api.c_SUCCESS_RET_KEY]:
        exit(call_return[scp_api.c_CODE_RET_KEY])


def succeeded(ret):
    """Whether request succeeded"""
    # 2xx, e.g. 200 or 204, means success
    return str(ret["response"].status_code)[0] == "2"


def login(parsed_args, manager=None, dry_run=False, api_base=None, verbose=False):
    """
    Login to authorize credentials.

    :param manager: API Manager
    :param dry_run: If true, will do a dry run with no actual execution of functionality.
    :return:
    """
    if manager is None:
        manager = scp_api.SCPAPIManager(verbose=verbose)
        if parsed_args.user_agent:
            user_agent = get_user_agent()
            manager.login(
                token=parsed_args.token,
                dry_run=dry_run,
                api_base=api_base,
                user_agent=user_agent,
            )
        else:
            manager.login(token=parsed_args.token, dry_run=dry_run, api_base=api_base)
    return manager


def get_user_agent():
    """Generate User-Agent string to reflect locally installed package versions"""
    try:
        ingest_pkg_version = pkg_resources.get_distribution(
            "scp-ingest-pipeline"
        ).version
    except pkg_resources.DistributionNotFound:
        ingest_pkg_version = None
    try:
        portal_pkg_version = pkg_resources.get_distribution(
            "single_cell_portal"
        ).version
    except pkg_resources.DistributionNotFound:
        portal_pkg_version = None
    user_agent = f"single-cell-portal/{portal_pkg_version} (manage-study) scp-ingest-pipeline/{ingest_pkg_version} (ingest_pipeline.py)"
    return user_agent


def download_from_bucket(file_path):
    """Downloads file from Google Cloud Storage bucket"""

    path_segments = file_path[5:].split("/")

    storage_client = storage.Client()
    bucket_name = path_segments[0]
    bucket = storage_client.get_bucket(bucket_name)
    source = "/".join(path_segments[1:])

    blob = bucket.blob(source)
    destination = "/tmp/" + source.replace("/", "%2f")
    blob.download_to_filename(destination)
    print(f"{file_path} downloaded to {destination}.")

    return destination


def validate_metadata_file(parsed_args, connection):
    metadata_path = parsed_args.metadata_file
    study_name = parsed_args.study_name
    dry_run = parsed_args.dry_run
    verbose = parsed_args.verbose
    study_accession_res = connection.get_study_attribute(
        study_name=study_name, attribute="accession", dry_run=dry_run
    )
    # Needed dummy values for CellMetadata
    study_file = ObjectId("addedfeed000000000000000")
    study_file_id = ObjectId("addedfeed000000000000001")
    if succeeded(study_accession_res):
        if verbose:
            print(f"Study accession {study_accession_res} retrieved for {study_name}")
        study_accession = study_accession_res.get("study_attribute")
        metadata = CellMetadata(
            metadata_path,
            study_file,
            study_file_id,
            study_accession=str(study_accession),
        )
        convention_res = connection.do_get(
            command=get_api_base(parsed_args)
            + "metadata_schemas/alexandria_convention/latest/json",
            dry_run=dry_run,
        )
        if succeeded(convention_res):
            if verbose:
                print(f"Retreieved file for latest metdata convention")
            convention = convention_res["response"].json()
            validate_against_convention = True
            metadata.preprocess(validate_against_convention)
            metadata.validate(validate_against_convention)
            if not conforms_to_metadata_convention(self.cell_metadata):
                return 1


def confirm(question):
    while True:
        answer = input(question + " (y/n): ").lower().strip()
        if answer in ("y", "yes", "n", "no"):
            return answer in ("y", "yes")


def main():
    parsed_args = create_parser().parse_args()
    if parsed_args.verbose:
        print("Args----")
        print(vars(parsed_args))
        print("-----Args")

    verbose = parsed_args.verbose

    origin = env_origin_map[parsed_args.environment]
    api_base = origin + "/single_cell/api/v1/"

    # Login connection
    connection = login(
        parsed_args,
        manager=None,
        dry_run=parsed_args.dry_run,
        api_base=api_base,
        verbose=verbose,
    )

    ## Handle list studies
    if hasattr(parsed_args, "summarize_list"):
        if verbose:
            print("START LIST STUDIES")
        ret = connection.get_studies(dry_run=parsed_args.dry_run)
        manage_call_return(ret)
        print(
            "You have access to "
            + str(len(ret[scp_api.c_STUDIES_RET_KEY]))
            + " studies."
        )
        if not parsed_args.summarize_list:
            print(os.linesep.join(ret[scp_api.c_STUDIES_RET_KEY]))

    ## Create new study
    if hasattr(parsed_args, "study_description") and not parsed_args.study_name is None:
        if verbose:
            print("START CREATE STUDY")
        is_public = not parsed_args.is_private
        ret = connection.create_study(
            study_name=parsed_args.study_name,
            study_description=parsed_args.study_description,
            branding=parsed_args.branding,
            billing=parsed_args.billing,
            is_public=is_public,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret)
        if succeeded(ret):
            print("Created study")

    ## Get a study attribute
    if parsed_args.command == c_TOOL_STUDY_GET_ATTR:
        if verbose:
            print("STARTING GET ATTRIBUTE")
        ret = connection.get_study_attribute(
            study_name=parsed_args.study_name,
            attribute=parsed_args.attribute,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret)
        print("Study {}:".format(parsed_args.attribute))
        print(ret[scp_api.c_ATTR_RET_KEY])

    ## Edit a study description
    if parsed_args.command == c_TOOL_STUDY_EDIT_DESC:
        if verbose:
            print("STARTING EDIT DESCRIPTION")

        if parsed_args.from_file:
            with open(parsed_args.new_description, "r") as d_file:
                new_description = d_file.read()
        else:
            new_description = parsed_args.new_description

        ret = connection.edit_study_description(
            study_name=parsed_args.study_name,
            new_description=new_description,
            accept_html=parsed_args.accept_html,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret)
        if succeeded(ret):
            print("Updated study description")

    ## Get all external resources from a study
    if parsed_args.command == c_TOOL_STUDY_GET_EXT:
        if verbose:
            print("STARTING GET EXTERNAL RESOURCES")
        ret = connection.get_study_external_resources(
            study_name=parsed_args.study_name,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret, verbose)
        print("Study external resources: \n")
        # Returns in dict format -- table format might be better
        print(ret[scp_api.c_EXT_RET_KEY])

    ## Delete all external resources from a study
    if parsed_args.command == c_TOOL_STUDY_DEL_EXT:
        if verbose:
            print("STARTING DELETE EXTERNAL RESOURCES")

        # first get all external resource ids
        ret = connection.get_study_external_resources(
            study_name=parsed_args.study_name,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret, verbose)
        ext_ids = [res["_id"]["$oid"] for res in ret["external_resources"]]
        if not ext_ids:
            print("No external resources associated with study.")
            exit()
        # confirm deletion with user
        confirmed = confirm(
            "Delete {} external resources associated ".format(len(ext_ids))
            + "with study {}?".format(parsed_args.study_name)
        )
        if confirmed:
            if verbose:
                print("Will continue deleting resources.")
            for ext_id in ext_ids:
                ret = connection.delete_study_external_resource(
                    study_name=parsed_args.study_name,
                    resource_id=ext_id,
                    dry_run=parsed_args.dry_run,
                )
                manage_call_return(ret, verbose)
            print("Deleted all external resources")

    ## Create new external resource for a study
    if parsed_args.command == c_TOOL_STUDY_CREATE_EXT:
        if verbose:
            print("STARTING CREATE EXTERNAL RESOURCE")
        ret = connection.create_study_external_resource(
            study_name=parsed_args.study_name,
            title=parsed_args.title,
            url=parsed_args.url,
            description=parsed_args.description,
            publication_url=parsed_args.publication_url,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret, verbose)
        if succeeded(ret):
            print("Created external resource")

    ## Share with user
    if hasattr(parsed_args, "permission"):
        if verbose:
            print("START SET PERMISSION")
        ret = connection.set_permission(
            study_name=parsed_args.study_name,
            email=parsed_args.email,
            access=parsed_args.permission,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret)
        if succeeded(ret):
            print("Set permission")

    ## Validate files
    if parsed_args.validate and not hasattr(parsed_args, "summarize_list"):

        if verbose:
            print("START VALIDATE FILES")

        if hasattr(parsed_args, "metadata_file") and parsed_args.use_convention:
            validate_metadata_file(parsed_args, connection)

        # command = ["python3 verify_portal_file.py"]
        #
        # if hasattr(parsed_args, "cluster_file"):
        #     command.extend(["--coordinates-file", parsed_args.cluster_file])
        # if hasattr(parsed_args, "expression_file"):
        #     command.extend(["--expression-files", parsed_args.expression_file])
        # if hasattr(parsed_args, "metadata_file"):
        #     command.extend(["--metadata-file", parsed_args.metadata_file])
        #
        # if parsed_args.dry_run:
        #     print("TESTING:: no command executed."+os.linesep+"Would have executed: " + os.linesep + " ".join(command))
        # else:
        #     valid_code = Commandline.Commandline().func_CMD(" ".join(command))
        #     if verbose: print(valid_code)
        #     if not valid_code:
        #         print("There was an error validating the files, did not upload. Code=" + str(valid_code))
        #         exit(valid_code)

    ## Upload cluster file
    if hasattr(parsed_args, "cluster_file"):
        if verbose:
            print("START UPLOAD CLUSTER FILE")
        connection = login(parsed_args, manager=connection, dry_run=parsed_args.dry_run)
        ret = connection.upload_cluster(
            file=parsed_args.cluster_file,
            study_name=parsed_args.study_name,
            cluster_name=parsed_args.cluster_name,
            description=parsed_args.description,
            x=parsed_args.x_label,
            y=parsed_args.y_label,
            z=parsed_args.z_label,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret)
        if succeeded(ret):
            print("Uploaded and began parse of cluster file")

    ## Upload metadata file
    if hasattr(parsed_args, "metadata_file"):
        connection = login(parsed_args, manager=connection, dry_run=parsed_args.dry_run)
        if verbose:
            print("START UPLOAD METADATA FILE")
            print(f"connection is {connection}")
        ret = connection.upload_metadata(
            file=parsed_args.metadata_file,
            use_convention=parsed_args.use_convention,
            study_name=parsed_args.study_name,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret)
        if succeeded(ret):
            print("Uploaded and began parse of metadata file")

    ## Upload expression file
    if hasattr(parsed_args, "expression_file"):
        if verbose:
            print("START UPLOAD EXPRESSION FILE")
        connection = login(parsed_args, manager=connection, dry_run=parsed_args.dry_run)
        ret = connection.upload_expression_matrix(
            file=parsed_args.expression_file,
            study_name=parsed_args.study_name,
            species=parsed_args.species,
            genome=parsed_args.genome,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret)
        if succeeded(ret):
            print("Uploaded and began parse of expression file")

    ## Upload miscellaneous file
    ### TODO

    ## Validate and Upload and Sort 10X files
    ### TODO

    ## Validate and Upload 10X directory
    ### TODO

    ## Validate and Upload fastqs
    ### TODO

    ## Validate and Upload bams
    ### TODO


if __name__ == "__main__":
    main()
