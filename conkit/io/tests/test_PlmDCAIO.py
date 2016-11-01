"""Testing facility for conkit.io.PlmDCAIO"""

__author__ = "Felix Simkovic"
__date__ = "26 Oct 2016"

from conkit.core import Contact
from conkit.core import ContactFile
from conkit.core import ContactMap
from conkit.core import Sequence
from conkit.io.PlmDCAIO import PlmDCAParser

import os
import unittest
import tempfile


def _create_tmp(data=None):
    f_in = tempfile.NamedTemporaryFile(delete=False)
    if data:
        f_in.write(data)
    f_in.close()
    return f_in.name


class Test(unittest.TestCase):

    def test_read(self):
        # ==================================================
        # Test Case 1
        content = """1,2,0.12212
1,3,0.14004
1,4,0.12926
1,5,0.089211
1,6,0.079976
1,7,0.078954
1,8,0.052275
1,9,0.026012
1,10,0.049844
1,11,0.045109
"""
        f_name = _create_tmp(content)
        contact_file = PlmDCAParser().read(open(f_name, 'r'))
        contact_map1 = contact_file.top_map
        self.assertEqual(1, len(contact_file))
        self.assertEqual(10, len(contact_map1))
        self.assertEqual([1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [c.res1_seq for c in contact_map1])
        self.assertEqual([2, 3, 4, 5, 6, 7, 8, 9, 10, 11], [c.res2_seq for c in contact_map1])
        self.assertItemsEqual(
            [0.12212, 0.14004, 0.12926, 0.089211, 0.079976, 0.078954, 0.052275, 0.026012, 0.049844, 0.045109],
            [c.raw_score for c in contact_map1]
        )
        os.unlink(f_name)

    def test_write(self):
        # ======================================================
        # Test Case 1
        contact_file = ContactFile('RR')
        contact_file.target = 'R9999'
        contact_file.author = '1234-5678-9000'
        contact_file.remark = ['Predictor remarks']
        contact_file.method = ['Description of methods used', 'Description of methods used']
        contact_map = ContactMap('1')
        contact_file.add(contact_map)
        for c in [(1, 9, 0, 8, 0.7), (1, 10, 0, 8, 0.7), (2, 8, 0, 8, 0.9), (3, 12, 0, 8, 0.4)]:
            contact = Contact(c[0], c[1], c[4], distance_bound=(c[2], c[3]))
            contact_map.add(contact)
        contact_map.sequence = Sequence('1', 'HLEGSIGILLKKHEIVFDGCHDFGRTYIWQMSD')
        contact_map.assign_sequence_register()
        f_name = _create_tmp()
        PlmDCAParser().write(open(f_name, 'w'), contact_file)
        content = """1,9,0.700000
1,10,0.700000
2,8,0.900000
3,12,0.400000
"""
        data = "".join(open(f_name, 'r').readlines())
        self.assertEqual(content, data)
        os.unlink(f_name)


if __name__ == "__main__":
    unittest.main(verbosity=2)