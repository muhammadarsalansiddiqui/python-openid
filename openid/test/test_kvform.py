import unittest

from openid import kvform
from openid.test.support import CatchLogs


class KVBaseTest(unittest.TestCase, CatchLogs):

    def checkWarnings(self, num_warnings, msg=None):
        full_msg = 'Invalid number of warnings {} != {}'.format(num_warnings, len(self.messages))
        if msg is not None:
            full_msg = full_msg + ' ' + msg
        self.failUnlessEqual(num_warnings, len(self.messages), full_msg)

    def setUp(self):
        CatchLogs.setUp(self)

    def tearDown(self):
        CatchLogs.tearDown(self)


class KVDictTest(KVBaseTest):

    def runTest(self):
        for kv_data, result, expected_warnings in kvdict_cases:
            # Clean captrured messages
            del self.messages[:]

            # Convert KVForm to dict
            d = kvform.kvToDict(kv_data)

            # make sure it parses to expected dict
            self.failUnlessEqual(d, result)

            # Check to make sure we got the expected number of warnings
            self.checkWarnings(expected_warnings, msg='kvToDict({!r})'.format(kv_data))

            # Convert back to KVForm and round-trip back to dict to make
            # sure that *** dict -> kv -> dict is identity. ***
            kv = kvform.dictToKV(d)
            d2 = kvform.kvToDict(kv)
            self.failUnlessEqual(d, d2)


class KVSeqTest(KVBaseTest):

    def cleanSeq(self, seq):
        """Create a new sequence by stripping whitespace from start
        and end of each value of each pair"""
        clean = []
        for k, v in seq:
            if isinstance(k, str):
                k = k.decode('utf8')
            if isinstance(v, str):
                v = v.decode('utf8')
            clean.append((k.strip(), v.strip()))
        return clean

    def runTest(self):
        for kv_data, result, expected_warnings in kvseq_cases:
            # Clean captrured messages
            del self.messages[:]

            # seq serializes to expected kvform
            actual = kvform.seqToKV(kv_data)
            self.failUnlessEqual(actual, result)
            self.assertIsInstance(actual, str)

            # Parse back to sequence. Expected to be unchanged, except
            # stripping whitespace from start and end of values
            # (i. e. ordering, case, and internal whitespace is preserved)
            seq = kvform.kvToSeq(actual)
            clean_seq = self.cleanSeq(seq)

            self.failUnlessEqual(seq, clean_seq)
            self.checkWarnings(expected_warnings)


kvdict_cases = [
    # (kvform, parsed dictionary, expected warnings)
    ('', {}, 0),
    ('college:harvey mudd\n', {'college': 'harvey mudd'}, 0),
    ('city:claremont\nstate:CA\n', {'city': 'claremont', 'state': 'CA'}, 0),
    ('is_valid:true\ninvalidate_handle:{HMAC-SHA1:2398410938412093}\n',
     {'is_valid': 'true', 'invalidate_handle': '{HMAC-SHA1:2398410938412093}'}, 0),

    # Warnings from lines with no colon:
    ('x\n', {}, 1),
    ('x\nx\n', {}, 2),
    ('East is least\n', {}, 1),

    # But not from blank lines (because LJ generates them)
    ('x\n\n', {}, 1),

    # Warning from empty key
    (':\n', {'': ''}, 1),
    (':missing key\n', {'': 'missing key'}, 1),

    # Warnings from leading or trailing whitespace in key or value
    (' street:foothill blvd\n', {'street': 'foothill blvd'}, 1),
    ('major: computer science\n', {'major': 'computer science'}, 1),
    (' dorm : east \n', {'dorm': 'east'}, 2),

    # Warnings from missing trailing newline
    ('e^(i*pi)+1:0', {'e^(i*pi)+1': '0'}, 1),
    ('east:west\nnorth:south', {'east': 'west', 'north': 'south'}, 1),
]

kvseq_cases = [
    ([], '', 0),

    # Make sure that we handle non-ascii characters (also wider than 8 bits)
    ([(u'\u03bbx', u'x')], '\xce\xbbx:x\n', 0),

    # If it's a UTF-8 str, make sure that it's equivalent to the same
    # string, decoded.
    ([('\xce\xbbx', 'x')], '\xce\xbbx:x\n', 0),

    ([('openid', 'useful'), ('a', 'b')], 'openid:useful\na:b\n', 0),

    # Warnings about leading whitespace
    ([(' openid', 'useful'), ('a', 'b')], ' openid:useful\na:b\n', 2),

    # Warnings about leading and trailing whitespace
    ([(' openid ', ' useful '),
      (' a ', ' b ')], ' openid : useful \n a : b \n', 8),

    # warnings about leading and trailing whitespace, but not about
    # internal whitespace.
    ([(' open id ', ' use ful '),
      (' a ', ' b ')], ' open id : use ful \n a : b \n', 8),

    ([(u'foo', 'bar')], 'foo:bar\n', 0),
]

kvexc_cases = [
    [('openid', 'use\nful')],
    [('open\nid', 'useful')],
    [('open\nid', 'use\nful')],
    [('open:id', 'useful')],
    [('foo', 'bar'), ('ba\n d', 'seed')],
    [('foo', 'bar'), ('bad:', 'seed')],
]


class KVExcTest(unittest.TestCase):

    def runTest(self):
        for kv_data in kvexc_cases:
            self.failUnlessRaises(ValueError, kvform.seqToKV, kv_data)


class GeneralTest(KVBaseTest):
    kvform = '<None>'

    def test_convert(self):
        result = kvform.seqToKV([(1, 1)])
        self.failUnlessEqual(result, '1:1\n')
        self.checkWarnings(2)