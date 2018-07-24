# Monitoring Scripts

Scripts to run in WDL tasks to output runtime performance.

## Usage
~~~~
task TaskName {
	File monitoringScript	
	command {
	    chmod u+x ${monitoringScript}
	    ${monitoringScript} > monitoring.log &

	    original_task commands...
	}

	output {
		...
		File monitoringLog = "monitoring.log"
	}
~~~~