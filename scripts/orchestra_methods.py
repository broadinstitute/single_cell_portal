#! /usr/bin/env python
"""Python Functions for CellRanger BCL->Fastq->SCP Pipeline
Arguments:
-c command to be run:
    count:
       -id, --sampleId  Id of sample being run
       -cf, --commaFastqs  Comma seperated String with list of fastq directories
       -fs, --fastqs  List of fastq directories
       -E, --expectCells  Number of cells to expect
       -F --forceCells  Force number of cells
       -C, --chemistry  Chemistry of fastqs
       -S, --secondary  Run cellranger secondary analysis
       -tf, --transcriptome  Transcriptome file
       -dfc, --doForceCells  Boolean to use force cells
    mkfastq:
       -b, --bcl  Location of bcl
       -M, --masterCsv  Master Csv file containing maps of information
       -O, --output_directory  List of fastq directories
    parse:
       -M, --masterCsv  Master Csv file containing maps of information
    analysis:
       -M, --masterCsv  Master Csv file containing maps of information
       -hs, --h5s  H5 output files
    filter:
       -M, --masterCsv  Master Csv file containing maps of information
       -p, --paths  Paths to fastq directories
       -S, --sampleIds  help='List of sample names
       -t, --transMap  CSV map of reference names to gsurls

"""
# Imports
import os
from subprocess import call
import xml.etree.ElementTree as ET
import pandas as pd
from subprocess import run
from subprocess import check_output
import sys
import argparse

def cellranger_count(sample_id, transcriptome, comma_fastqs='',fastqs='', expect_cells='', force_cells='', secondary='false', chemistry='threeprime', do_force_cells = ''):
    """Run Cell Ranger count on directory (s) of fastqs.
        Arguments:
        sample_id- name of sample
        transcriptome- path of transcriptome file
        comma_fastqs- comma seperated string of fastq directory gsurls
        fastqs- wdl formatted array of fastqs
        secondary- CellRanger count argument, run Cell Ranger built in analysis
        expect_cells- CellRanger count argument
        force_cells- CellRanger count argument
        do_force_cells- pass force cells to CellRanger?
        chemistry- CellRanger count argument
        Outputs-
        CellRanger Count Files {
            barcodes
            genes
            matrix
            qc
            report
            sorted_bam
            sorted_bam_index
            filtered_gene_h5
            raw_gene_h5
            raw_barcodes
            raw_genes
            raw_matrix
            mol_info_h5
            cloupe
        }
    """
    # download the transcriptome file to directory
    os.mkdir('transcriptome_dir')
    call(['tar', 'xf', transcriptome, '-C', 'transcriptome_dir', '--strip-components', '1'])

    # create a unique list (set) of fastq directories and download them
    dirs = set()
    if comma_fastqs is not '':
        fastqs = comma_fastqs.split(',')
    for fastq, i in enumerate(fastqs):
        # download the fastqs to a unique location and add that location to set
        os.mkdir(str(i))
        call(['gsutil', '-q', '-m', 'cp', '-r', fastq, str(i)])
        os.path.join(str(i), sample_id, '')
        dirs.add(os.path.join(str(i), sample_id, ''))

    # create the cellranger count command and execute it
    call_args = list()
    call_args.append('cellranger')
    call_args.append('count')
    call_args.append('--jobmode=local')
    call_args.append('--transcriptome=transcriptome_dir')
    call_args.append('--sample=' + sample_id)
    call_args.append('--id=results_' + sample_id)
    call_args.append('--fastqs=' + ','.join(dirs))
    if secondary is not 'true':
        call_args.append('--nosecondary')
    if (force_cells is not '') and (do_force_cells is 'true'):
        call_args.append('--force-cells=' + str(force_cells))
    elif expect_cells is not '':
        call_args.append('--expect-cells=' + str(expect_cells))
    if chemistry is not '':
        call_args.append('--chemistry=' + chemistry)
    call(call_args)

