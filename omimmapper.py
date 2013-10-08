#!/usr/bin/env python

import os
import re
import sys
import math
sys.path.append("/home/purple1/textmining/tagger/")
import tagger
import backtrack

ignored_entities = set(["DOID:4", "DOID:225"])

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
				#ignore disease or syndrome
				if entity in ignored_entities:
					continue
				matches.append(TaggedEntity(entity, start, end, term, text_type))
				self._page_entity[page].append(TaggedEntity(entity, start, end, term, text_type))
		return matches
		
	def get_mapping(self):
		mapping = {}
		for page in self._page_entity:
			tagged_entities = self._page_entity[page]
			seen = {}
			ignore = False
			candidates = []
			
			#count how often was an entity tagged
			for tagged_entity in tagged_entities:
				if tagged_entity.entity in seen:
					seen[tagged_entity.entity] += 1
				else:
					seen[tagged_entity.entity] = 1
			
			#unite tagged terms, and create one with the strongest properties
			for s in seen:
				if s > 1:
					entities = filter(lambda x: True if x.entity == s else False, tagged_entities)
					united_entity = s
					united_start = 10000
					united_end = 0
					united_term_set = set()
					united_text_type = ""
					for entity in entities:
						if united_start > entity.start:
							united_start = entity.start
						if united_end > entity.end:
							united_end = entity.end
						united_term_set.add(entity.term)
						if united_text_type != "first_title":
							united_text_type = entity.text_type
					united_term = ";".join(list(united_term_set))
					candidates.append(TaggedEntity(united_entity, united_start, united_end, united_term, united_text_type))
					
				if s == 1:
					candidate = filter(lambda x: True if x.entity == s else False, tagged_entities)
					candidates.extend(candidate)
			
			#ignore parents
			cs = []
			i=0
			while i < len(candidates):
				j=0
				while j < len(candidates):
					if j == i:
						j+=1
						continue
					if self._backtrack.is_parent(candidates[j].entity, candidates[i].entity):
						ignore = True
					j+=1
				if ignore != True:
					cs.append(candidates[i])
				i+=1
				ignore = False
			candidates = cs
			
			if self._debug:
				print "Original tagged ID's for %s were:" % (page)
				original = []
				for te in tagged_entities:
					original.append(te.entity)
				print "%s" % (",".join(original))
				print "After filtering parents and removing duplicates:"
				altered = []
				for c in candidates:
					altered.append(c.entity)
				print "%s" % (",".join(altered))
				
			if len(candidates) > 1:
				# ignore the page if the same term name has been tagged (e.g.: dystonia in DOID:543 and DOID:544)
				term_names = {}
				for candidate in candidates:
					if candidate.term in term_names and term_names[candidate.term] != candidate.entity:
						ignore = True
						break
					term_names[candidate.term] = candidate.entity
				if self._debug:
					if ignore:
						print "Unfortunately a term name has been associated with multiple entities, ignoring page"
				
			if len(candidates) > 1:
				# check position of matches, keep if matches from the first character
				cs = filter(lambda x: True if x.start == 0 else False, candidates)
				if(len(cs) != 0):
					candidates = cs
				if self._debug:
					altered = []
					print "After filtering titles not starting at position 0"
					for c in candidates:
						altered.append(c.entity)
					print "%s" % (",".join(altered))
			
			#if len(candidates) > 1 and len(filter(lambda x: True if x.text_type == "title" else False, candidates)) > 0:
				# check whether it is an original title, keep if it is the only title
			#	cs = filter(lambda x: True if x.text_type == "title" else False, candidates)
			#	if(len(cs) != 0):
			#		candidates = cs			
			#	if self._debug:
			#		altered = []
			#		print "After filtering out derived titles"
			#		for c in candidates:
			#			altered.append(c.entity)
			#			print "%s" % (",".join(altered))
			#
			if len(candidates) > 1:
				#check whether title is the first title (main title)
				firsttitles = list()
				for candidate in candidates:
					if candidate.text_type == "first_title":
						firsttitles.append(candidate)
				if len(firsttitles) > 0:
					candidates = firsttitles
				if self._debug:
					print "After choosing the match from the first title"
					altered = []
					for c in candidates:
						altered.append(c.entity)
					print "%s" % (",".join(altered))
			
			if len(candidates) > 1:
				# check whether a specific term got tagged from the many, despite that they are different branches in the ontology
				# assumption: specific term has more words (see OMIM:614751)
				word_count = {}
				most_words = 0
				entity_with_most_words = ""
				for candidate in candidates:
					word_count[candidate.entity] = len(candidate.term.split(" "))
					if word_count[candidate.entity] > most_words:
						most_words = word_count[candidate.entity]
						entity_with_most_words = candidate.entity
				candidates = filter(lambda x: True if x.entity == entity_with_most_words else False, candidates)
				if self._debug:
					print "After keeping the specific term with the highest number of words"
					altered = []
					for c in candidates:
						altered.append(c.entity)
					print "%s" % (",".join(altered))
					
			if len(candidates) > 1 and ignore == False:
				raise Exception("There are more than entities to map at %s: %s" % (page, ";".join(map(str,candidates))))
			
			if len(tagged_entities) > 0 and len(candidates) == 0 and ignore == False:
				raise Exception("Something happened at %s, all of the possible mapping are gone! Original candidates were: %s" % (page, ";".join(map(str,tagged_entities))))
			
			if len(candidates) == 1:
				mapping[page] = MappingData(candidates[0].entity, 0, [candidates[0].term])		

		
		return mapping
