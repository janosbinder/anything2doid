#!/usr/bin/env python

import os
import re
import sys
import math
sys.path.append("/home/purple1/textmining/tagger/")
import tagger
import backtrack

class MappingData:
	def __init__(self, entry, score, synonyms):
		self.entry = entry
		self.score = score
		self.synonyms = synonyms
	

class Mapper:
	def __init__(self, backtrack, dictionary, mapping, threshold = 0.0, debug = False):
		self._debug = debug
		self._backtrack = backtrack
		self._threshold = threshold
		self._dictionary = dictionary
		self._mapping = mapping
		self._pages = set()
		self._type_entry_page = {}
		self._type_page_entry_count = {}
		self._page_entry_synonyms = {}
		self._tag = tagger.Tagger()
		self._type_weight = {'text': 1, 'title': 5}
		self._tag.LoadNames("%s_entities.tsv" % self._dictionary, "%s_names_expanded.tsv" % self._dictionary)
		self._entity_name = self.loadnames()
	
	def loadnames(self):
		id_entity = {}
		entity_name = {}
		for line in open("%s_entities.tsv" % self._dictionary):
			f = map(str.strip, line[:-1].split("\t"))
			id_entity[f[0]] = f[2]
		
		for line in open("%s_names.tsv" % self._dictionary):
			f = map(str.strip, line[:-1].split("\t"))
			if(int(f[2]) < 2):
				entity_name[id_entity[f[0]]] = f[1]
		return entity_name
			
	def tagtext(self, page, text, text_type):
		matches = []
		self._pages.add(page)
		if text_type not in self._type_entry_page:
			self._type_entry_page[text_type] = {}
		if text_type not in self._type_page_entry_count:
			self._type_page_entry_count[text_type] = {}
		if page not in self._type_page_entry_count[text_type]:
			self._type_page_entry_count[text_type][page] = {}
		if page not in self._page_entry_synonyms:
			self._page_entry_synonyms[page] = {}
		for match in self._tag.GetMatches(text, page, [-26]):
			start, end, entities = match
			term = text[start:end+1].lower()
			for entity in entities:
				entry = entity[1]
				if self._backtrack.is_filtered(entry):
					next
				matches.append("%s\t%s\t%s\t%s" % (text_type, page, entry, term))
				for d in self._backtrack.getparents_and_entry(entry):
					if d not in self._type_entry_page[text_type]:
						self._type_entry_page[text_type][d] = set()
					self._type_entry_page[text_type][d].add(page)
					if d not in self._type_page_entry_count[text_type][page]:
						self._type_page_entry_count[text_type][page][d] = 1
					else:
						self._type_page_entry_count[text_type][page][d] += 1
					if d not in self._page_entry_synonyms[page]:
						self._page_entry_synonyms[page][d] = set()
				self._page_entry_synonyms[page][entry].add(term)
		return matches

	def getmapping(self):
		mapping = {}
		page_entry = {}
		if self._debug:
			DEBUG = open("%s_scores.tsv" % self._mapping, "w")
		for t in self._type_page_entry_count:
			for page in self._type_page_entry_count[t]:
				if page not in page_entry:
					page_entry[page] = {}
				if len(self._type_page_entry_count[t][page]):
					max_count = float(max(self._type_page_entry_count[t][page].values()))
					for entry in self._type_page_entry_count[t][page]:
						count = self._type_page_entry_count[t][page][entry]
						tf = 100 * count / max_count
						idf = math.log10(float(len(self._pages)) / (1 + len(self._type_entry_page[t][entry])))
						score = tf * idf
						score *= self._type_weight[t]
						if self._debug:
							DEBUG.write("%s\t%s\t%f\t%d\t%d\t%d\t%d\t%f\t%s\t%s\n" % (t, page, score, count, max_count, len(self._type_entry_page[t][entry]), len(self._pages), idf, entry, "|".join(self._page_entry_synonyms[page][entry])));
						if entry not in page_entry[page]:
							page_entry[page][entry] = 0
						page_entry[page][entry] += score
		
		if self._debug:
			DEBUG.close()
			DEBUG = open("%s_%s_idf.tsv" % (self._mapping, self._dictionary), "w")
			for t in self._type_entry_page:
				for entry in self._type_entry_page[t]:
					DEBUG.write("%s\t%d\t%d\t%s\n" % (t, len(self._type_entry_page[t][entry]), len(self._pages), entry))
			DEBUG.close()
			DEBUG = open("%s_%s_mapping_full.tsv" % (self._mapping, self._dictionary), "w")
		
		for page in page_entry:
			score_entry = sorted(map(lambda x: (x[1],x[0]), page_entry[page].items()), reverse=True)	
			i = 0
			for score, entry in score_entry:
				synonyms = []
				if len(self._page_entry_synonyms[page][entry]) > 0:
					synonyms = self._page_entry_synonyms[page][entry]
				elif entry in self._entity_name:
					synonyms.append("[%s]" % (self._entity_name[entry]))
				else:
					synonyms.append("[]")
				if i == 0 and score >= self._threshold:
					m = MappingData(entry, score, synonyms)
					mapping[page] = m
				i += 1
				if self._debug:
					DEBUG.write("%s\t%s\t%f\t%s\n" % (page, entry, score, "|".join(synonyms)))
			
		if self._debug:
			DEBUG.close
			print "Number of parsed %s entries in %s: %d\n" % (self._dictionary, self._mapping, len(self._pages))
		
		return mapping
	
