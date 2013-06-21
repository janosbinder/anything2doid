all: doid_entities.tsv doid_names.tsv doid_groups.tsv doid_names_expanded.tsv uniprot_corpus.tsv omim_corpus.tsv uniprot_doid_mapping.tsv omim_doid_mapping.tsv string_doid_mapping.tsv

%_entities.tsv %_names.tsv %_groups.tsv: %.obo
	./obo2reflect.pl $*
	
%_names_expanded.tsv: %_entities.tsv %_names.tsv
	./orthoexpand.pl $^ > $@
	
uniprot_corpus.tsv uniprot_text_omim.tsv: uniprot_sprot.dat
	./uniprot2corpus.py
	
omim_corpus.tsv: omim.txt
	./omim2corpus.py
	
uniprot_doid_mapping_full.tsv uniprot_doid_mapping.tsv uniprot_doid_diversity_index.tsv uniprot_doid_mapping_diversity.tsv uniprot_doid_idf_title.tsv uniprot_doid_idf_text.tsv uniprot_scores_title.tsv uniprot_scores_text.tsv uniprot_matches_title.tsv uniprot_matches_text.tsv: uniprot_corpus.tsv doid_entities.tsv doid_names_expanded.tsv doid_groups.tsv filter.tsv
	./corpus2mapping.py -t 201 -d doid -m uniprot -f filter.tsv
	
omim_doid_mapping_full.tsv omim_doid_mapping.tsv omim_doid_diversity_index.tsv omim_doid_mapping_diversity.tsv omim_doid_idf_title.tsv omim_doid_idf_text.tsv omim_scores_title.tsv omim_scores_text.tsv omim_matches_title.tsv omim_matches_text.tsv: omim_corpus.tsv doid_entities.tsv doid_names_expanded.tsv doid_groups.tsv filter.tsv
	./corpus2mapping.py -t 120.3 -d doid -m omim -f filter.tsv

string_doid_mapping.tsv: uniprot_doid_mapping.tsv /home/purple1/dictionary/stitch_entities.tsv /home/purple1/dictionary/stitch_names.tsv
	./uniprot2STRING.py > $@

