import os
import re
import sys
import math
import backtrack
import omimmapper

class Benchmark:
	
	def __init__(self, backtracker, benchmark_filename):
		self._backtrack = backtracker
		self._expected = {}
		self._negatives = {}
		for line in open(benchmark_filename):
			if "#" in line[:-1]:
				continue
			f = line[:-1].strip().split("\t")
			document = f[0]
			entity = f[1]
			negative = None
			if len(f) == 3:
				negative = f[2]
			if document in self._expected:
				raise Exception, "Multiple mappings defined for document %s in benchmark file %s." % (document, benchmark_filename)
			if negative != None and negative == "F":
				self._negatives[document] = entity
			self._expected[document] = entity
		
	def get_performance(self, mapping):
		tp = 0
		fp = 0
		fn = 0
		WRONG = open("%s_wrong_mappings.tsv" % "omim", "w")
		WRONG.write("# Page\tWrong mapped ID\tID\tRelatives?\n")
		GOOD = open("%s_good_mappings.tsv" % "omim", "w")
		GOOD.write("# Page\tID\n")
		for document in self._expected:
			if document in mapping:
				if document in self._negatives:
					WRONG.write("%s\t%s\t\tKNOWN_NEGATIVE\n" % (document, mapping[document].entity))
				else:
					if mapping[document].entity == self._expected[document]:
					#if mapping[document].entity == random.choice(self._expected.values()):
						tp += 1
						GOOD.write("%s\t%s\n" % (document, mapping[document].entity))
					else:
						fp += 1
						is_relatives = False
						if self._backtrack.is_child(mapping[document].entity, self._expected[document]) or self._backtrack.is_child(self._expected[document], mapping[document].entity):
							is_relatives = True
						if is_relatives:
							WRONG.write("%s\t%s\t%s\tRELATIVES\n" % (document, mapping[document].entity, self._expected[document]))	
						else:
							WRONG.write("%s\t%s\t%s\t\n" % (document, mapping[document].entity, self._expected[document]))	
			else:
				fn += 1
				WRONG.write("%s\t%s\t\tNO_MAPPING_EXISTS\n" % (document, self._expected[document]))
		WRONG.close()
		GOOD.close()
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