def cellranger_mkfastq(bcl, master_csv, output_directory, samples_csv = 'sample.csv'):
    """Run Cell Ranger mkfastq on a single BCL.
       Arguments:
       bcl- gsurl of bcl directory
       masterCsv- Csv File mapping samples, lanes and indices to bcl
       output_directory- gsurl path where fastqs will be outputted too
       Outputs-
       path.txt- fastq output gsurl
       undetermined.txt- undetermined fastq gsurl
    """
    # copy the BCL over 
    call(['gsutil', '-q', '-m', 'cp', '-r', bcl, '.'])
    # Create local fastq output directory
    os.mkdir('fastqs')
    # get the name of the flowcell, need this to know fastq output directory name
    path = bcl
    run = list(filter(None, path.split('/')))[-1]

    # get flowcell
    tree = ET.parse(os.path.join(run, 'RunInfo.xml'))
    root = tree.getroot()
    flowcell = root.find('Run').find('Flowcell').text

    # create the sample lane index csv
    df = pd.read_csv(master_csv, header=0)
    df = df.loc[df['Flowcell'] == path]
    df = df[['Lane','Sample', 'Index']]
    df.to_csv(samples_csv, index=False)

    # run mkfastq command
    call_args = list()
    call_args.append('cellranger')
    call_args.append('mkfastq')
    call_args.append('--run=' + os.path.join(run,''))
    call_args.append('--csv=' + samples_csv)
    call_args.append('--output-dir=fastqs')
    call(call_args)

    # move the fastqs to the output directory
    call(['gsutil', '-q', '-m', 'mv', os.path.join('fastqs', flowcell), output_directory])
    # move and rename the qc summary file to fastq output directory, rename it so it doesn't get rewritten if there are multiple bcls
    call(['gsutil', '-q', '-m', 'mv', os.path.join(flowcell,'outs','qc_summary.json'), os.path.join(output_directory,flowcell + '_qc_summary.json')])
    
    # write the path of fastqs for cromwell
    with open('path.txt', 'w')  as file:
        file.write(os.path.join(output_directory, flowcell, ''))

    # move the undetermined fastqs over to the bucket
    try:
        call(['gsutil', '-q', '-m', 'mv', os.path.join('fastqs', 'Undetermined_*'), os.path.join(output_directory, flowcell + '_Undetermined', '')])
        # write the undetermined fastqs path for cromwell
        with open('undetermined.txt', 'w') as file:
            file.write(os.path.join(output_directory, flowcell + '_Undetermined', ''))
    except:
        print('Unable to move Undetermined to Bucket')
    
    
def orchestra_parse_csv(master_csv):
    """Parse the initial csv input to orchestra.
        Arguments:
        master_csv- Csv File mapping samples, lanes and indices to bcl
        Outputs-
        samples_file- list of samples for scattering
        bcl_file- list of bcl gsurls for scattering
    """
    # Read the master_csv
    df = pd.read_csv(master_csv, header=0)
    # Get unique gsurls of bcls
    bcl_paths = set(df['Flowcell'].tolist())
    # Write the bcls for Cromwell
    with open('bcls.txt', 'w+') as bcl_file:
        for item in bcl_paths:
          bcl_file.write('%s\n' % item)
    # Get unique sample names
    sampleIds = set(df['Sample'].tolist())
    # Write the sample names for Cromwell
    with open('samples.txt', 'w+') as samples_file:
        for item in sampleIds:
          samples_file.write('%s\n' % item)


def orchestra_analysis_csv(master_csv, h5s):
    """Map the initial csv input to CellRanger Count h5 file outputs for analysis WDL.
        Arguments:
        master_csv- Csv File mapping samples, lanes and indices to bcl
        h5s- array of cromwell localized file strings of h5 files from CellRanger Count
        Outputs-
        analysis_csv- list of samples for scattering
    """
    # Read master Csv
    df = pd.read_csv(master_csv, header=0)
    # We don't need Flowcell, Lane or Index for Bo's Wdl
    df = df.drop(columns = ['Flowcell', 'Lane', 'Index'])
    # Sort by sample name
    df = df.sort_values(by=['Sample']).drop_duplicates(subset=['Sample'])
    sorted_h5s = []
    # TODO this is more robust but still not good enough-- calling sample in might not work if your sample names are something like 'test_sample' and 'test_sample2'
    for sample in df['Sample']:
        for h5 in h5s:
            if sample in h5:
                sorted_h5s = sorted_h5s + [h5.replace('/cromwell_root/', 'gs://')]
                break
    # Add the location column
    df['Location'] = sorted_h5s
    # Save the csv, output it
    df.to_csv('analysis.csv', index=False)


def orchestra_filter(paths, master_csv, sample_ids,trans_map):
    """Map the initial inputs to CellRanger Count.
        Arguments:
        paths- gsurls to every fastq directory
        master_csv- Csv File mapping samples, lanes and indices to bcl
        sample_ids- list of every sample, not actually needed, just easier
        trans_map- map of reference name to gsurl of transcriptome files
        Outputs-
        paths.tsv- Cromwell mapping of sample to a comma seperated string of fastq gsurls
        reference_list.tsv- Cromwell mapping of sample to genome
        transcriptome_list.tsv- Cromwell mapping of sample to transcriptome file
        chemistry.tsv- Cromwell mapping of sample to chemistry
    """
    # get a list of every fastq/sample directory using gsutil ls
    fastqs = []
    for path in paths:
        fastqs = fastqs + check_output(['gsutil', 'ls', path]).decode('utf-8').split('\n')
    # open the files for writing
    with open('chemistry.tsv', 'w+') as chemistry_list, open('reference.tsv', 'w+') as reference_list, open('transcriptome.tsv', 'w+') as transcriptome_list, open('paths.tsv', 'w+') as paths_list:
        # open the masterCsv and transcriptome map csv
        df = pd.read_csv(master_csv)
        tm = pd.read_csv(trans_map)
        # create the maps
        for sample in sample_ids:
            # Sample paths map
            # a path matches if it ends with .../sample_id/
            key = os.path.join(sample, '')
            filter_paths = ','.join([path for path in fastqs if path.endswith(key)])
            # Write to file
            paths_list.write('%s\t%s\n' % (sample, filter_paths))
            # Chemistry and Genome map
            # Chemistry and Genome are the same across sample (assumed) so we can just use the first one we get
            rows = df.loc[df['Sample'] == sample]
            chemistry = rows['Chemistry'].tolist()[0]
            # first get the genome for the sample
            reference = rows['Reference'].tolist()[0]
            # we have a map of reference names to gsurls
            transcriptome_file = list(tm[tm['Reference Name'] == reference]['Location'])[0]           
            # Write to files
            chemistry_list.write('%s\t%s\n' % (sample, chemistry))
            reference_list.write('%s\t%s\n' % (sample, reference))
            transcriptome_list.write('%s\t%s\n' % (sample, transcriptome_file))

