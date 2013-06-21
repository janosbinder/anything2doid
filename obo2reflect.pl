#!/usr/bin/perl -w

use strict;

my $input = $ARGV[0];
my $output = (scalar @ARGV > 1 ? $ARGV[1] : $ARGV[0]);

my $extralinksfile = $input."_extra_links.tsv";
my $extranamesfile = $input."_extra_names.tsv";
my $extratextsfile = $input."_extra_texts.tsv";
my $filterfile = $input."_filters.tsv";
my $obofile = $input.".obo";

open ENTITIES, "| sort -u > ".$output."_entities.tsv";
open NAMES,    "| sort -u > ".$output."_names.tsv";
open GROUPS,   "| sort -u > ".$output."_groups.tsv";
open TEXTS,    "| sort -u > ".$output."_texts.tsv";


my %id_filter = ();
my %id_name_filter = ();
if (-e $filterfile) {
    open FILTER, "< $filterfile";
    while (<FILTER>) {
        s/\r?\n//;
        my ($id, $name) = split /\t/;
        if ($name) {
            $id_name_filter{$id}{$name} = 1;
        }
        else {
            $id_filter{$id} = 1;
        }
    }
    close FILTER;
}

my $base_type = -20;

my %input_type = (
    "go" => -24,
    "bto" => -25,
    "doid" => -26,
    "envo" => -27,
    "apo" => -29,
    "nbo" => -30
);

my %namespace_type = (
    "biological_process" => -21,
    "cellular_component" => -22,
    "molecular_function" => -23,
    "observable" => -28
);

my $serial = 1000000000-1000000*(exists $input_type{$input} ? $input_type{$input}-$base_type : 0);

my %id_serial = ();
my %parent_child = ();
my @roots;
if (-e $extralinksfile) {
    open TSV, "< $extralinksfile";
    while (<TSV>) {
        s/\r?\n//;
        my ($child, $parent) = split /\t/;
        $parent_child{$parent}{$child} = 1;
    }
    close TSV;
}

my %id_text = ();
if (-e $extratextsfile) {
    open TSV, "< $extratextsfile";
    while (<TSV>) {
        s/\r?\n//;
        my ($id, $text) = split /\t/;
        $id_text{$id} = $text;
    }
    close TSV;
}

my %id_obsolete = ();
open OBO, "< $obofile";
while (<OBO>) {
    s/[ \t\r]*\n//;
    next unless /^\[Term]/;
    my $id = "";
    while (<OBO>) {
        s/[ \t\r]*\n//;
        last if /^$/;
        if (/^id: +([^ ]+)/) {
            $id = $1;
        }
        elsif (/^is_obsolete: +true/) {
            $id_obsolete{$id} = 1;
        }
    }
}
close OBO;

my %id_type = ();
open OBO, "< $obofile";
while (<OBO>) {
    s/[ \t\r]*\n//;
    next unless /^\[Term]/;
    my $id = "";
    my $namespace = "";
    my %name_priority = ();
    my @parents = ();
    my %subsets = ();
    my $text = "";
    my $root = 1;
    $serial++;
    while (<OBO>) {
        s/[ \t\r]*\n//;
        last if /^$/;
        if (/^id: +([^ ]+)/) {
            $id = $1;
            $id_serial{$1} = $serial;
            $name_priority{$id} = 2;
            last if exists $id_obsolete{$id};
        }
        elsif (/^alt_id: +(.+)/) {
            $id_serial{$1} = $serial;
        }
        elsif ((not (/" BROAD/ or /" NARROW/)) and (/^(name): +(.+)/ or /^(synonym): "(.+)"/)) {
            my $field = $1;
            my $name = $2;
            $name =~ s/\t/ /g;
            if (not exists $id_filter{$id} and not (exists $id_name_filter{$id} and exists $id_name_filter{$id}{$name}) and length($name) >= 5 and not $name =~ / antibody$/) {
                my $priority = 1;
                $priority = 3 if $field ne "name";
                $name_priority{$name} = $priority unless exists $name_priority{$name};
                if ($name =~ /^(.+), (.+)$/) {
                    my $name2 = $2." ".$1;
                    $name_priority{$name2} = $priority+1 unless exists $name_priority{$name2};
                }
            }
        }
        elsif (/^namespace: +([^ ]+)/) {
            $namespace = $1;
        }
        elsif (/^def: +"?(.+?)"?( +\[.*\])?$/) {
            $text = $1;
        }
        elsif (/^subset: +([^ ]+)$/) {
            $subsets{$1} = 1;
        }
        elsif (/^is_a: +([^ ]+)/ or /^relationship: +part_of +([^ ]+)/) {
            push @parents, $1;
            $root = 0;
        }
    }
    if ($id) {
        my $type = $base_type;
        $type = $input_type{$input} if exists $input_type{$input};
        $type = $namespace_type{$namespace} if defined $namespace and exists $namespace_type{$namespace};
	next if $input eq "apo" and not exists $subsets{"SGD"};
        next if $output eq "gobp" and $type != $namespace_type{"biological_process"};
        next if $output eq "gocc" and $type != $namespace_type{"cellular_component"};
        next if $output eq "gomf" and $type != $namespace_type{"molecular_function"};
        print ENTITIES $serial, "\t", $type, "\t", $id, "\n" unless exists $id_filter{$id};
        $id_type{$id} = $type;
        foreach my $name (keys %name_priority) {
            print NAMES $serial, "\t", $name, "\t", $name_priority{$name}, "\n";
        }
        foreach my $parent (@parents) {
            $parent_child{$parent}{$id} = 1;
        }
        $text = $id_text{$id} if exists $id_text{$id};
        print TEXTS $serial, "\t", $text, "\n" unless $text eq "";
    }
    push @roots, $id if $root;
}
close OBO;

my @parents;
sub print_children {
    my $current = $_[0];
    foreach my $parent (@parents) {
        print GROUPS $id_serial{$current}, "\t", $id_serial{$parent}, "\n" if exists $id_serial{$current} and not exists $id_filter{$current} and not exists $id_filter{$parent};
    }
    push @parents, $current;
    foreach my $child (keys %{$parent_child{$current}}) {
        print_children($child);
    }
    pop @parents;
}

foreach my $root (@roots) {
    print_children($root);
}

if (-e $extranamesfile) {
    open TSV, "< $extranamesfile";
    while (<TSV>) {
        s/\r?\n//;
        my ($id, $name) = split /\t/;
        if (not exists $id_serial{$id}) {
            $serial++;
            $id_serial{$id} = $serial;
            my $type = $base_type;
            $type = $input_type{$input} if exists $input_type{$input};
            $type = $id_type{$id} if exists $id_type{$id};
            print ENTITIES $serial, "\t", $type, "\t", $id, "\n" unless exists $id_filter{$id};
        }
        print NAMES $id_serial{$id}, "\t", $name, "\t5\n" unless exists $id_name_filter{$id} and exists $id_name_filter{$id}{$name};
    }
    close TSV;
}

close ENTITIES;
close NAMES;
close GROUPS;
close TEXTS;
