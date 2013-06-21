#!/usr/bin/env python

import os
import re
import sys
import math

class Backtrack:
	def __init__(self, dictionary, filterfile):
		self._entry_filter = {}
		if not os.path.isfile(filterfile):
			for line in open(filterfile):
				f = line[:-1].split("\t")
				self._entry_filter[f[0]] = f[1]
		serial_entity = {}
		for line in open("%s_entities.tsv" % dictionary):
			serial, t, entry = line[:-1].split("\t")
			serial_entity[serial] = entry
		self._child_parent = {}
		self._parent_child = {}
		for line in open("%s_groups.tsv" % dictionary):
			f = line[:-1].split("\t")
			child, parent = serial_entity[f[0]], serial_entity[f[1]]
			if child not in self._child_parent:
				self._child_parent[child] = set()
			self._child_parent[child].add(parent)
			if parent not in self._child_parent:
				self._child_parent[parent] = set()
			if parent in self._entry_filter and self._entry_filter[parent] == "*" and child not in self._entry_filter:
				self._entry_filter[child] = "1"
			if parent not in self._parent_child:
				self._parent_child[parent] = set()
			self._parent_child[parent].add(child)
			if child not in self._parent_child:
				self._parent_child[child] = set()
				
	def getparents(self, entry):
		return self._child_parent[entry]
	def getparents_and_entry(self, entry):
		return self._child_parent[entry].union([entry])
	def getchildren(self, entry):
		return self._parent_child[entry]
	def is_filtered(self, entry):
		return True if entry in self._entry_filter else False