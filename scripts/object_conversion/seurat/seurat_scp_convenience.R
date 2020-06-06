# Functions for generating Single Cell Portal files from Seurat object.
# Supports objects created with Seurat v2.x and v3.x.
# Generating compressed Expression Matrix files (.mtx.gz) requires gzip to be installed.
#
# Functions:
# generateExpressionMatrix()
# generateClusterFile()
# generateMetadataFile()
# addConsistentMetadataColumns()
#
# Note that these functions assume consistency between cell names in raw.data/data/counts and 
# meta.data slots in object. This might not be true if cells were removed during processing steps -- 
# double check your object first.




#' Writes expression matrix file for SCP visualization (in Matrix Market format). Can also generate
#' corresponding barcodes and genes files. Expression data is taken from raw count or normalized data
#' slots in object. If data in object is not in sparse format, this function will convert it first. 
#' 
#' Read more about the expression matrix file format at https://github.com/broadinstitute/single_cell_portal/wiki/Expression-File.
#'  
#' Requires data.table package (>= v1.12.4).
#' For now only accepts raw.data and data (normalized) slots. Note that in Seurat v2.x objects,
#' raw counts are available through "raw.data", while in Seurat v3.x objects, raw counts are available
#' through "counts".
#' Writes gene-sorted .mtx file and barcodes and genes files if requested into directory specified.
#' Currently requires gzip to be installed for compression, as fwrite to compressed file causes corruption, 
#' while write.table cannot append directly to compressed file (for now). 
#' Compression may take a while for large objects. 
#' Some code from tutorial by Kamil Slowikowski (https://slowkow.com/notes/sparse-matrix/).
#'
#' @param object Seurat object.
#' @param matrix.dir Path to directory where files should be written. Must not already exist. 
#' @param slot.use Data slot to use for expression data (supports "raw.data", "data", "counts"). (default "raw.data")
#' @param include.barcodes Write barcodes .tsv file in addition to .mtx file (default TRUE).
#' @param include.genes Write genes .tsv file in addition to .mtx file (default TRUE).
#' @param compress.files Whether to compress individual files (default FALSE). 
#' 
#' @examples
#' \dontrun{
#' generateExpressionMatrix(seurat_obj, "/path/to/directory", slot.use = "data", compress.files = T)
#' }
generateExpressionMatrix = function(object, matrix.dir, slot.use = "raw.data", 
                                    include.barcodes = T, include.genes = T,
                                    compress.files = F) {
  
  if (!(slot.use %in% c('raw.data', 'data', 'counts'))) {
    stop('This slot is not supported for expression matrix writing. Please use "raw data", "data", or "counts".')
  }
  if (file.exists(matrix.dir)){
    stop('Provided directory already exists. Please use different directory name.')
  } else {
    dir.create(matrix.dir)
  }
  
  write_matrix = Seurat::GetAssayData(object, slot = slot.use)
  # set numeric types here 
  mtype = "real"
  if (slot.use == "raw.data") {
    mtype = "integer"
  }
  # convert to sparse matrix format if dense
  if (class(write_matrix)[1] != 'dgCMatrix') {
    write_matrix = as(as.matrix(write_matrix), 'CsparseMatrix')
  }
  # sort sparse matrix by gene
  # might need to make this more memory efficient 
  summ = summary(write_matrix)
  summ = summ[with(summ, order(i)),]
  
  # set vars for compression
  write_function = "file"
  file_suffix = ""
  if (compress.files) {
    write_function = "gzfile"
    file_suffix = ".gz"
  }
  # write .mtx file 
  out = paste0(matrix.dir, '/expression_matrix.mtx')
  writeLines(
    c(
      sprintf("%%%%MatrixMarket matrix coordinate %s general", mtype),
      sprintf("%s %s %s", write_matrix@Dim[1], write_matrix@Dim[2], length(write_matrix@x))
    ),
    file(out)
  )
  # Found that using fwrite to .gz files results in some incompatability between 
  # the file and SCP parser (causes end of file error)
  # If this is ever fixed, use data.table::fwrite to write directly to .gz file.
  data.table::fwrite(
    x = summ,
    file = out,
    append = TRUE,
    sep = " ",
    row.names = FALSE,
    col.names = FALSE
  )
  message(paste0("Finished writing ", out))
  
  if (compress.files) {
    # compress the .mtx file
    system(paste0('gzip ', out))
    message(paste0("Finished compressing ", out))
  }
  
  # write barcodes file 
  if (include.barcodes) {
    out = paste0(matrix.dir, '/barcodes.tsv', file_suffix)
    writeLines(
      colnames(write_matrix), 
      get(write_function)(out)
    )
    message(paste0("Finished writing ", out))
  }
  
  # write genes file 
  if (include.genes) {
    out = paste0(matrix.dir, '/genes.tsv', file_suffix)
    writeLines(
      row.names(write_matrix), 
      get(write_function)(out)
    )
    message(paste0("Finished writing ", out))
  }
}

