#! /usr/bin/env python

# Imports
import os
from subprocess import call
import xml.etree.ElementTree as ET
import pandas as pd
from subprocess import run
from subprocess import check_output
import sys
import argparse

def cellranger_count(sampleId, transcriptome, commaFastqs='',fastqs='', expectCells='', forceCells='', secondary='false', chemistry='threeprime', doForceCells = ''):
    """Run Cell Ranger count on directory (s) of fastqs.
        Arguments:
        sampleId- name of sample
        transcriptome- path of transcriptome file
        commaFastqs- comma seperated string of fastq direcotry gsurls
        fastqs- wdl formatetd array of fastqs
        secondary- CellRanger count argument, run Cell Ranger built in analysis
        expectCells- CellRanger count argument
        forceCells- CellRanger count argument
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
    os.mkdir("transcriptome_dir")
    call(["tar", "xf", transcriptome, "-C", "transcriptome_dir", "--strip-components", "1"])

    # create a unique list (set) of fastq directories and download them
    dirs = set()
    sample = sampleId
    i = 0
    if commaFastqs is not '':
        fastqs = commaFastqs.split(",")
    for f in fastqs:
        # download the fastqs to a unique location and add that location to set
        os.mkdir(str(i))
        call(["gsutil", "-q", "-m", "cp", "-r", f, str(i)])
        os.path.join(str(i), sample,"")
        dirs.add(os.path.join(str(i), sample,""))
        i+=1
    # create the cellranger count command and execute it
    call_args = list()
    call_args.append('cellranger')
    call_args.append('count')
    call_args.append('--jobmode=local')
    call_args.append('--transcriptome=transcriptome_dir')
    call_args.append('--sample=' + sample)
    call_args.append('--id=results_'+sample)
    call_args.append('--fastqs=' + ','.join(dirs))
    if secondary is not 'true':
        call_args.append('--nosecondary')
    if (forceCells is not '') and (doForceCells is 'true'):
        call_args.append('--force-cells=' + str(forceCells))
    elif expectCells is not '':
        call_args.append('--expect-cells=' + str(expectCells))
    if chemistry is not '':
        call_args.append('--chemistry='+chemistry)
    call(call_args)

def cellranger_mkfastq(bcl,masterCsv,output_directory,samples_csv = 'sample.csv'):
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
    call(["gsutil", "-q", "-m", "cp", "-r", bcl, "."])
    # Create local fastq output directory
    os.mkdir("fastqs")
    # get the name of the flowcell, need this to know fastq output directory name
    path = bcl
    run = list(filter(None, path.split("/")))[-1]

    # get flowcell
    tree = ET.parse(os.path.join(run,"RunInfo.xml"))
    root = tree.getroot()
    flowcell = root.find('Run').find('Flowcell').text

    # create the sample lane index csv
    df = pd.read_csv(masterCsv,header=0)
    df = df.loc[df['Flowcell'] == path]
    df = df[["Lane","Sample", "Index"]]
    df.to_csv(samples_csv,index=False)

    # run mkfastq command
    call_args = list()
    call_args.append('cellranger')
    call_args.append('mkfastq')
    call_args.append('--run=' + os.path.join(run,""))
    call_args.append('--csv=' + samples_csv)
    call_args.append('--output-dir=fastqs')
    call(call_args)

    # move the fastqs to the output directory
    call(["gsutil", "-q", "-m", "mv", os.path.join('fastqs',flowcell), output_directory])
    # move and rename the qc summary file to fastq output directory, rename it so it doesn't get rewritten if there are multiple bcls
    call(["gsutil", "-q", "-m", "mv", os.path.join(flowcell,"outs","qc_summary.json"), os.path.join(output_directory,flowcell+"_qc_summary.json")])
    
    # write the path of fastqs for cromwell
    file = open("path.txt","w") 
    file.write(os.path.join(output_directory,flowcell,""))
    file.close()

    # move the undetermined fastqs over to the bucket
    try:
        call(["gsutil", "-q", "-m", "mv", os.path.join('fastqs',"Undetermined_*"), os.path.join(output_directory,flowcell+"_Undetermined","")])
        
        # write the undetermined fastqs path for cromwell
        file = open("undetermined.txt","w") 
        file.write(os.path.join(output_directory,flowcell+"_Undetermined",""))
        file.close()
    except:
        print("Unable to move Undetermined to Bucket")
    
    
def orchestra_parse_csv(masterCsv):
    """Parse the initial csv input to orchestra.
        Arguments:
        masterCsv- Csv File mapping samples, lanes and indices to bcl
        Outputs-
        samples_file- list of samples for scattering
        bcl_file- list of bcl gsurls for scattering
    """
    # Read the masterCsv
    df = pd.read_csv(masterCsv,header=0)
    # Get unique gsurls of bcls
    bcl_paths = set(df['Flowcell'].tolist())
    # Write the bcls for Cromwell
    bcl_file = open('bcls.txt', 'w+')
    for item in bcl_paths:
      bcl_file.write("%s\n" % item)
    bcl_file.close()
    # Get unique sample names
    sampleIds = set(df['Sample'].tolist())
    # Write the sample names for Cromwell
    samples_file = open('samples.txt', 'w+')
    for item in sampleIds:
      samples_file.write("%s\n" % item)
    samples_file.close()


def orchestra_analysis_csv(masterCsv, h5s):
    """Map the initial csv input to CellRanger Count h5 file outputs for analysis WDL.
        Arguments:
        masterCsv- Csv File mapping samples, lanes and indices to bcl
        h5s- array of cromwell localized file strings of h5 files from CellRanger Count
        Outputs-
        analysis_csv- list of samples for scattering
    """
    # Read master Csv
    df = pd.read_csv(masterCsv,header=0)
    # We don't need Flowcell, Lane or Index for Bo's Wdl
    df = df.drop(columns = ["Flowcell", "Lane", "Index"])
    # Sort by Sample Name
    df = df.sort_values(by=["Sample"]).drop_duplicates(subset=["Sample"])
    sorted_h5s = []
    # TODO this is more robust but still not good enough
    for sample in df["Sample"]:
        for h5 in h5s:
            if sample in h5:
                sorted_h5s = sorted_h5s + [h5.replace("/cromwell_root/", "gs://")]
                break
    # Add the location column
    df["Location"] = sorted_h5s
    # Save the csv, output it
    df.to_csv("analysis.csv", index=False)


def orchestra_filter(paths, masterCsv, sampleIds,transMap):
    """Map the initial inputs to CellRanger Count.
        Arguments:
        paths- gsurls to every fastq directory
        masterCsv- Csv File mapping samples, lanes and indices to bcl
        sampleIds- list of every sample, not actually needed, just easier
        transMap- map of reference name to gsurl of transcriptome files
        Outputs-
        paths.tsv- Cromwell mapping of sample to a comma seperated string of fastq gsurls
        reference_list.tsv- Cromwell mapping of sample to genome
        transcriptome_list.tsv- Cromwell mapping of sample to transcriptome file
        chemistry.tsv- Cromwell mapping of sample to chemistry
    """
    # get a list of every fastq/sample directory using gsutil ls
    fastqs = []
    for f in paths:
        fastqs = fastqs + check_output(["gsutil", "ls", f]).decode("utf-8").split("\n")
    # open the files for writing
    chemistry_list = open('chemistry.tsv', 'w+')
    reference_list = open('reference.tsv', 'w+')
    transcriptome_list = open('transcriptome.tsv', 'w+')
    paths_list = open('paths.tsv', 'w+')
    # open the masterCsv and transcriptome map csv
    df = pd.read_csv(masterCsv)
    tm = pd.read_csv(transMap)
    # create the maps
    for sample in sampleIds:
        # Sample paths map
        # a path matches if it ends with .../sample_id/
        key = os.path.join(sample,"")
        filter_paths = ",".join([path for path in fastqs if path.endswith(key)])
        # Write to file
        paths_list.write("%s\t%s\n" % (sample, filter_paths))
        # Chemistry and Genome map
        # Chemistry and Genome are the same across sample (assumed) so we can just use the first one we get
        rows = df.loc[df["Sample"] == sample]
        chemistry = rows["Chemistry"].tolist()[0]
        # first get the genome for the sample
        reference = rows["Reference"].tolist()[0]
        # we have a map of reference names to gsurls
        transcriptome_file = list(tm[tm["Reference Name"] == reference]["Location"])[0]           
        # Write to files
        chemistry_list.write("%s\t%s\n" % (sample, chemistry))
        reference_list.write("%s\t%s\n" % (sample, reference))
        transcriptome_list.write("%s\t%s\n" % (sample, transcriptome_file))
    # close the files
    transcriptome_list.close()
    reference_list.close()
    chemistry_list.close()
    paths_list.close()

def __main__(argv):
    """Command Line parser for scRna-Seq pipeline.
    Inputs- command line arguments
    """
    # the first command, -c, tells us which arguments we need to check for next, and which function we are going to call
    command = argv[1].replace("-c=", "")
    # create the argument parser
    parser = argparse.ArgumentParser()
    if command == "count":
        # CellRanger count method
        # add arguments
        parser.add_argument('--sampleId', '-id', help="Id of sample being run", type= str)
        parser.add_argument('--commaFastqs', '-cf', help="Comma seperated String with list of fastq directories", type= str, default='')
        parser.add_argument('--fastqs', '-fs', help="List of fastq directories", nargs='+', type= str, default=[''])
        parser.add_argument('--expectCells', '-E', help="Number of cells to expect", type= str, default='')
        parser.add_argument('--forceCells', '-F', help="Force number of cells", type= str, default='')
        parser.add_argument('--chemistry', '-C', help="Chemistry of fastqs", type= str, default = "threeprime")
        parser.add_argument('--secondary', '-S', help="Run cellranger secondary analysis", type= str, default = "true")
        parser.add_argument('--transcriptome', '-tf', help="Transcriptome file", type= str, default = "")
        parser.add_argument('--doForceCells', '-dfc', help="Boolean to use force cells", type= str, default = "")
        parser.add_argument('--command', '-c', help="Command to run", type= str, default = "")

        # call the method with parsed args
        args = parser.parse_args()
        cellranger_count(sampleId= args.sampleId, transcriptome= args.transcriptome, commaFastqs= args.commaFastqs, fastqs= args.fastqs, expectCells= args.expectCells, forceCells= args.forceCells, chemistry = args.chemistry)
    elif command == "mkfastq":
        # CellRanger mkfastq method
        # add arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--bcl', '-b', help="Location of bcl", type= str)
        parser.add_argument('--masterCsv', '-M', help="Master Csv file containing maps of information", type= str, default='')
        parser.add_argument('--output_directory', '-O', help="List of fastq directories", type= str, default='')
        parser.add_argument('--command', '-c', help="Command to run", type= str, default = "")
        
        # call the method with parsed args
        args = parser.parse_args()
        cellranger_mkfastq(bcl = args.bcl, masterCsv = args.masterCsv, output_directory = args.output_directory)
    elif command == "parse":
        # Orchestra parseCsv Method
        # add arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--masterCsv', '-M', help="Master Csv file containing maps of information", type= str, default='')
        parser.add_argument('--command', '-c', help="Command to run", type= str, default = "")
        
        # call the method with parsed args
        args = parser.parse_args()
        orchestra_parse_csv(masterCsv = args.masterCsv)
    elif command == "analysis":
        # Orchestra generate analysis csv method
        # add arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--masterCsv', '-M', help="Master Csv file containing maps of information", type= str, default='')
        parser.add_argument('--h5s', '-hs', help="H5 output files", type= str, nargs='+', default=[''])
        parser.add_argument('--command', '-c', help="Command to run", type= str, default = "")
        
        # call the method with parsed args
        args = parser.parse_args()
        orchestra_analysis_csv(masterCsv = args.masterCsv, h5s = args.h5s)
    elif command == "filter":
        # Orchestra filter method
        # add arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--masterCsv', '-M', help="Master Csv file containing maps of information", type= str, default='')
        parser.add_argument('--paths', '-p', help="Paths to fastq directories", nargs='+',type= str, default=[''])
        parser.add_argument('--sampleIds', '-S', help="List of Sample Names", nargs='+',type= str, default=[''])
        parser.add_argument('--transMap', '-t', help="CSV map of reference names to gsurls", type= str, default='')
        parser.add_argument('--command', '-c', help="Command to run", type= str, default = "")
        
        # call the method with parsed args
        args = parser.parse_args()
        orchestra_filter(masterCsv = args.masterCsv, paths = args.paths, sampleIds = args.sampleIds, transMap = args.transMap)
    else:
        # Incorrectely formatted input
        print("Error", command, "Is not a registered command")

# python default
if __name__ == "__main__":
    __main__(sys.argv)