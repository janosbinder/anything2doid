#!/usr/bin/env python

import os
import re
import sys
import math
import getopt
sys.path.append("/home/purple1/textmining/tagger/")
import tagger

threshold = 0

# -t threshold -m mapping -d dictionary
try:
	opts, args = getopt.getopt(sys.argv[1:], "t:m:d:f:")
except getopt.GetoptError, e:
	print >> sys.stderr, str(e)
	sys.exit(1)

entry_filter = ""

for o,a in opts:
	if o == "-t":
		threshold = float(a)
	elif o == "-m":
		mapping = a
		#if not os.path.isfile(corpus_filename):
		#	print >> sys.stderr, "%s does not exits." % corpus_filename
		#	sys.exit(2)
	elif o == "-d":
		dictionary = a
	elif o == "-f":
		dictionary_filter = a

tag = tagger.Tagger()
tag.LoadNames("%s_entities.tsv" % dictionary, "%s_names_expanded.tsv" % dictionary)

#check ignore stuff

entry_filter = {}
if not os.path.isfile(dictionary_filter):
	for line in open(dictionary_filter):
		f = line[:-1].split("\t")
		entry_filter[f[0]] = f[1]

serial_entity = {}
for line in open("%s_entities.tsv" % dictionary):
	serial, t, entry = line[:-1].split("\t")
	serial_entity[serial] = entry

child_parent = {}
parent_child = {}

for line in open("%s_groups.tsv" % dictionary):
	f = line[:-1].split("\t")
	child, parent = serial_entity[f[0]], serial_entity[f[1]]
	if child not in child_parent:
		child_parent[child] = set()
	child_parent[child].add(parent)
	if parent not in child_parent:
		child_parent[parent] = set()
	if parent in entry_filter and entry_filter[parent] == "*" and child not in entry_filter:
		entry_filter[child] = "1"
	if parent not in parent_child:
		parent_child[parent] = set()
	parent_child[parent].add(child)
	if child not in parent_child:
		parent_child[child] = set()

page_text = {}
page_title = {}
pages = set()

for line in open("%s_corpus.tsv" % mapping):
	page, block, text = line[:-1].split("\t")
	pages.add(page)
	if block == "TITLE":
		page_title[page] = text
	elif block == "TEXT":
		page_text[page] = text

N = 0
entry_pagetitles = {}
entry_pagetexts = {}
pagetitle_entry_count = {}
pagetext_entry_count = {}
page_entry_synonyms = {}

OUT2 = open("%s_matches_title.tsv" % mapping, "w")
OUT3 = open("%s_matches_text.tsv" % mapping, "w")
for page in pages:
	N += 1
	# title part
	pagetitle_entry_count[page] = {}
	page_entry_synonyms[page]  = {}
	text = page_title[page]
	for match in tag.GetMatches(text, page, [-26]):
		start, end, entities = match
		term = text[start:end+1].lower()
		for entity in entities:
			entry = entity[1]
			if entry in entry_filter:
				next
			OUT2.write("%s\t%s\t%s\n" % (page, entry, term))
			for d in child_parent[entry].union([entry]):
				if d not in entry_pagetitles:
					entry_pagetitles[d] = set()
				entry_pagetitles[d].add(page)
				if d not in pagetitle_entry_count[page]:
					pagetitle_entry_count[page][d] = 1
				else:
					pagetitle_entry_count[page][d] += 1
				if d not in page_entry_synonyms[page]:
					page_entry_synonyms[page][d] = set()
			page_entry_synonyms[page][entry].add(term)
	# text part
	pagetext_entry_count[page] = {}
	text = page_text[page]
	for match in tag.GetMatches(text, page, [-26]):
		start, end, entities = match
		term = text[start:end+1].lower()
		for entity in entities:
			entry = entity[1]
			if entry in entry_filter:
				next
			OUT3.write("%s\t%s\t%s\n" % (page, entry, term))
			for d in child_parent[entry].union([entry]):
				if d not in entry_pagetexts:
					entry_pagetexts[d] = set()
				entry_pagetexts[d].add(page)
				if d not in pagetext_entry_count[page]:
					pagetext_entry_count[page][d] = 1
				else:
					pagetext_entry_count[page][d] += 1
				if d not in page_entry_synonyms[page]:
					page_entry_synonyms[page][d] = set()
			page_entry_synonyms[page][entry].add(term)

