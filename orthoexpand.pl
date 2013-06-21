#!/usr/bin/perl -w

use strict;

my $processes = 1;

die "Too few arguments" if scalar @ARGV < 2;
$processes = $ARGV[2] if scalar @ARGV >= 3;


# Master section.

my @pids = ();
my $process;
for ($process = 0; $process < $processes; $process++) {
	my $pid = fork;
	die "Could not fork" unless defined $pid;
	last unless $pid;
	push @pids, $pid;
}

if ($process == $processes) {
	foreach my $pid (@pids) {
		waitpid $pid, 0;
	}
	system "cat /tmp/orthoexpand_1_*.tsv /tmp/orthoexpand_2_*.tsv /tmp/orthoexpand_3_*.tsv /tmp/orthoexpand_4_*.tsv /tmp/orthoexpand_5_*.tsv | sort -u";
	system "rm -f /tmp/orthoexpand_1_*.tsv /tmp/orthoexpand_2_*.tsv /tmp/orthoexpand_3_*.tsv /tmp/orthoexpand_4_*.tsv /tmp/orthoexpand_5_*.tsv";
	exit 0;
}


# Slave section.

my %serial_type = ();
open TSV, "< $ARGV[0]";
while (<TSV>) {
	s/\r?\n//;
	my ($serial, $type, undef) = split /\t/;
	next unless $serial % $processes == $process;
	$serial_type{$serial} = $type;
}
close TSV;

open TMP1, "> /tmp/orthoexpand_1_".$process.".tsv";
open TMP2, "> /tmp/orthoexpand_2_".$process.".tsv";
open TMP3, "> /tmp/orthoexpand_3_".$process.".tsv";
open TMP4, "> /tmp/orthoexpand_4_".$process.".tsv";
open TMP5, "> /tmp/orthoexpand_5_".$process.".tsv";

