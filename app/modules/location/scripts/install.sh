#!/bin/bash

# map controller
CTL="${BASEURL}index.php?/module/location/"

# Get the scripts in the proper directories
${CURL} "${CTL}get_script/location.sh" -o "${MUNKIPATH}preflight.d/location.py"

# Check exit status of curl
if [ $? = 0 ]; then
	# Make executable
	chmod a+x "${MUNKIPATH}preflight.d/location.py"

	# Set preference to include this file in the preflight check
	defaults write "${PREFPATH}" ReportItems -dict-add location "${MUNKIPATH}preflight.d/cache/location.plist"

else
	echo "Failed to download all required components!"
	rm -f "${MUNKIPATH}preflight.d/location.py"

	# Signal that we had an error
	ERR=1
fi


