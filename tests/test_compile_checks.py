import copy
import unittest

from longbanana.compile_checks import compile_checks
from longbanana.util import digest
from openclaw_longbanana.judge.answer_parser import parse_agent_answer


class CompilerTests(unittest.TestCase):
    def setUp(self):
        self.graph = {'references': [{'reference_id': 'R01'}],
                      'nodes': [{'id': 'N1'}], 'constraints': [{'id': 'C1'}], 'evidence_edges': []}
        self.check = {'id': 'Q1', 'source': 'constraint:C1', 'members': ['N1'],
                      'requirement': 'The canvas is square.'}
        self.review = {'approved': True, 'graph_digest': digest(self.graph),
                       'check_digest': digest(self.check), 'status': 'candidate_only',
                       'reference_ids': [], 'candidate_only_reason': 'Canvas geometry is self-contained.'}

    def test_verbatim_and_no_global_branch_change(self):
        result = compile_checks('LAC-001', [self.check], self.graph, {'Q1': self.review})[0]
        self.assertEqual(result['question'], self.check['requirement'])
        self.assertEqual(result['category'], 'graph_constraint')
        self.assertEqual(result['guide'], '')
        self.assertEqual(result['reference_ids'], [])

    def test_unreviewed_and_stale_rejected(self):
        with self.assertRaises(ValueError):
            compile_checks('LAC-001', [self.check], self.graph)
        self.review['check_digest'] = 'stale'
        with self.assertRaises(ValueError):
            compile_checks('LAC-001', [self.check], self.graph, {'Q1': self.review})

    def test_explicit_bindings_cannot_be_overridden(self):
        self.graph['evidence_edges'] = [{'src': 'R01', 'dst': 'C1'}]
        self.assertEqual(compile_checks('LAC-001', [self.check], self.graph)[0]['reference_ids'], ['R01'])
        with self.assertRaises(ValueError):
            compile_checks('LAC-001', [self.check], self.graph, {'Q1': self.review})

    def test_unknown_and_duplicate_reviewed_refs_rejected(self):
        for ids in [['R99'], ['R01', 'R01']]:
            review = {**self.review, 'status': 'bound', 'reference_ids': ids, 'candidate_only_reason': ''}
            with self.assertRaises(ValueError):
                compile_checks('LAC-001', [self.check], self.graph, {'Q1': review})

    def test_structural_error_cannot_be_approved(self):
        bad = copy.deepcopy(self.check)
        bad['members'] = ['N99']
        review = {**self.review, 'check_digest': digest(bad)}
        with self.assertRaisesRegex(ValueError, 'members'):
            compile_checks('LAC-001', [bad], self.graph, {'Q1': review})

    def test_unused_review_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unconsumed'):
            compile_checks('LAC-001', [self.check], self.graph, {'Q1': self.review, 'Q2': self.review})

    def test_projection_options_are_supported_by_existing_parser(self):
        for answer, passed, uncertain in [('pass', True, False), ('fail', False, False), ('uncertain', False, True)]:
            result = parse_agent_answer('<answer>{"answer":"' + answer + '","reason":"fixture"}</answer>',
                                        ['pass', 'fail', 'uncertain'])
            self.assertFalse(result.is_invalid)
            self.assertEqual(result.is_pass, passed)
            self.assertEqual(result.is_uncertain, uncertain)


if __name__ == '__main__':
    unittest.main()
