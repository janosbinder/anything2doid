#!/usr/bin/env python

import os
import re
import sys
import math

import backtrack
import omimmapper as mapper

def parse_title(title):
	re_remove_with = re.compile(",? WITH [^;]*?", re.DOTALL)
	re_acronym_and_newline = re.compile("; ([a-zA-Z0-9]+) ?\n", re.DOTALL)

	original_titles = title.split(";;")
	titles = []
	derived_titles = []
	intermediate_titles = []
	# TODO: handle multiple diseases in a separate list. These are with AND


	# split the titles (disgusting OMIM format)
	i = 0
	for t in original_titles:
		if ((i == 0 and re_acronym_and_newline.search(t))):
			intermediate_titles.extend(t.split("\n"))
			i += 1
			continue
			
		intermediate_titles.append(t)
		i += 1
	
	for it in intermediate_titles:
		# skip empty lines
		if it.strip() == "" or it.strip() == "\n":
			continue
		
		# remove new lines and trailing whitespaces
		it = it.replace("\n", " ").strip()
		
		# remove everything with "With ..."
		it = re_remove_with.sub(" ", it)
		
		# check for acronyms, and handle them as a title
		acronym = ""
		a = it.split("; ")
		if len(a) > 1:
			acronym = a[1]
			it = a[0]

		# reverse titles with adjectives, and generate two varians if there are multiple adjectives
		parts = it.split(", ")
								
		if len(parts) > 1 and parts[1].find("TYPE") < 0:
			ending = ""
			if(len(parts) > 2):
				ending = " " + " ".join(parts[2:])
		
			adjectives = parts[1].split(" ")			
			if len(adjectives) == 2:
				derived_titles.append("%s %s %s%s" % (adjectives[0], adjectives[1], parts[0], ending)) # Permutating adjectives: (1, 2)
				derived_titles.append("%s %s %s%s" % (adjectives[1], adjectives[0], parts[0], ending)) # Permutating adjectives: (2, 1)
			else:
				derived_titles.append("%s %s%s" % (parts[1], parts[0], ending)) # More than two adjectives or just one results in a permuation of the noun and adjective only.

		# store original title
		titles.append(it.replace(",", ""))
		# store acronyms
		if (acronym != ""):
			titles.append(acronym)
			
	return (handle_numbers(titles), handle_numbers(derived_titles))
			


def handle_numbers(original_titles):
	re_space_before_number = re.compile("([a-zA-Z]{2,})(\d+)") # to separate acronyms from numbers
	re_number_letter_separator = re.compile("(\d+)([a-zA-Z])") # to separate type 1a to type 1
	roman_arabic = {
		'I': '1',
		'II': '2',
		'III': '3',
		'IV': '4',
		'V': '5',
		'VI': '6',
		'VII': '7',
		'VIII': '8',
		'IX': '9',
		'X': '10'
		}
	
	
	titles = []
	for t in original_titles:
		# change Roman numbers to arabic numbers
		for number in roman_arabic:
			roman_pattern = re.compile(r' ' + number)
			for m in roman_pattern.finditer(t):
				# apply the pattern depening on where did matched.
				if len(t) == m.end():
					# Match of roman number at the end of title.
					pattern = re.compile(r' ' + number)	
					t = pattern.sub(" " + roman_arabic[number], t, 1)
				elif len(t) - 1 == m.end():
					# Match of roman number one character before at the end of title.
					pattern = re.compile(r' ' + number + r'(( \w)|([a-zA-H]))')	
					t = pattern.sub(" " + roman_arabic[number] + "\\1", t, 1)
				else:
					# Match but not at the end.
					pattern = re.compile(r' ' + number + r'(( \w)|([a-zA-H]?:(\w+)))')	
					t = pattern.sub(" " + roman_arabic[number] + "\\1", t, 1)
				
		# split integer and letter e.g. type 1A -> type 1 A, and acronyms like ABC2 to ABC 2
		t = re_space_before_number.sub("\\1 \\2", t)
		if(re_number_letter_separator.search(t)):
			titles.append(re_number_letter_separator.sub("\\1",t))
		if(t.strip() != ""):
			titles.append(t)
	return titles

if __name__ == "__main__":
	
	b = backtrack.Backtrack("doid", "filter.tsv")
	m = mapper.Mapper(b, "doid", "omim", 0, do_backtrack = False, debug = True)
	
	re_disease_link = re.compile("(.*?), ?(\d+) \(\d+\)")
	re_last_number  = re.compile(" \(\d\)$")
	re_remove_chars = re.compile("[{}\[\]|]")
	
	ignored_omim = set()
	
	#ignore specific labels like beginning with ^ (moved to) and * (pure genes)
	re_info = re.compile("\\*FIELD\\* NO\n(\d+)\n\\*FIELD\\* TI\n(([#%+*^]?)\d+ (.*?))\\*FIELD\\* TX\n(.*?)\\*FIELD\\*", re.DOTALL)
	re_space_before_number = re.compile("([a-zA-Z]+)(\d+)") # to separate acronyms from numbers

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
		
	omim_title = {}
	
	#DEBUG_FILTER = set()
	#DEBUG_FILTER.add(612098)
	#DEBUG_FILTER.add(611878)
	#DEBUG_FILTER.add(613721)
	#DEBUG_FILTER.add(601318)
	#DEBUG_FILTER.add(125700)
	#DEBUG_FILTER.add(604377)
	#DEBUG_FILTER.add(273120)
		
	MATCHES = open("omim_matches.tsv", "w")
	TITLES = open("omim_titles.tsv", "w")
	for document in open("omim.txt").read().split("*RECORD*")[1:]:
		info = re_info.search(document)
		symbol = info.group(3).strip()
		omim = int(info.group(1).strip())
		#if omim not in DEBUG_FILTER:
		#	continue
		title = info.group(4)
		titles, derived_titles = parse_title(title)
		if symbol != "^" and symbol != "*" and omim not in ignored_omim:
			text   = re_space_before_number.sub("\\1 \\2", info.group(5)).strip().replace(",", "").replace("\n", " ")
			docid  = "OMIM:%d" % omim
			omim_title[docid] = ";; ".join(titles)
			i = 0
			for t in titles:
				TITLES.write("%s\ttitle\t#%s\t%s\n" % (docid, i, t))
				#print >> sys.stderr, omim, t
				#print >> sys.stderr, omim, ";".join(m.tag_text(docid, t, "title"))
				matches = m.tag_text(docid, t, "title")
				for te in matches:
					MATCHES.write("%s\t%s\t%s\n" % (docid, t, te))
				i += 1
			for dt in derived_titles:
				TITLES.write("%s\tderived_title\t#%s\t%s\n" % (docid, i, dt))
				#print >> sys.stderr, omim, ";".join(m.tag_text(docid, dt, "derived_title"))
				matches = m.tag_text(docid, dt, "derived_title")
				for te in matches:
					MATCHES.write("%s\t%s\t%s\n" % (docid, dt, te))
				i += 1				
			#m.tag_text(docid, text, "text")
	TITLES.close()
	MATCHES.close()
	
	raw_mapping = m.get_mapping()
	
	#sys.stderr.write(str(mapper.Benchmark("omim_benchmark.tsv").get_performance(raw_mapping)))
	#sys.exit()
	
	for docid in raw_mapping.iterkeys():
		data = raw_mapping[docid]
		print "%f\t%s\t%s\t%s\t%s" % (data.score, docid, data.entity, "|".join(data.synonyms), omim_title[docid])