#' Writes cluster file for SCP visualization with appropriate headers. Cluster coordinates 
#' are taken from "cell.embeddings" of appropriate dimensionality reduction slot (eg. t-SNE or UMAP).
#' Cluster files can have 2 or 3 dimensions. This function cuts off coordinates after the 
#' third dimension (eg. using only the first 3 PCs) if more are present. Can be used to create 
#' cluster file for subset of all cells by passing vector of cell names to subset.cells.
#' 
#' Read more about cluster files at https://github.com/broadinstitute/single_cell_portal/wiki/Cluster-Files.
#' 
#' @param object Seurat object. 
#' @param file.name File path to write (.tsv is appropriate). (Must be new name; will not overwrite existing file.)
#' @param reduction.use Name of dimensional reduction to use for coordinates (default 'tsne').
#' @param max.cols Number of coordinate columns/dimensions to include (only 2 or 3 are acceptable) (default 3 or 
#'   2 if only 2 columns available).
#' @param subset.cells Vector of cell names to use in subsetting cluster file (default NULL).
#' 
#' @examples
#' \dontrun{
#' generateClusterFile(seurat_obj, "/path/to/file.tsv", reduction.use = "umap")
#' }
generateClusterFile = function(object, file.name, reduction.use = 'tsne', 
                               max.cols = 3, subset.cells = NULL) {
  
  if (file.exists(file.name)){
    stop('Provided file path already exists. Please use different file.name.')
  }
  
  # Get coordinates from cell embeddings 
  s_version = packageVersion('Seurat')$major
  if (s_version == 2) {
    coords = GetCellEmbeddings(object, reduction.type = reduction.use)
  } else if (s_version == 3) {
    coords = Embeddings(object, reduction = reduction.use)
  } else {
    stop ('Only Seurat objects with major version >= 2 are supported.')
  }
  if (!(max.cols %in% c(2, 3))) {
    stop("Only 2 or 3 coordinate columns allowed. Please specify different max.cols.")
  }
  
  if (!is.null(subset.cells)) {
    coords = coords[subset.cells,]
  }
  # Cut off extra columns
  if (ncol(coords) > max.cols) {
    coords = coords[,1:max.cols]
    message(paste0("Keeping only first", max.cols, " dimensions of selected reduction."))
  }
  # Add cell names and rename columns
  coords = cbind(row.names(coords), coords)
  colnames(coords) = c('NAME', 'X', 'Y', 'Z')[1:ncol(coords)]
  
  # Insert data type row and reorder
  data_types = c('TYPE', rep('numeric', ncol(coords) - 1))
  coords = rbind(coords, data_types)
  coords = coords[c(nrow(coords), 1:(nrow(coords) - 1)),]
  
  write.table(coords, file = file.name, sep = '\t', row.names = F, quote = F)
  message(paste0("Finished writing ", file.name))
}

# Global variables for metadata related functions below
# ***These may need to be updated periodically***
required_meta_cols = c('biosample_id', 'donor_id', 'species', 'disease', 'organ', 
                       'library_preparation_protocol', 'sex', 'biosample_type')
required_with_cv = c('sex', 'biosample_type')
cv_list = list(
  biosample_type = c("CellLine","DerivedType_Organoid","DerivedType_InVitroDifferentiated",
                     "DerivedType_InducedPluripotentStemCell","PrimaryBioSample",
                     "PrimaryBioSample_BodyFluid","PrimaryBioSample_CellFreeDNA",
                     "PrimaryBioSample_PrimaryCell","PrimaryBioSample_PrimaryCulture",
                     "PrimaryBioSample_Stool","PrimaryBioSample_Tissue"),
  sex = c("male", "female", "mixed", "unknown")
)

# Utility function to handle user input (with potential controlled values)
readline_q = function(prompt, cv = NULL) {
  input = readline(prompt)
  if (input == 'quit') {
    stop("Manual quit.", call. = F)
  } else {
    if (!is.null(cv) & !(as.character(input) %in% cv)) {
      input = readline_q("Value not included in list of controlled values. Try again: ",
                         cv = cv)
    } else {
      return(input)
    }
  } 
}

