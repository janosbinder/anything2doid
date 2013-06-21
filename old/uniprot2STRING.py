#!/usr/bin/env python

import sys
import os

serial_entity = {}
for line in open("doid_entities.tsv"):
	serial, t, entry = line[:-1].split("\t")
	serial_entity[serial] = entry

child_parent = {}

for line in open("doid_groups.tsv"):
	f = line[:-1].split("\t")
	child, parent = serial_entity[f[0]], serial_entity[f[1]]
	if child not in child_parent:
		child_parent[child] = set()
	child_parent[child].add(parent)
	if parent not in child_parent:
		child_parent[parent] = set()

uniprot = {}
for line in open("uniprot_doid_mapping.tsv"):
	score, uniprot_id, omim_id, doid, term, title = line[:-1].replace("#","\t").split("\t")
	#uniprot[uniprot_id] = [doid, score, omim_id, term, title]
	linkout = "http://www.uniprot.org/uniprot/%s" % uniprot_id
	uniprot[uniprot_id] = [doid, linkout, score]

uniprot_stars = {}
lowest = 10000
highest = 0

for u in uniprot.itervalues():
	score = float(u[2])
	if score < lowest:
		lowest = score
	if score > highest:
		highest = score

# sorted(uniprot.iteritems(), key = lambda (k,v): operator.itemgetter(2)(v))		
for u in uniprot.iterkeys():
	stars = 2 + 3 * (float(uniprot[u][2]) - lowest) / ((highest - lowest) * 0.32)
	uniprot_stars[u] = stars if stars < 5.0 else 5.0

dictionary_path = "/home/purple1/dictionary"

serial_type = {}
serial_entity = {}

for line in open("%s/stitch_entities.tsv" % dictionary_path):
	serial, type1, entity = line[:-1].split("\t")
	serial_type[serial] = type1
	serial_entity[serial] = entity

for line in open("%s/stitch_names.tsv" % dictionary_path):
	serial, name, priority = line[:-1].split("\t")
	if name in uniprot and (serial_type[serial] == "9606"):
		doid = uniprot[name][0]
		linkout = uniprot[name][1]
		print "%s\t%s\t-26\t%s\tUniProtKB\tTEXT\t%s\tTRUE\t%s" % (serial_type[serial], serial_entity[serial], doid, uniprot_stars[name], linkout)
		for parent in child_parent[doid]:
			print "%s\t%s\t-26\t%s\tUniProtKB\tTEXT\t%s\tFALSE\t%s" % (serial_type[serial], serial_entity[serial], parent, uniprot_stars[name], linkout)
