#!/usr/bin/env python

import mapper
import backtrack


b = backtrack.Backtrack("doid", "filter.tsv")
m = mapper.Mapper(b, "doid", "omim", 120.3)

pages = set()
type_page_text = {}
type_page_text["title"] = {}
type_page_text["text"] = {}

for line in open("omim_corpus.tsv"):
	page, block, text = line[:-1].split("\t")
	pages.add(page)
	if block == "TITLE":
		type_page_text["title"][page] = text
	elif block == "TEXT":
		type_page_text["text"][page] = text

OUT2 = open("omim_matches.tsv", "w")

type_entry_page = {}
type_page_entry_count = {}

for t in type_page_text:
	type_entry_page[t] = {}
	type_page_entry_count[t] = {}
	for page in type_page_text[t]:
		text = type_page_text[t][page]
		match = m.tagtext(page, text, t)
		OUT2.write("\n".join(match))
OUT2.close()

raw_mappings = m.getmapping()

for docid in raw_mappings.iterkeys():
	data = raw_mappings[docid]
	print "%f\t%s\t%s\t%s\t%s" % (data.score, docid, data.entry, "|".join(data.synonyms), type_page_text["title"][docid])

#raw_mappings = m.getmapping()
#
#lowest = 10000
#highest = 0
#
#mappings = {}
#
#for rm in raw_mappings.iterkeys():
#	uniprot_id, omim_id = rm.split("#")
#	if uniprot_id not in mappings:
#		mappings[uniprot_id] = list()
#	mappings[uniprot_id].append(raw_mappings[rm])
#	score = float(raw_mappings[rm].score)
#	if score < lowest:
#		lowest = score
#	if score > highest:
#		highest = score
#		
#dictionary_path = "/home/purple1/dictionary"
#
#serial_type = {}
#serial_entity = {}
#
#for line in open("%s/stitch_entities.tsv" % dictionary_path):
#	serial, type1, entity = line[:-1].split("\t")
#	serial_type[serial] = type1
#	serial_entity[serial] = entity
#
#for line in open("%s/stitch_names.tsv" % dictionary_path):
#	serial, name, priority = line[:-1].split("\t")
#	if name in mappings and (serial_type[serial] == "9606"):
#		linkout = "http://www.uniprot.org/uniprot/%s" % name
#		for mapping in mappings[name]:
#			stars = 2 + 3 * (float(mapping.score - lowest) / ((highest - lowest) * 0.32))
#			if stars > 5.0:
#				stars = 5.0
#			doid = mapping.entry
#			print "%s\t%s\t-26\t%s\tUniProtKB\tTEXT\t%s\tTRUE\t%s" % (serial_type[serial], serial_entity[serial], doid, stars, linkout)
#			for parent in b.getparents(doid):
#				print "%s\t%s\t-26\t%s\tUniProtKB\tTEXT\t%s\tFALSE\t%s" % (serial_type[serial], serial_entity[serial], parent, stars, linkout)