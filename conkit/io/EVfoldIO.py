"""
Parser module specific to EVfold predictions
"""

__author__ = "Felix Simkovic"
__date__ = "12 Oct 2016"
__version__ = 0.1

from conkit.core import Contact
from conkit.core import ContactMap
from conkit.core import ContactFile
from conkit.io._ParserIO import _ContactFileParser

import os
import re

RE_SPLIT = re.compile(r'\s+')


class EVfoldParser(_ContactFileParser):
    """Class to parse a EVfold contact file
    """
    def __init__(self):
        super(EVfoldParser, self).__init__()

    def read(self, f_handle, f_id="evfold"):
        """Read a contact file

        Parameters
        ----------
        f_handle
           Open file handle [read permissions]
        f_id : str, optional
           Unique contact file identifier

        Returns
        -------
        :obj:`ContactFile`

        """

        hierarchy = ContactFile(f_id)
        contact_map = ContactMap("map_1")
        hierarchy.add(contact_map)

        for line in f_handle:
            line = line.rstrip()

            if not line:
                continue

            else:
                res1_seq, res1, res2_seq, res2, _, raw_score = RE_SPLIT.split(line)

                contact = Contact(
                    int(res1_seq),
                    int(res2_seq),
                    float(raw_score)
                )
                contact.res1 = res1
                contact.res2 = res2
                contact_map.add(contact)

        hierarchy.method = 'Contact map predicted using EVfold'

        return hierarchy

    def write(self, f_handle, hierarchy):
        """Write a contact file instance to to file

        Parameters
        ----------
        f_handle
           Open file handle [write permissions]
        hierarchy : :obj:`ContactFile`, `:obj:`ContactMap` or :obj:`Contact`

        Raises
        ------
        RuntimeError
           More than one contact map in the hierarchy

        """
        # Double check the type of hierarchy and reconstruct if necessary
        contact_file = self._reconstruct(hierarchy)

        if len(contact_file) > 1:
            raise RuntimeError('More than one contact map provided')

        for contact_map in contact_file:
            for contact in contact_map:
                line = "{res1_seq} {res1} {res2_seq} {res2} 0 {raw_score}"
                line = line.format(res1_seq=contact.res1_seq, res2_seq=contact.res2_seq,
                                   res1=contact.res1, res2=contact.res2, raw_score=contact.raw_score)
                f_handle.write(line + os.linesep)

        return