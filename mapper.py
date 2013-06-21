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
		self._type_weight = {'firstmatch': 4, 'title': 2, 'text': 1}
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
			
	def tagtext(self, page, text, original_text_type):
		text_type = original_text_type
		matches = []
		self._pages.add(page)
		self._init_storage(text_type, page)
			
		for match in self._tag.GetMatches(text, page, [-26]):
			start, end, entities = match
			term = text[start:end+1].lower()

			for entity in entities:
				entry = entity[1]
				if self._backtrack.is_filtered(entry):
					next
				matches.append("%s\t%s\t%s\t%s" % (text_type, page, entry, term))
				for d in self._backtrack.getparents(entry):
					self._store_entry(text_type, d, page)
				
				# ugly setting type to detech first match in the title				
				if start == 0 and original_text_type == 'title':
					text_type = 'firstmatch'
					self._init_storage(text_type, page)	
				self._store_entry(text_type, entry, page)
				self._page_entry_synonyms[page][entry].add(term)
				text_type = original_text_type	
		return matches

	def _store_entry(self, text_type, entry, page):
		if entry not in self._type_entry_page[text_type]:
			self._type_entry_page[text_type][entry]= set()
		self._type_entry_page[text_type][entry].add(page)
		if entry not in self._type_page_entry_count[text_type][page]:
			self._type_page_entry_count[text_type][page][entry]= 1
		else:
			self._type_page_entry_count[text_type][page][entry]+= 1
		if entry not in self._page_entry_synonyms[page]:
			self._page_entry_synonyms[page][entry]= set()
	
	def _init_storage(self, text_type, page):
		if text_type not in self._type_entry_page:
			self._type_entry_page[text_type] = {}
		if text_type not in self._type_page_entry_count:
			self._type_page_entry_count[text_type] = {}
		if page not in self._type_page_entry_count[text_type]:
			self._type_page_entry_count[text_type][page] = {}
		if page not in self._page_entry_synonyms:
			self._page_entry_synonyms[page] = {}
			
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
			sys.stderr.write("Number of parsed %s entries in %s: %d\n" % (self._dictionary, self._mapping, len(self._pages)))
		
		return mapping
	
