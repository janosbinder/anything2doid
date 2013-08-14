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

class TaggedEntity:

	def __init__(self, entity, start, end, term, text_type):
		self.entity = entity
		self.start = start
		self.end = end
		self.text_type = text_type
		self.term = term
		
	def __str__(self):
		return "%s\t%s\t%s\t%d\t%d" % (self.text_type, self.entity, self.term, self.start, self.end)

class Mapper:
	
	def __init__(self, backtrack, dictionary, mapping, threshold = 0.0, do_backtrack = False, debug = False):
		self._debug = debug
		self._backtrack = backtrack
		self._do_backtrack = do_backtrack
		self._threshold = threshold
		self._dictionary = dictionary
		self._mapping = mapping
		self._pages = set()
		self._page_entity = {}
		self._tag = tagger.Tagger()
		self._max_tokens = 15
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
		if page not in self._page_entity:
			self._page_entity[page] = []
			
		for match in self._tag.GetMatches(text, page, [-26], max_tokens = self._max_tokens):
			start, end, entities = match
			term = text[start:end+1].lower()
			for e in entities:
				entity = e[1]
				matches.append(TaggedEntity(entity, start, end, term, text_type))
				self._page_entity[page].append(TaggedEntity(entity, start, end, term, text_type))
		return matches
		
	def get_mapping(self):
		mapping = {}
		for page in self._page_entity:
			tagged_entities = self._page_entity[page]
			ignore = False
			candidates = []
			i=0
			while i < len(tagged_entities):
				# do not add if any children has been tagged
				j=0
				while j < len(tagged_entities):
					if j == i:
						j+=1
						continue
					if self._backtrack.is_parent(tagged_entities[j].entity, tagged_entities[i].entity):
						ignore = True
					j+=1
				if ignore != True:
					candidates.append(tagged_entities[i])
				i+=1
						
			if len(candidates) > 1:
				# check position of matches, keep if matches from the first character
				candidates = filter(lambda x: True if x.start == 0 else False, candidates)
				#new_candidates = []
				#for candidate in candidates:
				#	if candidate.start == 0:
				#		new_candidates.append(candidate)
				#candidates = new_candidates
			
			if len(candidates) > 1:
				# check whether it is an original title, keep if it is the only title
				candidates = filter(lambda x: True if x.text_type == "title" else False, candidates)
				#new_candidates = []
				#for candidate in candidates:
				#	if candidate.text_type == "title":
				#		new_candidates.append(candidate)
				#candidates = new_candidates
			
			if len(candidates) > 1:
				# get rid of duplicate entries
				seen = set()
				new_candidates = []
				for candidate in candidates:
					if candidate.entity in seen:
						continue
					seen.add(candidate.entity)
					new_candidates.append(candidate)
				candidates = new_candidates
				
			if len(candidates) > 1:
				raise Exception("There are more than entities to map at %s: %s" % (page, ";".join(map(str,candidates))))
			
			if len(candidates) == 1:
				mapping[page] = MappingData(candidates[0].entity, 0, [candidates[0].term])		

		
		return mapping
