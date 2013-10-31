#!/usr/bin/perl -w

use strict;

open OBO, "< $ARGV[0]";
while(<OBO>) {
    s/[ \t\r]*\n//;
    next unless /^\[Term]/;
    my $id = "";
    my $name = "";
    my $confirmed = 0;
    while (<OBO>) {
        s/[ \t\r]*\n//;
        last if /^$/;
        if (/^id: +([^ ]+)/) {
            $id = $1;
        }
        elsif (/^name: +(.+)/) {
            $name = $1;
        }
        elsif (/^comment: OMIM mapping confirmed.*/) {
            $confirmed = 1;
        }
        elsif (/^xref: +OMIM:(\d+)/) {
            print "OMIM:", $1, "\t", $id, "\t", $name, "\n" if $confirmed;
            # print STDERR "IGNORED:", $id, "\t", $name, "\tOMIM:", $1, "\n" unless $confirmed;
        }
    }    
}
close OBO;
