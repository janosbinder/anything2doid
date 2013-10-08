#!/usr/bin/env python

import os
import re
import sys
import math
import backtrack
import omimmapper as mapper
import benchmark

DEBUG_MODE = False

def parse_title(title):
	re_remove_with = re.compile(",? WITH [^;]*", re.DOTALL)
	re_acronym_and_newline = re.compile("; ([a-zA-Z0-9]+) ?\n", re.DOTALL)

	original_titles = title.split(";;")
	titles_types = {}
	intermediate_titles = {}

	# split the titles (disgusting OMIM format)
	i = 0
	for t in original_titles:
		if ((i == 0 and re_acronym_and_newline.search(t))):
			parts = t.split("\n")
			for part in parts:
				if i == 0:
					intermediate_titles[part] = "first_title"
				else:
					intermediate_titles[part] = "title"
				i += 1
			continue
		if i == 0:
			intermediate_titles[t] = "first_title"
		else:
			intermediate_titles[t] = "title"
		i += 1
	
	for it, title_type in intermediate_titles.iteritems():
		derived_titles = []
		titles = []
		# skip empty lines
		if it.strip() == "" or it.strip() == "\n":
			continue
		
		# remove new lines and trailing whitespaces
		it = it.replace("\n", " ").strip()
		
		# remove everything with "With ..."
		it = re_remove_with.sub("", it)
		
		# handle diseases with AND
		if it.find(" AND ") > 0:
			and_titles = []
			parts = it.split(" AND ")
			lastpart = parts.pop()
			for part in parts:
				tparts = part.split(", ")
				and_titles.extend(list(tparts))
			and_titles.append(lastpart)
			for at in and_titles:
				titles_types[at] = "and_title"
		
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
		
		for title in handle_numbers(titles):
			titles_types[title] = title_type
		if title_type == "title":
			title_type = "derived_title"
		for title in handle_numbers(derived_titles):
			titles_types[title] = title_type
	return titles_types
			


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
		# keep also original title
		#ot = t
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
		# add also original title
		#if(ot.strip() != ""):
			#titles.append(ot)
	return titles

if __name__ == "__main__":
	
	b = backtrack.Backtrack("doid", "filter.tsv")
	m = mapper.Mapper(b, "doid", "omim", 0, do_backtrack = False, debug = DEBUG_MODE)
	
	re_disease_link = re.compile("(.*?), ?(\d+) \(\d+\)")
	re_last_number  = re.compile(" \(\d\)$")
	re_remove_chars = re.compile("[{}\[\]|]")
	
	ignored_omim = set()
	#ignored_omim = set()
	
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
	
	if DEBUG_MODE:
		DEBUG_FILTER = set()
		#DEBUG_FILTER.add(144700)
		#DEBUG_FILTER.add(608569)
		#DEBUG_FILTER.add(614684)
		#DEBUG_FILTER.add(615087)
		#DEBUG_FILTER.add(106150)
		#DEBUG_FILTER.add(159900)
		#DEBUG_FILTER.add(253320)
		#DEBUG_FILTER.add(136120)
		#DEBUG_FILTER.add(600046)
		#DEBUG_FILTER.add(612098)
		#DEBUG_FILTER.add(302802)
		#DEBUG_FILTER.add(217090)
		#DEBUG_FILTER.add(310000)
		#DEBUG_FILTER.add(258100)
		
	MATCHES = open("omim_matches.tsv", "w")
	TITLES = open("omim_titles.tsv", "w")
	for document in open("omim.txt").read().split("*RECORD*")[1:]:
		info = re_info.search(document)
		symbol = info.group(3).strip()
		omim = int(info.group(1).strip())
		if DEBUG_MODE and (omim not in DEBUG_FILTER):
			continue
		title = info.group(4)
		titles = []
		titles_types = parse_title(title)
		for key, value in titles_types.iteritems():
			if value == "first_title":
				titles.append(key)		
		if symbol != "^" and symbol != "*" and omim not in ignored_omim:
			text   = re_space_before_number.sub("\\1 \\2", info.group(5)).strip().replace(",", "").replace("\n", " ")
			docid  = "OMIM:%d" % omim
			omim_title[docid] = ";; ".join(titles)
			if "and_title" not in titles_types.values():
				i = 0
				for t, t_type in titles_types.iteritems():
					TITLES.write("%s\t%s\t#%s\t%s\n" % (docid, t_type, i, t))
					if DEBUG_MODE:
						print "%s: Passing title %s (type %s) for tagging" % (docid, t, t_type)
					matches = m.tag_text(docid, t, t_type)
					for te in matches:
						MATCHES.write("%s\t%s\t%s\n" % (docid, t, te))
					i += 1
			else:
				i = 0
				for t, t_type in titles_types.iteritems():
					if t_type == "and_title":
						and_id = "%s#%d" % (docid, i)
						omim_title[and_id] = t
						TITLES.write("%s\t%s\t#%s\t%s\n" % (and_id, t_type, i, t))
						matches = m.tag_text(and_id, t, t_type)
						for te in matches:
							MATCHES.write("%s\t%s\t%s\n" % (and_id, t, te))				
						i += 1
			#m.tag_text(docid, text, "text")
	TITLES.close()
	MATCHES.close()
	
	raw_mapping = m.get_mapping()
	
	sys.stderr.write(str(benchmark.Benchmark(b, "omim_benchmark.tsv").get_performance(raw_mapping)))
	#sys.exit()
	
	for docid in raw_mapping.iterkeys():
		data = raw_mapping[docid]
		print "%f\t%s\t%s\t%s\t%s" % (data.score, docid, data.entity, "|".join(data.synonyms), omim_title[docid])

