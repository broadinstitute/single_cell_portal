""""
CLI for command line arguments for manage_study.py
"""

import argparse

# Subparser tool names
c_TOOL_LIST_STUDY = "list-studies"
c_TOOL_CLUSTER = "upload-cluster"
c_TOOL_EXPRESSION = "upload-expression"
c_TOOL_METADATA = "upload-metadata"
c_TOOL_PERMISSION = "permission"
c_TOOL_STUDY = "create-study"
c_TOOL_STUDY_EDIT_DESC= "edit-study-description"
c_TOOL_STUDY_GET_ATTR= "get-study-attribute"
c_TOOL_STUDY_GET_EXT= 'get-study-external-resources'
c_TOOL_STUDY_DEL_EXT= 'delete-study-external-resources'
c_TOOL_STUDY_CREATE_EXT = 'create-study-external-resource'

def create_parser():
    args = argparse.ArgumentParser(
        prog='manage_study.py',
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    args.add_argument(
        '--token',
        default=None,
        help='Personal token after logging into Google (OAuth2).  This token is not persisted after the finish of the script.',
    )
    args.add_argument(
        '--dry-run',
        action='store_true',
        help='Walk through and log what would occur, without performing the actions.',
    )
    args.add_argument(
        '--no-validate',
        dest='validate',
        action='store_false',
        help='Do not check file locally before uploading.',
    )
    args.add_argument(
        '--verbose', action='store_true', help='Whether to print debugging information'
    )

    args.add_argument(
        '--environment',
        default='production',
        choices=['development', 'staging', 'production'],
        help='API environment to use',
    )


    # Create tools (subparser)
    subargs = args.add_subparsers(dest = 'command')

    ## List studies subparser
    parser_list_studies = subargs.add_parser(
        c_TOOL_LIST_STUDY,
        help="List studies. \""
        + args.prog
        + " "
        + c_TOOL_LIST_STUDY
        + " -h\" for more details",
    )
    parser_list_studies.add_argument(
        '--summary',
        dest='summarize_list',
        action='store_true',
        help='Do not list, only summarize number of accessible studies',
    )

    ## Create study subparser
    parser_create_studies = subargs.add_parser(
        c_TOOL_STUDY,
        help="Create a study. \""
        + args.prog
        + " "
        + c_TOOL_STUDY
        + " -h\" for more details",
    )
    parser_create_studies.add_argument(
        '--description',
        dest='study_description',
        default="Single Cell Genomics Study",
        help='Short description of the study',
    )
    parser_create_studies.add_argument(
        '--study-name', required=True, help='Short name of the study'
    )
    parser_create_studies.add_argument(
        '--branding',
        default=None,
        help='Portal branding to associate with the study',
    )
    parser_create_studies.add_argument(
        '--billing', default=None, help='Portal billing project to associate with the study'
    )
    parser_create_studies.add_argument(
        '--is-private', action='store_true', help='Whether the study is private'
    )

    # Create edit description subparser
    parser_edit_description = subargs.add_parser(
        c_TOOL_STUDY_EDIT_DESC,
        help="Edit a study description. \""
        + args.prog
        + " "
        + c_TOOL_STUDY_EDIT_DESC
        + " -h\" for more details",
    )
    parser_edit_description.add_argument(
        '--study-name',
        required=True,
        help='Name of the study for which to edit description.',
    )
    parser_edit_description.add_argument(
        '--new-description',
        required=True,
        help='New description of the study to replace current one.',
    )

    parser_edit_description.add_argument(
        '--from-file',
        action='store_true',
        help='If true, assumes new_description argument is name pointing to file containing new_description.',
    )

    parser_edit_description.add_argument(
        '--accept-html',
        action='store_true',
        help='If true, will allow HTML formatting in new description.',
    )

    ## Create study get attribute subparser
    parser_get_attribute = subargs.add_parser(
        c_TOOL_STUDY_GET_ATTR,
        help="Get a study attribute (such as cell_count, etc). \""
        + args.prog
        + " "
        + c_TOOL_STUDY_GET_ATTR
        + " -h\" for more details",
    )
    parser_get_attribute.add_argument(
        '--study-name',
        required=True,
        help='Name of the study from which to get attribute.',
    )
    parser_get_attribute.add_argument(
        '--attribute',
        required=True,
        help='Attribute to return (such as cell_count, etc).',
    )

    ## Create study get external resources subparser
    parser_get_ext_resources = subargs.add_parser(
        c_TOOL_STUDY_GET_EXT,
        help="Get study external resources for a study. \""
        + args.prog
        + " "
        + c_TOOL_STUDY_GET_EXT
        + " -h\" for more details",
    )
    parser_get_ext_resources.add_argument(
        '--study-name',
        required=True,
        help='Name of the study from which to get resources.',
    )

    ## Create study delete external resources subparser
    parser_delete_ext_resources = subargs.add_parser(
        c_TOOL_STUDY_DEL_EXT,
        help="Delete all study external resources for a study. \""
        + args.prog
        + " "
        + c_TOOL_STUDY_DEL_EXT
        + " -h\" for more details",
    )
    parser_delete_ext_resources.add_argument(
        '--study-name',
        required=True,
        help='Name of the study from which to delete resources.',
    )

    ## Create study new external resource subparser
    parser_create_ext_resource = subargs.add_parser(
        c_TOOL_STUDY_CREATE_EXT,
        help="Create a new external resource for a study. \""
        + args.prog
        + " "
        + c_TOOL_STUDY_CREATE_EXT
        + " -h\" for more details",
    )
    parser_create_ext_resource.add_argument(
        '--study-name',
        required=True,
        help='Name of the study to which to add resource.',
    )
    parser_create_ext_resource.add_argument(
        '--title',
        required=True,
        help='Title of resource.',
    )
    parser_create_ext_resource.add_argument(
        '--url',
        required=True,
        help='URL of resource.',
    )
    parser_create_ext_resource.add_argument(
        '--description',
        required=True,
        help='Tooltip description of resource.',
    )
    parser_create_ext_resource.add_argument(
        '--publication-url',
        action='store_true',
        help='Whether resource is publication URL.',
    )
    # TODO: Fix permissions subparser (SCP-2024)
    # ## Permissions subparser
    # parser_permissions = subargs.add_parser(
    #     c_TOOL_PERMISSION,
    #     help="Change user permissions in a study. \""
    #     + args.prog
    #     + " "
    #     + c_TOOL_PERMISSION
    #     + " -h\" for more details",
    # )
    # parser_permissions.add_argument(
    #     '--email',
    #     dest='email',
    #     required=True,
    #     default='Single Cell Genomics Study',
    #     help='User email to update study permission.',
    # )
    # parser_permissions.add_argument(
    #     '--study-name', dest='study_name', required=True, help='Short name of the study.'
    # )
    # parser_permissions.add_argument(
    #     '--access',
    #     dest='permission',
    #     choices=scp_api.c_PERMISSIONS,
    #     required=True,
    #     help='Access to give the user.  Must be one of the following values: '
    #     + " ".join(scp_api.c_PERMISSIONS),
    # )

    ## Create cluster file upload subparser
    parser_upload_cluster = subargs.add_parser(
        c_TOOL_CLUSTER,
        help="Upload a cluster file. \""
        + args.prog
        + " "
        + c_TOOL_CLUSTER
        + " -h\" for more details",
    )
    parser_upload_cluster.add_argument(
        '--file', dest='cluster_file', required=True, help='Cluster file to load.'
    )
    parser_upload_cluster.add_argument(
        '--study-name',
        required=True,
        help='Name of the study to add the file.',
    )
    parser_upload_cluster.add_argument(
        '--description',
        default="Coordinates and optional metadata to visualize clusters.",
        help='Text describing the cluster file.',
    )
    parser_upload_cluster.add_argument(
        '--cluster-name',
        required=True,
        help='Name of the clustering that will be used to refer to the plot.',
    )
    parser_upload_cluster.add_argument(
        '--x', dest='x_label', default=None, help='X axis label (test).'
    )
    parser_upload_cluster.add_argument(
        '--y', dest='y_label', default=None, help='Y axis label (test).'
    )
    parser_upload_cluster.add_argument(
        '--z', dest='z_label', default=None, help='Z axis label (test).'
    )

    ## Create expression file upload subparser
    parser_upload_expression = subargs.add_parser(
        c_TOOL_EXPRESSION,
        help="Upload a gene expression matrix file. \""
        + args.prog
        + " "
        + c_TOOL_EXPRESSION
        + " -h\" for more details",
    )
    parser_upload_expression.add_argument(
        '--file', dest='expression_file', required=True, help='Expression file to load.'
    )
    parser_upload_expression.add_argument(
        '--study-name',
        required=True,
        help='Name of the study to add the file.',
    )
    parser_upload_expression.add_argument(
        '--description',
        default='Gene expression in cells',
        help='Text describing the gene expression matrix file.',
    )
    parser_upload_expression.add_argument(
        '--species',
        required=True,
        help='Species from which the data is generated.',
    )
    parser_upload_expression.add_argument(
        '--genome',
        required=True,
        help='Genome assembly used to generate the data.',
    )
    # TODO: Add upstream support for this in SCP RESI API
    # parser_upload_expression.add_argument(
    #     '--axis_label', dest='axis_label',
    #     default='',
    #     help=''
    # )

    ## Create metadata file upload subparser
    parser_upload_metadata = subargs.add_parser(
        c_TOOL_METADATA,
        help="Upload a metadata file. \""
        + args.prog
        + " "
        + c_TOOL_METADATA
        + " -h\" for more details",
    )
    parser_upload_metadata.add_argument(
        '--file', dest='metadata_file', required=True, help='Metadata file to load.'
    )
    parser_upload_metadata.add_argument(
        '--use-convention',
        help='Whether to use metadata convention: validates against standard vocabularies, and will enable faceted search on this data',
        action='store_true'
    )
    parser_upload_metadata.add_argument(
        '--validate-against-convention',
        help='Validates against standard vocabularies prior to upload',
        action='store_true'
    )
    parser_upload_metadata.add_argument(
        '--study-name',
        required=True,
        help='Name of the study to add the file.',
    )
    parser_upload_metadata.add_argument(
        '--description',
        default='',
        help='Text describing the metadata file.',
    )
    return args