OUT2.close()
OUT3.close()

OUT1 = open("%s_scores_title.tsv" % mapping, "w")
OUT2 = open("%s_scores_text.tsv" % mapping, "w")

page_entry = {}

for page in pagetitle_entry_count:
	if page not in page_entry:
		page_entry[page] = {}
	if len(pagetitle_entry_count[page]):
		max_count = float(max(pagetitle_entry_count[page].values()))
		for entry in pagetitle_entry_count[page]:
			count = pagetitle_entry_count[page][entry]
			tf = 100 * count / max_count
			idf = math.log10(float(N) / (1 + len(entry_pagetitles[entry])))
			score = tf * idf
			OUT1.write("%s\t%f\t%d\t%d\t%d\t%d\t%f\t%s\t%s\n" % (page, score, count, max_count, len(entry_pagetitles[entry]), N, idf, entry, "|".join(page_entry_synonyms[page][entry])))
			if entry not in page_entry[page]:
				page_entry[page][entry] = 0
			page_entry[page][entry] += score
			
for page in pagetext_entry_count:
	if page not in page_entry:
		page_entry[page] = {}
	if len(pagetext_entry_count[page]):
		max_count = float(max(pagetext_entry_count[page].values()))
		for entry in pagetext_entry_count[page]:
			count = pagetext_entry_count[page][entry]
			tf = 100 * count / max_count
			idf = math.log10(float(N) / (1 + len(entry_pagetexts[entry])))
			score = tf * idf
			OUT2.write("%s\t%f\t%d\t%d\t%d\t%d\t%f\t%s\t%s\n" % (page, score, count, max_count, len(entry_pagetexts[entry]), N, idf, entry, "|".join(page_entry_synonyms[page][entry])))
			if entry not in page_entry[page]:
				page_entry[page][entry] = 0
			page_entry[page][entry] += score

OUT1.close()
OUT2.close()

OUT1 = open("%s_%s_idf_title.tsv" % (mapping, dictionary), "w")
OUT2 = open("%s_%s_idf_text.tsv" % (mapping, dictionary), "w")
for entry in entry_pagetitles:
	OUT1.write("%d\t%d\t%s\n" % (len(entry_pagetitles[entry]), N, entry))
	
for entry in entry_pagetexts:
	OUT2.write("%d\t%d\t%s\n" % (len(entry_pagetexts[entry]), N, entry))

OUT1.close()
OUT2.close()

OUT1 = open("%s_%s_mapping_full.tsv" % (mapping, dictionary), "w")
OUT2 = open("%s_%s_mapping.tsv" % (mapping, dictionary), "w")
OUT3 = open("%s_%s_diversity_index.tsv" % (mapping, dictionary), "w")
OUT4 = open("%s_%s_mapping_diversity.tsv" % (mapping, dictionary), "w")
for page in page_entry:
	score_entry = sorted(map(lambda x: (x[1],x[0]), page_entry[page].items()), reverse=True)
	
	i = 0
	for score, entry in score_entry:
		if i == 0 and score >= threshold:
			OUT2.write("%f\t%s\t%s\t%s\t%s\n" % (score, page, entry, "|".join(page_entry_synonyms[page][entry]), page_title[page]))
		OUT1.write("%f\t%s\t%s\t%s\n" % (score, page, entry, "|".join(page_entry_synonyms[page][entry])))
		i += 1

	seen = set()
	scores = {}
	for score, entry in score_entry:
		if score >= threshold and not entry in seen:
			seen.add(entry)
			scores[entry] = score
			for parent in child_parent[entry]:
				seen.add(parent)
			for child in parent_child[entry]:
				seen.add(child)
	
	sum_score = sum(scores.values())
	if sum_score > 0:
		diversity = 1.0/sum(map(lambda x: (x/sum_score)**2, scores.values()))
		OUT3.write("%f\t%s\n" % (diversity, page))
		for score, entry in sorted(map(lambda x: (x[1],x[0]), scores.items()))[:int((round(diversity)))]:
			OUT4.write("%f\t%f\t%d\t%s\t%s\t%s\n" % (scores[entry], diversity, len(scores), page, entry, "|".join(page_entry_synonyms[page][entry])))

OUT1.close()
OUT2.close()
OUT3.close()
OUT4.close()

print "Number of parsed %s entries in %s: %d\n" % (dictionary, mapping, N) 