sub tmpprint
{
	my $priority = $_[0];
	if ($priority == 1) {
		print TMP1 join("\t", @_[1 .. $#_]), "\n";
	}
	elsif ($priority == 2) {
		print TMP2 join("\t", @_[1 .. $#_]), "\n";
	}
	elsif ($priority == 3) {
		print TMP3 join("\t", @_[1 .. $#_]), "\n";
	}
	elsif ($priority == 4) {
		print TMP4 join("\t", @_[1 .. $#_]), "\n";
	}
	else {
		print TMP5 join("\t", @_[1 .. $#_]), "\n";
	}
}

sub pluralize_and_tmpprint
{
	my $priority = $_[0];
	my $serial = $_[1];
	my $term = $_[2];
	$term =~ s/^ +//;
	$term =~ s/ +$//;
	my @terms = ($term);
	
	if (length($term) >= 5 && $term =~ /^[a-z -']+$/i) {       
		# Add plural endings.
		$_ = $term;
		if (s/([bcdfghjklmnpqrstvwxz])o$/$1oes/ or s/([bcdfghjklmnpqrstvwxz])y$/$1ies/ or s/(ch|s|sh|x|z)$/$1es/ or s/(\w+)$/$1s/) {
			push @terms, $_;
		}
		   
		# Add plural ending for Latin words.
		$_ = $term;
		if (s/us$/i/) {
			push @terms, $_;
		}
	}
	
	# Swap term around "deficiency|disorder of "
	$_ = $term;
	if (s/^(deficiency|disorder) of (.*)$/$2 $1/i) {
		push @terms, $_;
	}
	
	for $term (@terms) {
		tmpprint($priority+1, $serial, $term);
	}
}

open TSV, "< $ARGV[1]";
while (<TSV>) {
	
	s/\r?\n//;
	my ($serial, $name, $priority) = split /\t/;
	next unless $serial % $processes == $process;
	next unless exists $serial_type{$serial};
	$priority = 5 unless defined $priority;
	my $type = $serial_type{$serial};

	tmpprint($priority, $serial, $name);

	# Orthographic expansion of protein names
	if ($type > 0) {
	
		# Handle Greek letters converted to Latin equivalents
		$_ = $name;
		if (s/(^|[ \/])alpha([ \/]|$)/$1a$2/g || s/(^|[ \/])beta([ \/]|$)/$1b$2/g || s/(^|[ \/])gamma([ \/]|$)/$1g$2/g || s/(^|[ \/])delta([ \/]|$)/$1d$2/g || s/(^|[ \/])epsilon([ \/]|$)/$1e$2/gi) {
			if (length >= 3) {
				tmpprint($priority+1, $serial, $_);
			}
		}
		
		if ($name =~ /^([A-Z]+[0-9]+[0-9A-Z]*)(-[A-Z])?$/i and length($1) <= 7) {
			# Handle "p" postfix for proteins
			$_ = $name."p";
			tmpprint($priority+1, $serial, $_);
			
			# Handle "D" prefix for Drosophila proteins
			if ($type == "7227") {
				$_ = "D".$name;
				tmpprint($priority+1, $serial, $_);
			}
			
			# Handle "h" prefix for human proteins
			if ($type == "9606") {
				$_ = "h".$name;
				tmpprint($priority+1, $serial, $_);
			}
			
			# Handle "m" prefix for mouse proteins
			if ($type == "10090") {
				$_ = "m".$name;
				tmpprint($priority+1, $serial, $_);
			}
		}
	}
  
	# Chemicals
	if ($type == -1) {
	
		# Expand charge notation positive ones.
		$_ = $name;
		if (s/([2-4])([+-])$/$2 x $1/ge) {
			tmpprint($priority+1, $serial, $_);
		}

		# Collapse charge notation.
		$_ = $name;
		if (s/([+-]{2,4})/length($1).substr($1, 0, 1)/ge) {
			tmpprint($priority+1, $serial, $_);
		}
	}
	
	# Organisms
	if ($type == -2 or $type == -3) {
		
		# Remove quotes and what follows quoted names.
		if ($name =~ s/^"([^"]+)".*/$1/) {
			tmpprint($priority, $serial, $name);
		}
		
		# Remove brackets from names.
		if ($name =~ s/[()\[\]\{\}]+//g) {
			tmpprint($priority, $serial, $name);
		}
		
		# Abbreviate Linnean names.
		$_ = $name;
		if (s/^([A-Z])[a-z]+ ([a-z]+( |$))/$1. $2/g) {
			tmpprint($priority+1, $serial, $_);
			s/\.//;
			tmpprint($priority+1, $serial, $_);
		}
		
		# Remove species part of Linnean names with strain information.
		$_ = $name;
		if (/^([A-Z][a-z]+) ([a-z]+ |sp\. )?(subsp\. [a-z]+ )?([Ss][Tt][Rr]([Aa][Ii][Nn]|\.) )?(.{2,})/) {
			if (defined $2 or defined $3 or defined $4) {
				tmpprint($priority+1, $serial, $1." ".$6);
				tmpprint($priority+1, $serial, $1." str. ".$6) unless defined $4 and lc($4) eq "str. ";
				tmpprint($priority+1, $serial, $1." strain ".$6) unless defined $2 and $2 eq "strain " or defined $4 and lc($4) eq "strain ";
			}
			if (defined $2 and $2 ne "strain " and (defined $3 or defined $4)) {
				tmpprint($priority+1, $serial, $1." ".$2." ".$6);
				tmpprint($priority+1, $serial, $1." ".$2." str. ".$6) unless defined $4 and lc($4) eq "str. ";
				tmpprint($priority+1, $serial, $1." ".$2." strain ".$6) unless defined $4 and lc($4) eq "strain ";
			}
		}
	}
	
	# GO, BTO, and ENVO.
	if ($type <= -21 && $type >= -25 || $type == -27) {
		
		# Remove pointless last words.
		if ($name =~ s/ (activity|biome|complex|habitat|zone)$//) {
			tmpprint($priority+1, $serial, $name);
		}
		
		# Handle "response to" names.
		if ($name =~ s/^response to (.+ (stimulus|stimuli))$/$1/ or $name =~ s/^response to (.+)$/$1 response/) {
			tmpprint($priority+1, $serial, $name);
		}
		
		# Handle signaling cascades/pathways.
		$_ = $name;
		if (s/ (signall?ing )?cascade$// or s/ signall?ing pathway$//) {
		tmpprint($priority+1, $serial, $_." signaling");
			tmpprint($priority+1, $serial, $_." signalling");
			tmpprint($priority+1, $serial, $_." pathway");
			if (s/ receptor//) {
				tmpprint($priority+1, $serial, $_." signaling");
				tmpprint($priority+1, $serial, $_." signalling");
				tmpprint($priority+1, $serial, $_." pathway");
			}
		}
		elsif (length($name) >= 5 && $name =~ /^[a-z -]+$/i) {

			# Add adjective endings.
			$_ = $name;
			if (s/a$/al/ or s/le$/lar/ or s/me$/mal/ or s/ne$/nous/ or s/ol$/olic/ or s/on$/al/ or s/um$/al/ or s/us$/ar/ or s/(a[bcdfghjklmnpqrstvwxz]+)$/$1ic/) {
				tmpprint($priority+1, $serial, $_);
			}
			
			# Add plural endings.
			$_ = $name;
			if (s/([bcdfghjklmnpqrstvwxz])o$/$1oes/ or s/([bcdfghjklmnpqrstvwxz])y$/$1ies/ or s/(ch|s|sh|x|z)$/$1es/ or $_ .= "s") {
				tmpprint($priority+1, $serial, $_);
			}
			
			# Add plural ending for Latin words.
			$_ = $name;
			if (s/us$/i/) {
				tmpprint($priority+1, $serial, $_);
			}
			
		}
		
	}
	
	# DOID disease ontology
	if ($type == -26) {
	
		# Remove genitive case - 's
		$_ = $name;
		if (s/'s / /g) {
			pluralize_and_tmpprint($priority, $serial, $_);
		}
		
		$_ = $name;
		if (s/'s /' /g) {
			pluralize_and_tmpprint($priority, $serial, $_);
		}
		
		# Strip punctuations, quotes and parenthesis.
		$_ = $name;
		if (s/[-_,."'\(\)\[\]]//g) {
			pluralize_and_tmpprint($priority, $serial, $_);
		}

		# Remove "NOS".
		$_ = $name;
		if (s/(^NOS | NOS$)//g) {
			pluralize_and_tmpprint($priority, $serial, $_);
		}
		
		# Remove the word after "deficiency", but the term should not begin with deficiency and skip every anemia deficiency
		if ($name !~ m/anemia/ && $name =~ m/^[\w ]+deficiency/) {
			$_ = $name;
			if (s/deficiency [\w\(\)\[\]]+$/deficiency/i) {
				pluralize_and_tmpprint($priority, $serial, $_);
			}
		}
		
		# Remove "(morphologic abnormality)".
		$_ = $name;
		if (s/ \(morphologic abnormality\)//g) {
			pluralize_and_tmpprint($priority, $serial, $_);
		}
		
		# Remove "(disease)".
		$_ = $name;
		if (s/ \(disorder\)//g) {
			pluralize_and_tmpprint($priority, $serial, $_);
		}
		
		# Remove "(finding)".
		$_ = $name;
		if (s/ \(finding\)//g) {
			pluralize_and_tmpprint($priority, $serial, $_);
		}
		
		# Remove "[Ambiguous]".
		$_ = $name;
		if (s/ \[Ambiguous\]//g) {
			pluralize_and_tmpprint($priority, $serial, $_);
		}
		
		# Remove "Congenital".
		$_ = $name;
		if (s/^congenital //i) {
			pluralize_and_tmpprint($priority, $serial, $_);
		}

		# Create the pure plural variant
		pluralize_and_tmpprint($priority+1, $serial, $name);
		
		# Permute disease, disorder, and syndrome.
		$_ = $name;
		if (s/ disease$//i) {
			pluralize_and_tmpprint($priority, $serial, $_." disorder");
			pluralize_and_tmpprint($priority, $serial, $_." syndrome");
		}
		elsif (s/ disorder$//i) {
			pluralize_and_tmpprint($priority, $serial, $_." disease");
			pluralize_and_tmpprint($priority, $serial, $_." syndrome");
		}
		elsif (s/ syndrome$//i) {
			pluralize_and_tmpprint($priority, $serial, $_." disease");
			pluralize_and_tmpprint($priority, $serial, $_." disorder");
		}
	}
}
close TSV;

close TMP1;
close TMP2;
close TMP3;
close TMP4;
close TMP5;

exit 0;
