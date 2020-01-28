#!/usr/bin/env python3

################################################################################
# The publications metadata augmentor!
# This is the starting point of a pipeline that tries to augment a list of
# publications with metadata from places like PubMed and DOI.org to build a
# reporting tool and some pretty web pages.
# Go read the docs: https://github.com/OllyButters/papers/wiki
################################################################################

# core packages
import json
import os.path
from os import listdir
import os
import logging
import time
import sys
# from pprint import pprint

# Internal packages
import config.config as config
import setup.setup as setup
import clean.clean as clean
import add.geocode
import add.citations
import analyse.analyse as analyse
import web_pages.build_htmlv2
import bibliography.bibtex
import get.simple_collate
import networks.author_network as author_network
import analyse.coverage_report as coverage_report

__author__ = "Olly Butters, Hugh Garner, Tom Burton, Becca Wilson"
__date__ = 10/1/20
__version__ = '0.13.0'

# Lets figure out some paths that everything is relative to
# global root_dir
path_to_papers_py = os.path.abspath(sys.argv[0])
root_dir = os.path.dirname(os.path.dirname(path_to_papers_py))
print('Root directory = ' + root_dir)

# Get all the config - these will be a global vars available like config.varname
config.build_config_variables(root_dir)

# Delete any unneeded data hanging around in the cache
setup.tidy_existing_file_tree()
setup.clean_old_scopus_cache_file()

# Build the file tree relative to the root_dir
setup.build_file_tree()

# Time Log
start_time = time.time()
print('Start Time: ' + str(start_time))

# Set up the logging. Level can be DEBUG|.....
log_file = root_dir + '/logs/'+config.project_details['short_name']+'.log'
logging.basicConfig(filename=log_file,
                    filemode='w',
                    level=config.logging_loglevel)

print('Log file: ' + log_file)
print('Run something like: tail -f ' + log_file)

# Output some info to the log file to help with debugging
logging.info('Running version: ' + __version__)
logging.info('Started at: ' + str(start_time))

###########################################################
# Get the papers. This will get all the metadata and store
# it in a cache directory.
# papers will be the giant LIST that has all the papers in it, each as a dictionary
papers = []

# Collate does not do anything with the papers object.
get.simple_collate.collate()

# Get list of files in merged directory
merged_files_list = listdir(config.cache_dir + '/processed/merged/')
merged_files_list.sort()
# merged_files_list = merged_files_list[0:10]
print(str(len(merged_files_list))+' merged papers to load.')

# Open each one and add to papers object
for this_merged_file in merged_files_list:
    with open(config.cache_dir + '/processed/merged/' + this_merged_file) as fo:
        # Will be a dictionary
        this_paper = json.load(fo)
        this_paper['filename'] = this_merged_file
        papers.append(this_paper)

print(str(len(papers)) + ' papers to process.')


###########################################################
# Clean the data - e.g. tidy dates and institute names
clean.clean(papers)

# should probably move clean_institution into clean directly
clean.clean_institution(papers)

###########################################################
# Add some extra data in - i.e. geocodes and citations
add.geocode.geocode(papers)

# Write papers to summary file
file_name = root_dir + '/data/' + config.project_details['short_name'] + '/summary_added_to'
fo = open(file_name, 'w')
fo.write(json.dumps(papers, indent=4))
fo.close()

# Write a copy of each paper to a separate file
for this_paper in papers:
    this_file_name = config.cache_dir + '/processed/cleaned/' + this_paper['IDs']['zotero'] + '.cleaned'
    fo = open(this_file_name, 'w')
    fo.write(json.dumps(this_paper, indent=4))
    fo.close()

# Generate the coverage report, but only if not to be shown publicly
if not config.public_facing:
    coverage_report.coverage_report(papers)

bibliography.bibtex.bibtex(papers)

###########################################################
# Do some actual analysis on the data. This will result in
# some CSV type files that can be analysed.
analyse.journals(papers)

# Figure out the word frequecies
analyse.word_frequencies(papers, 'title')
analyse.word_frequencies(papers, 'keywords')
# papers_with_abstract_text = analyse.word_frequencies(papers, 'abstract')

network = analyse.authors(papers)
analyse.first_authors(papers)
analyse.inst(papers)
# analyse.mesh(papers)
analyse.output_csv(papers)

###########################################################
# Make some web pages
web_pages.build_htmlv2.build_css_colour_scheme()
cohort_rating, cohort_rating_data_from = web_pages.build_htmlv2.build_home(papers)
web_pages.build_htmlv2.build_papers(papers)
web_pages.build_htmlv2.build_mesh(papers)
web_pages.build_htmlv2.build_country_map(papers, config.google_maps_api_key)
web_pages.build_htmlv2.build_metrics(papers, cohort_rating, cohort_rating_data_from, config.metrics_study_start_year, config.metrics_study_current_year)
# web_pages.build_htmlv2.build_abstract_word_cloud(papers, papers_with_abstract_text)
web_pages.build_htmlv2.build_author_network(papers, network)
web_pages.build_htmlv2.build_help()
web_pages.build_htmlv2.build_search(papers)

if config.network_create_networks:
    # generate and dump the html for author network
    author_network.build_network()

# Time Log
end_time = time.time()
elapsed_time = end_time - start_time
elapsed_time_string = str(int(elapsed_time) / 60) + ":" + str(int(elapsed_time) % 60).zfill(2)
print('End Time: ' + str(end_time))
print('Elapsed Time (mm:ss) - ' + elapsed_time_string)

logging.info('Finished at: ' + str(end_time))
logging.info('Elapsed time (mm:ss) : ' + elapsed_time_string)
