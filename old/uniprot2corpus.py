#!/usr/bin/env python

import os
import re
import sys
import math

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

OUT1 = open("uniprot_corpus.tsv", "w")
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
		OUT1.write("%s\tTITLE\t%s\n" % (page, sentences[0]))
		OUT1.write("%s\tTEXT\t%s\n" % (page, ". ".join(sentences[1:])))
		i += 1
	for linkout in linkouts:
		OUT2.write("%s\t%d\tDR-FIELD\n" % (protein, int(linkout)))
OUT1.close()
OUT2.close()
