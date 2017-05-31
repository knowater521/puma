import csv
import json
import os.path
import logging
import papersCache as pc
from pprint import pprint
import config.config as config

from Bio import Entrez

# retrieve pubmed metadata for pubmed id
# store unformatted xml in cache (raw/pubmed/xml)
# process xml using BioPython (Entrez.read)
# store as json in cache (raw/pubmed)
# return data processed from xml (json-type)
def getPubmed(this_pmid):
  print 'Working on '+this_pmid
  logging.info('Working on %s',this_pmid)

  logging.info('Downloading %s', this_pmid)
  Entrez.email = config.pubmed_email     # Always tell NCBI who you are

  # Look at the PubModel. See http://www.nlm.nih.gov/bsd/licensee/elements_article_source.html
  override_pubmodel=False
  handle = Entrez.efetch(db="pubmed", id=this_pmid, retmode="xml")

  pmid_xml_data = handle.read()

  xml_file_loc = pc.dumpFile(this_pmid+'.xml', pmid_xml_data, 'raw/pubmed/xml')


  try:
    xml_file = open(xml_file_loc, 'r')
    pmid_data = Entrez.read(xml_file)
    if isinstance(pmid_data, list):
      pmid_data = pmid_data[0]
    print pmid_data
    if 'MedlineCitation' not in pmid_data.keys():
      if 'PubmedArticle' in pmid_data.keys() and 'MedlineCitation' in pmid_data['PubmedArticle'][0].keys():
        pmid_data = pmid_data['PubmedArticle'][0]
      else:
        raise ValueError("Can't find MedlineCitation for paper "+this_pmid)
    xml_file.close()

    ###
    # data processing
    # some dp is required as Entrez.read returns a subclassed Dict type with additonal xml data as attributes. These are not serialised by the json dump so we need to include them in another way.
    ###

    # add asterisk to major mesh headings
    try:
      for this_mesh_heading in pmid_data['MedlineCitation']['MeshHeadingList']:
        this_mesh_heading['MajorTopicYN'] = this_mesh_heading['DescriptorName'].attributes['MajorTopicYN']
    except KeyError:
      pass

    ###
    #
    # end data processing
    #
    ###

    pc.dumpJson(this_pmid, pmid_data, 'raw/pubmed')
    return pmid_data
  except Exception as e:
    logging.warn('Unable to read pmid %s', this_pmid)
    print str(e)
    return None
