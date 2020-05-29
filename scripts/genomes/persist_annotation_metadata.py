"""Write genome annotation metadata locally, and upload transformed GTFs to GCS
"""

from utils import *

def upload_gtf_product(transformed_gtf, bucket, existing_names):
    """Execute upload of a GTF product to GCS
    """
    source_blob_name = transformed_gtf
    target_blob_name = source_blob_name.replace('output/', '')

    # Check if this file was already uploaded
    if target_blob_name in existing_names:
        print('  Already in bucket, not uploading: ' + target_blob_name)
        return target_blob_name

    # Upload the file
    blob = bucket.blob(target_blob_name)
    blob.upload_from_filename(source_blob_name)
    print('  Uploaded to GCS: ' + target_blob_name)

    return target_blob_name


def upload_ensembl_gtf_products(ensembl_metadata, scp_species, config):
    """Upload position-sorted GTF file and GTF index file to GCS bucket
    """
    print('Uploading Ensembl GTF products')

    vault_path = config['vault_path']
    gcs_bucket = config['gcs_bucket']
    remote_output_dir = config['remote_output_dir']
    remote_prod_dir = config['remote_prod_dir']

    storage_client = get_gcs_storage_client(vault_path)

    # FireCloud workspace for canonical SCP reference data:
    # https://portal.firecloud.org/#workspaces/single-cell-portal/scp-reference-data
    reference_data_bucket = gcs_bucket
    target_folder = remote_output_dir

    bucket = storage_client.get_bucket(reference_data_bucket)

    remote_dev_dir = remote_output_dir
    copy_gcs_data_from_prod_to_dev(bucket, remote_prod_dir, remote_dev_dir)

    existing_names = [blob.name for blob in bucket.list_blobs()]

    for species in scp_species:
        taxid = species[2]
        organism_metadata = ensembl_metadata[taxid]
        transformed_gtfs = organism_metadata['transformed_gtfs']

        for transformed_gtf in transformed_gtfs:
            target_name = upload_gtf_product(transformed_gtf, bucket,
                existing_names)

            # Add GTF product URLs to metadata
            origin = 'https://storage.cloud.google.com'
            gcs_url = origin + reference_data_bucket + target_name
            if gcs_url[-7:] == '.gtf.gz':
                product = 'annotation_url'
            elif gcs_url[-11:] == '.gtf.gz.tbi':
                product = 'annotation_index_url'
            ensembl_metadata[taxid][product] = gcs_url

    return ensembl_metadata


def get_ensembl_gtf_release_date(gtf_path):
    """Parse the release date of the GTF from its header section
    """
    with open(gtf_path) as f:
        # Get first 5 lines, without reading file entirely into memory
        head = [next(f).strip() for x in range(5)]
    try:
        release_date = head[4].split('genebuild-last-updated ')[1]
    except IndexError:
        # Happens with e.g. Drosophila melanogaster genome annotation BDGP6
        print('No annotation release date found for ' + gtf_path)
        return None
    return release_date


def get_ref_file_annot_metadata(organism_metadata):
    """Get name, date, URL and index URL for a genome annotation
    """

    url = organism_metadata['annotation_url']
    index_url = organism_metadata['annotation_url']
    name = 'Ensembl ' + organism_metadata['release']

    gtf_path = organism_metadata['gtf_path'].replace('.gz', '')
    date = get_ensembl_gtf_release_date(gtf_path)

    return [name, date, url, index_url]


def update_meta_row(row, org_metadata, annot_metadata):
    """Update row from species_metadata_reference.tsv with annotation metadata
    """
    date = annot_metadata[1]

    ref_assembly_name = row[3]
    assembly_name = org_metadata['assembly_name']
    ref_assembly_acc = row[4]
    assembly_acc = org_metadata['assembly_accession']

    if ref_assembly_acc == assembly_acc or ref_assembly_name == assembly_name:
        if date is None:
            # If annotation is undated (as with Drosophila), use assembly date
            assembly_date = row[4]
            date = assembly_date
        date_parts = date.split('-')
        if len(date_parts) == 2 and len(date_parts[0]) == 4:
            # YYYY-MM encountered, YYYY-MM-DD needed; use first of month
            date += '-01'
        annot_metadata[1] = date

        new_row = '\t'.join(row + annot_metadata)
    else:
        new_row = '\t'.join(row)

    return new_row


def record_annotation_metadata(ensembl_metadata, scp_species):
    """Write annotation URLs, etc. to species metadata reference TSV file
    """
    new_metadata_ref = []

    ref_file = 'species_metadata_reference.tsv'

    with open(ref_file) as f:
        metadata_ref = [line.strip().split('\t') for line in f.readlines()]

    for species in scp_species:
        taxid = species[2]
        org_metadata = ensembl_metadata[taxid]

        annot_metadata = get_ref_file_annot_metadata(org_metadata)

        for row in metadata_ref[1:]:
            ref_taxid = row[2]
            if taxid == ref_taxid:
                new_row = update_meta_row(row, org_metadata, annot_metadata)
                new_metadata_ref.append(new_row)

    assembly_headers = metadata_ref[0]
    annot_headers = [
        'annotation_name',
        'annotation_release_date',
        'annotation_url',
        'annotation_index_url'
    ]
    header = '\t'.join(assembly_headers + annot_headers) + '\n'
    new_metadata_ref = header + '\n'.join(new_metadata_ref)

    with open(ref_file, 'w') as f:
        f.write(new_metadata_ref)
    print('Wrote annotation metadata to ' + ref_file)