"""Versioned graph-check projection; no model calls or semantic inference."""
from copy import deepcopy

from .datasets import resolve_bindings
from .util import digest

PROFILE = 'graph-check-projection-1'
SOURCE_CATEGORIES = {'obligation': 'reference_obligation', 'edge': 'graph_relation',
                     'constraint': 'graph_constraint'}
OPTIONS = ['pass', 'fail', 'uncertain']
OPTION_DESC = {'pass': 'The visible evidence satisfies the stated requirement.',
               'fail': 'The visible evidence contradicts the stated requirement.',
               'uncertain': 'The visible evidence is insufficient or ambiguous.'}


def compile_checks(case_id, checks, graph, reviewed=None):
    """Apply explicit graph evidence or separately approved missing-binding decisions.

    Review records are data artifacts, not trusted authorization from the model.
    The migration pipeline must authenticate their raw author/reviewer receipts.
    This projection validates source identity and refuses unrequested overrides.
    """
    reviewed = reviewed or {}
    rows, seen, consumed = [], set(), set()
    for check in checks:
        key = check['id']
        if not isinstance(key, str) or not key or key in seen:
            raise ValueError('Duplicate or empty graph check ID')
        seen.add(key)
        question = check['requirement']
        if not isinstance(question, str) or not question.strip():
            raise ValueError('Missing graph requirement')
        kind, separator, source_id = check['source'].partition(':')
        if kind not in SOURCE_CATEGORIES or not separator or not source_id:
            raise ValueError('Unsupported graph check source')
        reason = check.get('candidate_only_reason', '')
        try:
            refs = resolve_bindings(check, graph)
        except ValueError as exc:
            if str(exc) != 'No explicit image evidence: review this binding before release':
                raise
            decision = reviewed.get(key)
            if (not decision or decision.get('approved') is not True
                    or decision.get('graph_digest') != digest(graph)
                    or decision.get('check_digest') != digest(check)):
                raise ValueError('Missing or stale approved binding review') from exc
            status = decision.get('status')
            refs = decision.get('reference_ids')
            if not isinstance(refs, list) or len(refs) != len(set(refs)):
                raise ValueError('Invalid reviewed reference IDs')
            order = [r['reference_id'] for r in graph['references']]
            if refs != [r for r in order if r in refs]:
                raise ValueError('Unknown or unordered reviewed references')
            reason = decision.get('candidate_only_reason', '')
            if status == 'candidate_only':
                if refs or not isinstance(reason, str) or not reason.strip():
                    raise ValueError('Invalid candidate-only review')
            elif status != 'bound' or not refs or reason:
                raise ValueError('Invalid bound review')
            consumed.add(key)
        else:
            if key in reviewed:
                raise ValueError('Review cannot override explicit source bindings')
        row = {'case_id': case_id, 'check_id': key, 'category': SOURCE_CATEGORIES[kind],
               'question': question, 'guide': check.get('guide', ''),
               'options': deepcopy(check.get('options', OPTIONS)),
               'option_desc': deepcopy(check.get('option_desc', OPTION_DESC)),
               'reference_ids': refs, 'source': check['source'], 'compiler_profile': PROFILE}
        if row['category'] == 'global_check':
            raise ValueError('Graph projection must not select the legacy global branch')
        if row['options'] != OPTIONS or row['option_desc'] != OPTION_DESC:
            raise ValueError('Graph projection requires its versioned pass/fail/uncertain vocabulary')
        if not refs:
            row['candidate_only_reason'] = reason
        rows.append(row)
    if set(reviewed) != consumed:
        raise ValueError('Unconsumed binding review')
    return rows
