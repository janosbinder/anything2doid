#!/usr/bin/env python

import re
import sys

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
			# print "%s\t%d\t%s\t%s" % (gene, len(links), mim, disease)
			if len(links) > 1:
				ignored_omim.add(mim)
	
#ignore specific labels like beginning with ^ (moved to) and * (pure genes)
re_info = re.compile("\\*FIELD\\* NO\n(\d+)\n\\*FIELD\\* TI\n(([#%+*^]?)\d+ .*?)\\*FIELD\\* TX\n(.*?)\\*FIELD\\*", re.DOTALL)
re_space_before_number = re.compile("([a-zA-Z]+)(\d+)")
re_remove_with = re.compile(" WITH [^;]*?", re.DOTALL)

N = 0
omim_title           = {}
omimtitle_doid_count = {}
doid_omimtitles      = {}
omimtext_doid_count  = {}
doid_omimtexts       = {}

page_title = {}
page_text  = {}

OUT = open("omim_corpus.tsv", "w")
for document in open("omim.txt").read().split("*RECORD*")[1:]:
	info = re_info.search(document)
	symbol = info.group(3).strip()
	omim = int(info.group(1).strip())
	if symbol != "^" and symbol != "*" and omim not in ignored_omim:
		N += 1
		title  = re_space_before_number.sub("\\1 \\2", re_remove_with.sub(" ",info.group(2)).strip().replace(",", "").replace(";;", ". ").replace("\n", " "))
		text   = re_space_before_number.sub("\\1 \\2", info.group(4)).strip().replace(",", "").replace("\n", " ")
		docid  = "OMIM:%d" % omim
		OUT.write("%s\tTITLE\t%s\n" % (docid, title))
		OUT.write("%s\tTEXT\t%s\n" % (docid, text))
OUT.close()
