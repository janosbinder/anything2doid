#!/usr/bin/env python

import os
import re
import sys
import math
import backtrack
import mapper

b = backtrack.Backtrack("doid", "filter.tsv")
m = mapper.Mapper(b, "doid", "omim", 120.3, True)

re_disease_link = re.compile("(.*?), ?(\d+) \(\d+\)")
re_last_number  = re.compile(" \(\d\)$")
re_remove_chars = re.compile("[{}\[\]|]")

ignored_omim = set()

for line in open("genemap"):
	f = map(str.strip, line[:-1].split("|"))
	title = f[7]
	gene  = f[9]
	diseases = map(str.strip, re_remove_chars.sub("", " ".join(f[13:15])).split(";"))

	links = []
	if len(diseases) == 0:
		pass
	elif len(diseases) == 1:
		links.append((title, gene))
	else:
		for disease in diseases:
			if disease != "":
				match = re_disease_link.match(disease)
				if match:
					links.append((match.group(1), match.group(2)))
				else:
					links.append((re_last_number.sub("", disease), "0"))
				
	if len(links) :
		for disease, mim in links:
			if len(links) > 1:
				ignored_omim.add(mim)
	
#ignore specific labels like beginning with ^ (moved to) and * (pure genes)
re_info = re.compile("\\*FIELD\\* NO\n(\d+)\n\\*FIELD\\* TI\n(([#%+*^]?)\d+ (.*?))\\*FIELD\\* TX\n(.*?)\\*FIELD\\*", re.DOTALL)
re_space_before_number = re.compile("([a-zA-Z]+)(\d+)")
re_remove_with = re.compile(" WITH [^;]*?", re.DOTALL)

omim_title           = {}

for document in open("omim.txt").read().split("*RECORD*")[1:]:
	info = re_info.search(document)
	symbol = info.group(3).strip()
	omim = int(info.group(1).strip())
	if symbol != "^" and symbol != "*" and omim not in ignored_omim:
		title  = re_space_before_number.sub("\\1 \\2", re_remove_with.sub(" ",info.group(4)).strip().replace(",", "").replace(";;", ". ").replace("\n", " "))
		text   = re_space_before_number.sub("\\1 \\2", info.group(5)).strip().replace(",", "").replace("\n", " ")
		docid  = "OMIM:%d" % omim
		omim_title[docid] = title
		m.tagtext(docid, title, "title")
		m.tagtext(docid, text, "text")

raw_mappings = m.getmapping()

for docid in raw_mappings.iterkeys():
	data = raw_mappings[docid]
	print "%f\t%s\t%s\t%s\t%s" % (data.score, docid, data.entry, "|".join(data.synonyms), omim_title[docid])
