#!/usr/bin/env python

__author__ = "Felix Simkovic"
__date__ = "08 Feb 2017"
__version__ = 0.1

import argparse
import conkit
import logging
import sys

logging.basicConfig(format='%(message)s', level=logging.INFO)


def add_default_args(parser):
    """Define default arguments"""
    parser.add_argument('-dpi', dest='dpi', default=300, type=int,
                        help="the resolution in DPI [default: 300]")
    parser.add_argument('-o', dest='output', default=None, type=str,
                        help="the figure file. Note, the format is determined by the suffix")


def add_contact_map_args(subparsers):
    description = u"""
This command will plot a contact map using the provided contacts
alongside any additional information.

If you provide a reference structure, the true positive contacts
are identified by a distance of <8\u212B between C\u03B2-C\u03B2 atoms.

!!! IMPORTANT
=============
If contacts cannot be matched between your prediction and the
reference structure, they will not be plotted.

"""
    contact_map_subparser = subparsers.add_parser('cmap', help="Plot a contact map", description=description,
                                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    add_default_args(contact_map_subparser)
    contact_map_subparser.add_argument('-c', dest='pdbchain', default=None,
                                       help='PDB chain to use [default: first in file]. Inter-molecular predictions '
                                            'use two letter convention, i.e AD for contacts between A and D.')
    contact_map_subparser.add_argument('-d', dest='dtn', default=5, type=int,
                                       help='Minimum sequence separation [default: 5]')
    contact_map_subparser.add_argument('-e', dest='otherfile', default=None,
                                       help='a second contact map to plot for comparison')
    contact_map_subparser.add_argument('-ef', dest='otherformat', default=None,
                                       help='the format of the second contact map')
    contact_map_subparser.add_argument('-f', dest='dfactor', default=1.0, type=float,
                                       help='number of contacts to include relative to sequence length [default: 1.0]')
    contact_map_subparser.add_argument('-p', dest='pdbfile', default=None, type=str,
                                       help="A reference PDB file")
    contact_map_subparser.add_argument('-pf', dest='pdbformat', default='pdb', type=str,
                                       help="A reference PDB file")
    contact_map_subparser.add_argument('--confidence', action="store_true", default=False,
                                       help='Plot the confidence scores')
    contact_map_subparser.add_argument('--interchain', action="store_true", default=False,
                                       help='Plot inter-chain contacts')
    contact_map_subparser.add_argument('seqfile',
                                       help="Path to the sequence file")
    contact_map_subparser.add_argument('seqformat',
                                       help="Format of the sequence file")
    contact_map_subparser.add_argument('confile',
                                       help="Path to the contact file")
    contact_map_subparser.add_argument('conformat',
                                       help="Format of the contact file")
    contact_map_subparser.set_defaults(which='contact_map')


def add_sequence_coverage_args(subparsers):
    description = u"""
This command will plot a coverage plot for every position in your alignment.

"""
    sequence_coverage_subparser = subparsers.add_parser('scov', help="Plot the sequence coverage",
                                                        description=description,
                                                        formatter_class=argparse.RawDescriptionHelpFormatter)
    add_default_args(sequence_coverage_subparser)
    sequence_coverage_subparser.add_argument('-id', dest='identity', default=0.7, type=float,
                                             help='sequence identity [default: 0.7]')
    sequence_coverage_subparser.add_argument('msafile',
                                             help='Multiple Sequence Alignment file')
    sequence_coverage_subparser.add_argument('msaformat',
                                             help='Multiple Sequence Alignment format')
    sequence_coverage_subparser.set_defaults(which='sequence_coverage')


def main():

    description = u"""
This script provides a command-line interface to ConKit's plotting functionality.
You are provided with a single access point to many different kinds of plots.

"""
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers()
    # Add the subparsers
    add_contact_map_args(subparsers)
    add_sequence_coverage_args(subparsers)
    # Parse all arguments
    args = parser.parse_args()

    if args.which == 'contact_map':
        if args.interchain:
            logging.info('This script is experimental for inter-chain contact plotting')

        logging.info('Distance to neighbors: {0}'.format(args.dtn))
        logging.info('Contact list cutoff factor: {0}'.format(args.dfactor))

        seq = conkit.io.read(args.seqfile, args.seqformat)[0]
        con = conkit.io.read(args.confile, args.conformat)[0]

        con.sequence = seq
        con.assign_sequence_register()
        con.remove_neighbors(min_distance=args.dtn, inplace=True)
        ncontacts = int(seq.seq_len * args.dfactor)
        con.sort('raw_score', reverse=True, inplace=True)
        con_sliced = con[:ncontacts]

        if args.otherfile:
            other = conkit.io.read(args.otherfile, args.otherformat)[0]
            other.sequence = seq
            other.assign_sequence_register()
            other.remove_neighbors(min_distance=args.dtn, inplace=True)
            other.sort('raw_score', reverse=True, inplace=True)
            other_sliced = other[:ncontacts]
        else:
            other_sliced = None

        if args.pdbfile:
            if args.pdbchain:
                pdb = conkit.io.read(args.pdbfile, 'pdb')[args.pdbchain]
            elif args.pdbfile:
                pdb = conkit.io.read(args.pdbfile, 'pdb')[0]
            reference = pdb
            con_matched = con_sliced.match(pdb, renumber=True, remove_unmatched=True)
            if other_sliced:
                other_matched = other_sliced.match(pdb, renumber=True, remove_unmatched=True)
            else:
                other_matched = other_sliced
        else:
            reference = None
            con_matched = con_sliced
            other_matched = other_sliced

        def altloc_remove(map):
            altloc = False
            for contact in map.copy():
                if contact.res1_chain != contact.res2_chain:
                    altloc = True
                    break
                if contact.res1_chain == contact.res2_chain and args.interchain:
                    map.remove(contact.id)
                elif contact.res1_chain != contact.res2_chain and not args.interchain:
                    map.remove(contact.id)
            return altloc

        altloc = altloc_remove(con_matched)
        if other_matched:
            altloc = altloc_remove(other_matched)

        outformat = 'png'
        outfile = args.output if args.output else args.confile.rsplit('.', 1)[0] + '.' + outformat
        conkit.plot.ContactMapFigure(con_matched, other=other_matched, reference=reference,
                                     file_name=outfile, altloc=altloc, use_conf=args.confidence,
                                     dpi=args.dpi)

    elif args.which == 'sequence_coverage':
        hierarchy = conkit.io.read(args.msafile, args.msaformat)
        outformat = 'png'
        outfile = args.output if args.output else args.msafile.rsplit('.', 1)[0] + '.' + outformat
        conkit.plot.SequenceCoverageFigure(hierarchy, file_name=outfile, dpi=args.dpi)

    logging.info('Final plot written in {0} format to: {1}'.format(outformat.upper(), outfile))
    return 0


if __name__ == "__main__":
    sys.exit(main())