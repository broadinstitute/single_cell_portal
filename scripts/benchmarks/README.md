# Monitoring Scripts

Benchmarking Scripts/Notebooks

## Usage

File                                          | Usage                                               | Code                                     | Output              
--------------------------------------------- | ----------------------------------------------------| ---------------------------------------- | ------------------- 
cellranger_orchestra_pipeline.ipynb | benchmark cellranger pipelines (orchestra pipeline) | `parse_logs([["monitroig_log.log","corresponding_std_out.txt"], ["monitroig_log2.log","corresponding_std_out2.txt"]], hours = 2)` | Plotly graphs of cpu, mem and disk usage, with cellranger event mapping 