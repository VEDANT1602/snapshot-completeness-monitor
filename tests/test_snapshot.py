import sys
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from core import Monitor,assemble
from generate import page,generate
from support import verify_manifest

class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.path=Path(self.t.name)/'state.db';self.m=Monitor(self.path);self.addCleanup(lambda:self.m.close())
        self.m.admit('x',[page('one',1,['a','b'])])
    def test_incomplete_preserves_complete_head(self):
        with self.assertRaises(ValueError):self.m.admit('x',[page('two',2,['a'],next_cursor='missing')])
        self.assertEqual({'a','b'},self.m.state('x'));self.assertEqual([],self.m.ledger())
    def test_complete_empty_emits_real_losses(self):
        r=self.m.admit('x',[page('two',2,[])]);self.assertEqual(2,len(r['events']));self.assertEqual(set(),self.m.state('x'))
    def test_duplicate_retry_is_idempotent_after_reopen(self):
        self.m.admit('x',[page('two',2,['a'])]);self.m.close();self.m=Monitor(self.path)
        self.assertEqual('duplicate',self.m.admit('x',[page('two',2,['a'])])['status']);self.assertEqual(1,len(self.m.ledger()))
    def test_mixed_identity_refused(self):
        with self.assertRaises(ValueError):assemble([page('a',2,['a'],next_cursor='p'),page('b',2,['b'],cursor='p')])
    def test_cursor_cycle_refused(self):
        with self.assertRaises(ValueError):assemble([page('a',2,[],next_cursor='start')])
    def test_duplicate_page_equivalence(self):
        p=page('two',2,['a']);self.assertEqual({'a'},assemble([p,p])[2])
    def test_member_duplicates_refused(self):
        with self.assertRaises(ValueError):assemble([page('two',2,['a','a'])])
    def test_stale_new_id_refused(self):
        with self.assertRaises(ValueError):self.m.admit('x',[page('other',1,[])])
    def test_identity_reuse_different_content_refused(self):
        with self.assertRaises(ValueError):self.m.admit('x',[page('one',1,[])])
    def test_precommit_fault_rolls_back_head_and_events(self):
        with self.assertRaises(RuntimeError):self.m.admit('x',[page('two',2,['a'])],fail_before_commit=True)
        self.assertEqual({'a','b'},self.m.state('x'));self.assertEqual([],self.m.ledger())
        self.assertEqual(1,len(self.m.admit('x',[page('two',2,['a'])])['events']))
    def test_streams_isolated(self):
        self.m.admit('y',[page('one',1,['z'])]);self.assertEqual({'a','b'},self.m.state('x'))
    def test_committed_manifest(self):verify_manifest()