#' An interactive function that will allow users to easily add metadata that is consistent for their
#' entire dataset (eg. if all cells are Mus musculus). Automatically prompts user for 
#' value for all missing required metadata columns. Can be used to add optional columns as well.
#' 
#' @param object Seurat object.
#' @param return.object Whether to return modified object or dataframe. If TRUE, 
#'    will return modified Seurat object. If FALSE, will return new metadata dataframe. 
#' @examples
#' \dontrun{
#' updated_object = addConsistentMetadataColumns(seurat_obj, return.object = T)
#' }
addConsistentMetadataColumns = function(object, return.object = F) {
  
  metadata = object@meta.data
  # Check for required metadata columns (except for NAME)
  missing = setdiff(required_meta_cols, colnames(metadata))
  message("Note that your object metadata is missing the following required columns:\n",
          paste(missing, collapse = ', '))
  message("You will be prompted for corresponding values for each of these columns.\n", 
          "You can skip columns for which your dataset isn't constant by typing 'skip'.\n",
          "Type 'quit' to exit this function at any point.")
  message("Are there any other (optional) consistent columns you want to add?")
  
  cols_add = readline_q(prompt = "Enter columns you wish to add, separated by a space: ")
  cols_add = c(missing, strsplit(cols_add, ' ')[[1]])
  for (col in cols_add) {
    if (col %in% required_with_cv) {
      message(paste0("The next metadata column, ", col, " has a list of controlled values. The values are:\n"),
              paste(cv_list[[col]], collapse = ', '))
      input = readline_q(prompt = paste0("Enter dataset value for ", col, ": "), cv = cv_list[[col]])
    } else {
      input = readline_q(prompt = paste0("Enter dataset value for ", col, ": "))
    }
    if (input != "skip") {
      metadata[[col]] = as.character(input)
    }
  }
  
  if (return.object) {
    object@meta.data = metadata
    return(object)
  } else {
    return(metadata)
  }
}

#' Writes metadata file for SCP visualization with appropriate headers. Metadata columns 
#' are taken from meta.data slot in object. Function will stop if required metadata columns
#' are missing (https://github.com/broadinstitute/single_cell_portal/wiki/Metadata-Convention).
#' By default, will include all columns in meta.data slot with their existing column names. 
#' User can pass in different column names to match them with required column names if appropriate.
#' 
#' Read more about the metadata file format here: https://github.com/broadinstitute/single_cell_portal/wiki/Metadata-File
#' 
#' @param object Seurat object. 
#' @param file.name File path to write (.tsv is appropriate). (Must be new name; will not overwrite existing file.)
#' @param cols.use Vector of column names to determine which columns are written to file. Default is to
#'   include all columns in meta.data slot.
#' @param new.col.names Vector of new column names to use in place of existing column names. Must match in 
#'   length with number of columns written to file. Default is to use existing names.
#' @param data.types Vector of data types ("group" or "numeric") for included columns. Default is to 
#'   infer the data types from meta.data column classes. 
#' 
#' @examples
#' \dontrun{
#' generateMetadataFile(seurat_obj, "/path/to/file.tsv")
#' # providing new column names (this object has only 4 metadata columns)
#' generateMetadataFile(seurat_obj, "/path/to/file.tsv", new.col.names = c("nUMI", "nGene", "sex", "organ"))
#' }
generateMetadataFile = function(object, file.name, cols.use = NULL, new.col.names = NULL, 
                                data.types = NULL) {
  
  if (file.exists(file.name)){
    stop('Provided file path already exists. Please use different file.name.')
  }
  metadata = object@meta.data
  
  if (!is.null(cols.use)) {
    metadata = metadata[, cols.use]
  }
  if (!is.null(new.col.names)) {
    colnames(metadata) = new.col.names
  }
  
  # Check for required metadata columns (except for NAME)
  missing = setdiff(required_meta_cols, colnames(metadata))
  if (length(missing) > 0) {
    stop("Your object metadata is missing required metadata columns or does not have the appropriate column names.\n",
         "The missing columns are: ", paste(missing, collapse = ', '), ".\nUse the new.col.names argument to replace column ",
         "names if appropriate or the addConsistentMetadataColumns() function to interactively add ",
         "columns. Visit https://github.com/broadinstitute/single_cell_portal/wiki/Required-Metadata\n",
         "to learn more about the required metadata types.")
  }
  
  # Determine data types
  if (!is.null(data.types)) {
    if (length(data.types) != ncol(metadata) - 1) {
      stop("Length of data.types does not match number of metadata columns selected.")
    }
    data_types = c('TYPE', data.types)
  } else {
    # Infer data types from column types 
    classes = as.character(sapply(metadata, class))
    data_types = c('TYPE', sapply(classes, function(x) {
      if (x %in% c("integer", "numeric", "double")) {
        return("numeric")
      } else {
        return("group")
      }
    }, USE.NAMES = F)
    )
  }
  
  # Insert NAME column and reorder
  metadata[['NAME']] = row.names(metadata)
  metadata = metadata[,c(ncol(metadata), 1:(ncol(metadata) - 1))]
  
  # Insert data type row and reorder
  # First convert all types to character to prevent NAs
  metadata[] <- lapply(metadata, as.character)
  metadata = rbind(metadata, data_types)
  metadata = metadata[c(nrow(metadata), 1:(nrow(metadata) - 1)),]
  
  write.table(metadata, file = file.name, sep = '\t', row.names = F, quote = F)
  message(paste0("Finished writing ", file.name))
}