all: doid_entities.tsv doid_names.tsv doid_groups.tsv doid_names_expanded.tsv omim_doid_mapping.tsv

clean:
	rm doid_entities.tsv doid_names.tsv doid_groups.tsv doid_names_expanded.tsv omim_doid_mapping.tsv

%_entities.tsv %_names.tsv %_groups.tsv: %.obo
	./obo2reflect.pl $*
	
%_names_expanded.tsv: %_entities.tsv %_names.tsv
	./orthoexpand.pl $^ > $@

omim_doid_mapping.tsv: omim.txt omim2mapping.py
	./omim2mapping.py > $@	

string_doid_mapping.tsv: uniprot_sprot.dat
	./uniprot2mapping.py > $@

