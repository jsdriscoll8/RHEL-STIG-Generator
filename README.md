# RHEL-STIG-Generator

## Overview

One of the problems I have encountered while experimenting with removing STIG faults across RHEL machines
is the simple breadth and tediousness of fixing lots of findings. Tools like traditional Ansible playbooks
and Bash scripts serve to automate the process of eliminating vulnerabilities, but this still leaves the
issue of determining the appropriate findings to patch, and compiling their appropriate fixes.

In the contained SQLite database, fix entries are associated with a corresponding YAML play in the files/
directory. However, these patches may also be referenced via a tag (e.g. SSH or login settings) and/or their
CAT rating. The main configurator program generates custom, user-defined Ansible playbooks, eliminating
the precise vulnerabilities a user wishes to solve! 

## Files & Dependencies

* **insert_new_fix.py**
    * When run, enables the user to insert new STIG fixes into the database.
* **config_generator.py**
    * Collects fixes to compile based on user-defined queries.
    * Query language
        * Queries begin with a field specifier: GROUPID, TAG, or CAT.
        * GROUPID and TAG take in exact input via '=='; CAT may use any numeric comparison.
        * Single compound queries may be initiated via the AND keyword.
    * Sample queries
        * CAT > 3
        * GROUPID == 258145
        * TAG == SSH AND CAT <= 2
* **Dependencies/environment**
    * As SQLite3 is a standard Python library, no external packages are necessary! Any Python 3.10+ environment
    will run either file.

## Running
* Run either file from your preferred IDE or a terminal window; ensure you are running at least Python 3.10.
* Insert fixes or generate a configuration as necessary. The keywords and query language may be referenced while running
at any time.

## Known Bugs and Issues

* This page will be updated end-of-day if discovered issues are not resolved by 17:00.

## Future Plans and Updates

* Containerization
* Larger library of fixes
