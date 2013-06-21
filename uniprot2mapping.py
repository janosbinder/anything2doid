#!/usr/bin/env python

import os
import re
import sys
import math
import backtrack
import mapper

b = backtrack.Backtrack("doid", "filter.tsv")
m = mapper.Mapper(b, "doid", "uniprot", 201)

#ignore specific labels like beginning with ^ (moved to) and * (pure genes)
#re_info = re.compile("ID (\w+).*?(CC   -!- DISEASE:(.*?)CC   -!-)?.*?(DR   (MIM[^.]))*", re.DOTALL)
re_document = re.compile("ID.*?//\n", re.DOTALL)
re_entry    = re.compile("ID   (\w+)", re.DOTALL)
re_cc       = re.compile("CC   -!- DISEASE:(.*?)(?=CC   -[!-]-)", re.DOTALL)
re_linkout  = re.compile("DR   MIM; (\d+); phenotype\.")
re_omim     = re.compile("\[MIM:(\d+)\]")

protein_omims = {}
protein_page_texts = {}
pages = set()
page_text = {}
proteins = set()

OUT2 = open("uniprot_text_omim.tsv", "w")
for document in re_document.findall(open("uniprot_sprot.dat").read()):
	info = re_entry.search(document)
	protein = info.group(1).strip()
	linkouts = re_linkout.findall(document)
	ccs = re_cc.findall(document)
	i = 0
	if protein not in protein_omims:
			protein_omims[protein] = set()
	for cc in ccs:
		inf = re_omim.search(cc)
		omim = 0
		if inf != None:
			omim = int(inf.group(1))
			OUT2.write("%s\t%d\tCC-FIELD\n" % (protein, omim))
		else:
			omim = i
		text = cc.strip().replace("CC       ","").replace("\n", " ")
		sentences = text.strip().split(". ")
		page = "%s#%s" % (protein, omim)
		if len(sentences) == 0:
			print "%s\t%s" % (page, text)
		m.tagtext(page, sentences[0], "title")
		m.tagtext(page, ". ".join(sentences[1:]), "text")
		i += 1
	for linkout in linkouts:
		OUT2.write("%s\t%d\tDR-FIELD\n" % (protein, int(linkout)))
OUT2.close()

raw_mappings = m.getmapping()

lowest = 10000
highest = 0

mappings = {}

for rm in raw_mappings.iterkeys():
	uniprot_id, omim_id = rm.split("#")
	if uniprot_id not in mappings:
		mappings[uniprot_id] = list()
	mappings[uniprot_id].append(raw_mappings[rm])
	score = float(raw_mappings[rm].score)
	if score < lowest:
		lowest = score
	if score > highest:
		highest = score
		
dictionary_path = "/home/purple1/dictionary"

serial_type = {}
serial_entity = {}

for line in open("%s/stitch_entities.tsv" % dictionary_path):
	serial, type1, entity = line[:-1].split("\t")
	serial_type[serial] = type1
	serial_entity[serial] = entity

for line in open("%s/stitch_names.tsv" % dictionary_path):
	serial, name, priority = line[:-1].split("\t")
	if name in mappings and (serial_type[serial] == "9606"):
		linkout = "http://www.uniprot.org/uniprot/%s" % name
		for mapping in mappings[name]:
			stars = 2 + 3 * (float(mapping.score - lowest) / ((highest - lowest) * 0.32))
			if stars > 5.0:
				stars = 5.0
			doid = mapping.entry
			print "%s\t%s\t-26\t%s\tUniProtKB\tTEXT\t%s\tTRUE\t%s" % (serial_type[serial], serial_entity[serial], doid, stars, linkout)
			for parent in b.getparents(doid):
				print "%s\t%s\t-26\t%s\tUniProtKB\tTEXT\t%s\tFALSE\t%s" % (serial_type[serial], serial_entity[serial], parent, stars, linkout)
