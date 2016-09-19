#!/bin/bash

PROJECTS_ROOT="/scholar/projects"

if [ $# -eq 0 ]
	then
		echo "This script requires at least one argument."
		exit
fi

for job in "$@"
do
	job_folder="$PROJECTS_ROOT/$job"
	if [ -d $job_folder ]
		then
			echo "Working on $job"
			echo "Removing Muster render files..."
			find $job_folder \( -name "_musterfiles" -o -name "mustache_renderScenes" -o -name ".DS_Store" \) -prune -exec rm -rf "{}" \;
			echo -e "Moving to .purgatory...\n"
			mv $job_folder $PROJECTS_ROOT/.purgatory
		else
			echo -e "$job does not exist in $PROJECTS_ROOT\n"
	fi
done
