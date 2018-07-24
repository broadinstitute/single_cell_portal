# Monitoring Scripts

Scripts to run in WDL tasks to output runtime performance.

## Usage
~~~~
task TaskName {
	File monitoringScript	
	command {
	    chmod u+x ${monitoringScript}
	    ${monitoringScript} > monitoring.log &

	    original task commands...
	}

	output {
		original task outputs...
		File monitoringLog = "monitoring.log"
	}
~~~~