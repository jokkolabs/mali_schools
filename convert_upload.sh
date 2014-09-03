#!/bin/bash

if [ "x${OSM_PASSWD}" = "x" ];
	then
	echo "You need to set variable OSM_PASSWD."
	exit 1
fi

if [ "x${OSM_LIVE}" = "xy" ];
	then
	LIVE="-l y"
else
	LIVE=""
fi

rm -rf changesets

echo "Convert Source CSV into a list of OSM XML file"
python ./csv2osm.py MLI_schools.csv

ls -lh changesets

echo "Convert all OSM XML files into OSM Changeset files"
find changesets -name '*.osm' -exec python ./osm2change-python2.py {} \;

ls -lh changesets

if [ "x$OSM_UPLOAD" = "xy" ];
	then
	echo "Uploading Changeset files"
	find changesets -name '*.osc' -exec echo ./upload-python2.py -u opendatamali -p $OSM_PASSWD -m "Schools for {}" -c y $LIVE {} \;
else
	echo "Skipping upload. Use OSM_UPLOAD=y to Upload."
	echo "Use OSM_LIVE=y to target Live OSM server (defaults to dev)."
fi