def __main__(argv):
    """Command Line parser for scRna-Seq pipeline.
    Inputs- command line arguments
    """
    # the first command, -c, tells us which arguments we need to check for next, and which function we are going to call
    command = argv[1].replace('-c=', '')
    # create the argument parser
    parser = argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    if command == 'count':
        # CellRanger count method
        # add arguments
        parser.add_argument('--sampleId', '-id', help='Id of sample being run')
        parser.add_argument('--commaFastqs', '-cf', help='Comma seperated String with list of fastq directories', default='')
        parser.add_argument('--fastqs', '-fs', help='List of fastq directories', nargs='+', default=[''])
        parser.add_argument('--expectCells', '-E', help='Number of cells to expect', default='')
        parser.add_argument('--forceCells', '-F', help='Force number of cells', default='')
        parser.add_argument('--chemistry', '-C', help='Chemistry of fastqs', default = 'threeprime')
        parser.add_argument('--secondary', '-S', help='Run cellranger secondary analysis',  default = 'true')
        parser.add_argument('--transcriptome', '-tf', help='Transcriptome file',  default = '')
        parser.add_argument('--doForceCells', '-dfc', help='Boolean to use force cells', default = '')
        parser.add_argument('--command', '-c', help='Command to run', default = '')

        # call the method with parsed args
        args = parser.parse_args()
        cellranger_count(sample_id= args.sampleId, transcriptome= args.transcriptome, comma_fastqs= args.commaFastqs, fastqs= args.fastqs, expect_cells= args.expectCells, force_cells= args.forceCells, chemistry = args.chemistry, do_force_cells = args.doForceCells)
    elif command == 'mkfastq':
        # CellRanger mkfastq method
        # add arguments
        parser.add_argument('--bcl', '-b', help='Location of bcl')
        parser.add_argument('--masterCsv', '-M', help='Master Csv file containing maps of information', default='')
        parser.add_argument('--output_directory', '-O', help='List of fastq directories', default='')
        parser.add_argument('--command', '-c', help='Command to run', default = '')
        
        # call the method with parsed args
        args = parser.parse_args()
        cellranger_mkfastq(bcl = args.bcl, master_csv = args.masterCsv, output_directory = args.output_directory)
    elif command == 'parse':
        # Orchestra parseCsv Method
        # add arguments
        parser.add_argument('--masterCsv', '-M', help='Master Csv file containing maps of information', default='')
        parser.add_argument('--command', '-c', help='Command to run', default = '')
        
        # call the method with parsed args
        args = parser.parse_args()
        orchestra_parse_csv(master_csv = args.masterCsv)
    elif command == 'analysis':
        # Orchestra generate analysis csv method
        # add arguments
        parser.add_argument('--masterCsv', '-M', help='Master Csv file containing maps of information', default='')
        parser.add_argument('--h5s', '-hs', help='H5 output files', nargs='+', default=[''])
        parser.add_argument('--command', '-c', help='Command to run', default = '')
        
        # call the method with parsed args
        args = parser.parse_args()
        orchestra_analysis_csv(master_csv = args.masterCsv, h5s = args.h5s)
    elif command == 'filter':
        # Orchestra filter method
        # add arguments
        parser.add_argument('--masterCsv', '-M', help='Master Csv file containing maps of information', default='')
        parser.add_argument('--paths', '-p', help='Paths to fastq directories', nargs='+', default=[''])
        parser.add_argument('--sampleIds', '-S', help='List of sample names', nargs='+', default=[''])
        parser.add_argument('--transMap', '-t', help='CSV map of reference names to gsurls', default='')
        parser.add_argument('--command', '-c', help='Command to run', default = '')
        
        # call the method with parsed args
        args = parser.parse_args()
        orchestra_filter(master_csv = args.masterCsv, paths = args.paths, sample_ids = args.sampleIds, trans_map = args.transMap)
    args = parser.parse_args()
# python default
if __name__ == '__main__':
    __main__(sys.argv)