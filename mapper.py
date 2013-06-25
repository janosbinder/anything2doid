#!/usr/bin/env python

import os
import re
import sys
import math
import random
sys.path.append("/home/purple1/textmining/tagger/")
import tagger
import backtrack

class MappingData:
	
	def __init__(self, entity, score, synonyms):
		self.entity = entity
		self.score = score
		self.synonyms = synonyms


class Benchmark:
	
	def __init__(self, benchmark_filename):
		self._expected = {}
		for line in open(benchmark_filename):
			if "#" in line[:-1]:
				continue
			document, entity = line[:-1].strip().split("\t")
			if document in self._expected:
				raise Exception, "Multiple mappings defined for document %s in benchmark file %s." % (document, benchmark_filename)
			self._expected[document] = entity
		
	def get_performance(self, mapping):
		tp = 0
		fp = 0
		fn = 0
		for document in self._expected:
			if document in mapping:
				if mapping[document].entity == self._expected[document]:
				#if mapping[document].entity == random.choice(self._expected.values()):
					tp += 1
				else:
					fp += 1
			else:
				fn += 1
		precision = 0.0
		recall = 0.0
		F1 = 0.0
		if tp+fp > 0:
			precision = float(tp)/(tp+fp)
		if tp+fn > 0:
			recall = float(tp)/(tp+fn)
		if precision+recall > 0:
			F1 = 2*(precision*recall)/(precision+recall)
		return precision, recall, F1
		return precision

class Mapper:
	
	def __init__(self, backtrack, dictionary, mapping, threshold = 0.0, debug = False):
		self._debug = debug
		self._backtrack = backtrack
		self._threshold = threshold
		self._dictionary = dictionary
		self._mapping = mapping
		self._pages = set()
		self._type_entity_page = {}
		self._type_page_entity_count = {}
		self._page_entity_synonyms = {}
		self._tag = tagger.Tagger()
		self._type_weight = {'firstmatch': 3, 'title': 2, 'text': 1}
		self._tag.LoadNames("%s_entities.tsv" % self._dictionary, "%s_names_expanded.tsv" % self._dictionary)
		self._entity_name = self.load_names()
	
	def load_names(self):
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
			
	def tag_text(self, page, text, original_text_type):
		text_type = original_text_type
		matches = []
		self._pages.add(page)
		self._init_storage(text_type, page)
			
		for match in self._tag.GetMatches(text, page, [-26]):
			start, end, entities = match
			term = text[start:end+1].lower()

			for e in entities:
				entity = e[1]
				if self._backtrack.is_filtered(entity):
					next
				matches.append("%s\t%s\t%s\t%s" % (text_type, page, entity, term))
				for d in self._backtrack.getparents(entity):
					self._store_entity(text_type, d, page)
				
				# ugly setting type to detech first match in the title				
				if start == 0 and original_text_type == 'title':
					text_type = 'firstmatch'
					self._init_storage(text_type, page)	
				self._store_entity(text_type, entity, page)
				self._page_entity_synonyms[page][entity].add(term)
				text_type = original_text_type	
		return matches

	def _store_entity(self, text_type, entity, page):
		if entity not in self._type_entity_page[text_type]:
			self._type_entity_page[text_type][entity]= set()
		self._type_entity_page[text_type][entity].add(page)
		if entity not in self._type_page_entity_count[text_type][page]:
			self._type_page_entity_count[text_type][page][entity]= 1
		else:
			self._type_page_entity_count[text_type][page][entity]+= 1
		if entity not in self._page_entity_synonyms[page]:
			self._page_entity_synonyms[page][entity]= set()
	
	def _init_storage(self, text_type, page):
		if text_type not in self._type_entity_page:
			self._type_entity_page[text_type] = {}
		if text_type not in self._type_page_entity_count:
			self._type_page_entity_count[text_type] = {}
		if page not in self._type_page_entity_count[text_type]:
			self._type_page_entity_count[text_type][page] = {}
		if page not in self._page_entity_synonyms:
			self._page_entity_synonyms[page] = {}
			
	def get_mapping(self):
		mapping = {}
		page_entity = {}
		if self._debug:
			DEBUG = open("%s_scores.tsv" % self._mapping, "w")
		for t in self._type_page_entity_count:
			for page in self._type_page_entity_count[t]:
				if page not in page_entity:
					page_entity[page] = {}
				if len(self._type_page_entity_count[t][page]):
					max_count = float(max(self._type_page_entity_count[t][page].values()))
					for entity in self._type_page_entity_count[t][page]:
						count = self._type_page_entity_count[t][page][entity]
						tf = 100 * count / max_count
						idf = math.log10(float(len(self._pages)) / (1 + len(self._type_entity_page[t][entity])))
						score = tf * idf
						score *= self._type_weight[t]
						if self._debug:
							DEBUG.write("%s\t%s\t%f\t%d\t%d\t%d\t%d\t%f\t%s\t%s\n" % (t, page, score, count, max_count, len(self._type_entity_page[t][entity]), len(self._pages), idf, entity, "|".join(self._page_entity_synonyms[page][entity])));
						if entity not in page_entity[page]:
							page_entity[page][entity] = 0
						page_entity[page][entity] += score
		
		if self._debug:
			DEBUG.close()
			DEBUG = open("%s_%s_idf.tsv" % (self._mapping, self._dictionary), "w")
			for t in self._type_entity_page:
				for entity in self._type_entity_page[t]:
					DEBUG.write("%s\t%d\t%d\t%s\n" % (t, len(self._type_entity_page[t][entity]), len(self._pages), entity))
			DEBUG.close()
			DEBUG = open("%s_%s_mapping_full.tsv" % (self._mapping, self._dictionary), "w")
		
		for page in page_entity:
			score_entity = sorted(map(lambda x: (x[1],x[0]), page_entity[page].items()), reverse=True)	
			i = 0
			for score, entity in score_entity:
				synonyms = []
				if len(self._page_entity_synonyms[page][entity]) > 0:
					synonyms = self._page_entity_synonyms[page][entity]
				elif entity in self._entity_name:
					synonyms.append("[%s]" % (self._entity_name[entity]))
				else:
					synonyms.append("[]")
				if i == 0 and score >= self._threshold:
					m = MappingData(entity, score, synonyms)
					mapping[page] = m
				i += 1
				if self._debug:
					DEBUG.write("%s\t%s\t%f\t%s\n" % (page, entity, score, "|".join(synonyms)))
			
		if self._debug:
			DEBUG.close
			sys.stderr.write("Number of parsed %s entries in %s: %d\n" % (self._dictionary, self._mapping, len(self._pages)))
		
		return mapping
