"""Synthetic files and mocked process operations only; never launch a service."""
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location("owned_model", Path(__file__).with_name("owned_model.py"))
owned = importlib.util.module_from_spec(spec)
spec.loader.exec_module(owned)


class OwnedModelTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve())
        self.root = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def test_exact_hash_and_size_reject_changes(self):
        path = self.root / "fake-model"
        path.write_bytes(b"synthetic only")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(owned.verify_expected(path, 14, digest)["sha256"], digest)
        with self.assertRaises(ValueError):
            owned.verify_expected(path, 13, digest)
        with self.assertRaises(ValueError):
            owned.verify_expected(path, 14, "0" * 64)

    def test_copy_is_independent_and_exclusive(self):
        source, target = self.root / "source", self.root / "target"
        data = b"bounded synthetic model bytes"
        source.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        receipt = owned.copy_exact(source, target, len(data), digest)
        self.assertEqual(target.read_bytes(), data)
        self.assertNotEqual(receipt["source"]["inode"], receipt["copied"]["inode"])
        with self.assertRaises(FileExistsError):
            owned.copy_exact(source, target, len(data), digest)

    def test_symlink_leaf_and_ancestor_rejected(self):
        source = self.root / "ordinary"
        source.write_bytes(b"ok")
        leaf = self.root / "link"
        leaf.symlink_to(source)
        with self.assertRaises(ValueError):
            owned.hash_file(leaf, 2)
        actual = self.root / "actual"
        actual.mkdir()
        (actual / "file").write_bytes(b"ok")
        alias = self.root / "alias"
        alias.symlink_to(actual, target_is_directory=True)
        with self.assertRaises(ValueError):
            owned.hash_file(alias / "file", 2)

    def test_selected_objects_use_models_root_and_no_extra_inventory(self):
        model_root = self.root / "models"
        manifest_path = model_root / "manifests/registry.ollama.ai/library/gemma3/4b"
        refs = [{"digest": "sha256:" + str(i) * 64, "size": i + 1} for i in range(5)]
        selection = {"selectedModel": {"manifestIdentity": {"path": str(manifest_path), "sizeBytes": 1, "sha256": "a" * 64},
                    "manifest": {"config": refs[0], "layers": refs[1:]}}}
        files = owned.selected_files(selection, self.root / "private-models")
        self.assertEqual(len(files), 6)
        self.assertEqual(files[1][0], model_root / "blobs" / ("sha256-" + "0" * 64))
        self.assertEqual(files[-1][1], self.root / "private-models/blobs" / ("sha256-" + "4" * 64))

    def test_credentials_are_metadata_only_and_absence_changes_rejected(self):
        key = self.root / "fake-key"
        key.write_bytes(b"synthetic sentinel")
        key.chmod(0o600)
        config = self.root / "server.json"
        key_metadata = owned.metadata(key)
        selection = {"conventionalOllamaMetadata": [key_metadata, {"path": str(config), "exists": False}]}
        with patch.object(owned, "open_read", side_effect=AssertionError("must not read credentials")):
            result = owned.conventional_metadata(selection)
        self.assertEqual(result[0], key_metadata)
        self.assertNotIn("sha256", result[0])
        config.write_bytes(b"{}")
        with self.assertRaises(ValueError):
            owned.conventional_metadata(selection)

    def test_environment_preserves_home_and_drops_inherited_overrides(self):
        inherited = {"HOME": "/fixed/home", "PATH": "/bin", "OLLAMA_HOST": "unowned:11434",
                     "OLLAMA_MODELS": "/unowned", "HTTP_PROXY": "secret-proxy", "https_proxy": "other",
                     "ALL_PROXY": "third", "no_proxy": "fourth"}
        selection = {"proposedLaunch": {"environment": {"OLLAMA_HOST": "127.0.0.1:0", "OLLAMA_NO_CLOUD": "1"}}}
        env = owned.child_environment(selection, inherited)
        self.assertEqual(env["HOME"], inherited["HOME"])
        self.assertEqual(env["OLLAMA_HOST"], "127.0.0.1:0")
        self.assertNotIn("OLLAMA_MODELS", env)
        self.assertFalse(any(k.lower().endswith("proxy") for k in env))
        self.assertEqual(inherited["OLLAMA_HOST"], "unowned:11434")

    def test_listener_requires_exact_loopback_and_valid_nonzero_port(self):
        self.assertEqual(owned.listener_port(b'level=INFO msg="Listening on 127.0.0.1:54321 (version test)"'), 54321)
        self.assertIsNone(owned.listener_port(b"Listening on 0.0.0.0:11434"))
        self.assertIsNone(owned.listener_port(b"request to 127.0.0.1:11434"))
        with self.assertRaises(ValueError):
            owned.listener_port(b"Listening on 127.0.0.1:0")
        with self.assertRaises(ValueError):
            owned.listener_port(b"Listening on 127.0.0.1:65536")

    def member(self, pid=4321, status=2, uid=None):
        uid = os.getuid() if uid is None else uid
        return {"pid": pid, "ppid": 123, "pgid": 4321, "sid": 4321,
                "uid": uid, "realUid": uid, "savedUid": uid, "status": status,
                "startSeconds": "100", "startMicroseconds": "25"}

    def test_group_snapshot_requires_two_identical_snapshots(self):
        child = SimpleNamespace(pid=4321, returncode=None)
        first, changed = [self.member()], [self.member(), self.member(4322)]
        with patch.object(owned, "darwin_group_members", side_effect=[first, changed, changed, changed]), \
             patch.object(owned, "exited_without_reaping", return_value=False):
            result = owned.checked_owned_group(child)
        self.assertEqual(result["members"], changed)
        self.assertFalse(result["quiescent"])

    def test_foreign_owner_unknown_status_and_wrong_session_refuse_signals(self):
        child = SimpleNamespace(pid=4321, returncode=None)
        for field, value in [("uid", os.getuid()+1), ("realUid", os.getuid()+1), ("savedUid", os.getuid()+1), ("sid", 999), ("pgid", 999), ("status", 9)]:
            members = [self.member(), {**self.member(4322), field: value}]
            with self.subTest(field=field), patch.object(owned, "darwin_group_members", return_value=members), \
                 patch.object(owned, "exited_without_reaping", return_value=False), patch.object(owned.os, "killpg") as kill:
                with self.assertRaises(ValueError): owned.signal_owned_group(child, 15)
                kill.assert_not_called()

    def test_unknown_unstable_or_missing_live_leader_refuses_signals(self):
        child = SimpleNamespace(pid=4321, returncode=None)
        for snapshots in [[[],[]], [[self.member()],[self.member(4322)]]]:
            with patch.object(owned, "darwin_group_members", side_effect=__import__("itertools").cycle(snapshots)), \
                 patch.object(owned, "exited_without_reaping", return_value=False), patch.object(owned.os, "killpg") as kill:
                with self.assertRaises(owned.TransientGroupRead): owned.signal_owned_group(child, 15, timeout_seconds=0)
                kill.assert_not_called()
        with patch.object(owned, "darwin_group_members", side_effect=PermissionError(1,"no identity permission")), patch.object(owned.os, "killpg") as kill:
            with self.assertRaises(PermissionError): owned.signal_owned_group(child, 15)
            kill.assert_not_called()

    def test_reaped_child_is_never_inspected_or_signalled(self):
        with patch.object(owned, "darwin_group_members") as scan, patch.object(owned.os, "killpg") as kill:
            with self.assertRaises(ValueError): owned.signal_owned_group(SimpleNamespace(pid=4321, returncode=0),15)
            scan.assert_not_called(); kill.assert_not_called()

    def test_zombie_only_or_empty_group_requires_unreaped_exit_proof(self):
        child = SimpleNamespace(pid=4321, returncode=None)
        for members in [[],[self.member(status=5)],[self.member(status=5),self.member(4322,status=5)]]:
            with patch.object(owned, "darwin_group_members", return_value=members), \
                 patch.object(owned, "exited_without_reaping", return_value=True), patch.object(owned.os, "killpg") as kill:
                self.assertFalse(owned.signal_owned_group(child,0))
                self.assertFalse(owned.signal_owned_group(child,15))
                kill.assert_not_called()

    def test_zombie_session_unavailable_is_quiescent_but_live_unknown_is_not(self):
        child=SimpleNamespace(pid=4321,returncode=None)
        for status in [5,2]:
            members=[{**self.member(status=status),"sid":None}]
            with patch.object(owned,"darwin_group_members",return_value=members), \
                 patch.object(owned,"exited_without_reaping",return_value=True), patch.object(owned.os,"killpg") as kill:
                if status==5:self.assertFalse(owned.signal_owned_group(child,15))
                else:
                    with self.assertRaises(ValueError):owned.signal_owned_group(child,15)
                kill.assert_not_called()

    def test_live_group_liveness_never_uses_signal_zero(self):
        child=SimpleNamespace(pid=4321,returncode=None)
        with patch.object(owned, "darwin_group_members", return_value=[self.member()]), \
             patch.object(owned, "exited_without_reaping", return_value=False), patch.object(owned.os, "killpg") as kill:
            self.assertTrue(owned.signal_owned_group(child,0));kill.assert_not_called()
            events=[];self.assertTrue(owned.signal_owned_group(child,15,events));kill.assert_called_once_with(4321,15)
            self.assertEqual(events[0]["before"]["members"][0]["startMicroseconds"],"25")
            self.assertTrue(events[0]["sent"])

    def test_eperm_only_recovers_with_new_quiescence_evidence(self):
        child=SimpleNamespace(pid=4321,returncode=None)
        live={"quiescent":False,"members":[self.member()],"leaderExitedUnreaped":False}
        dead={"quiescent":True,"members":[self.member(status=5)],"leaderExitedUnreaped":True}
        for code in [owned.errno.EPERM,owned.errno.ESRCH]:
            events=[]
            with patch.object(owned,"checked_owned_group",side_effect=[live,dead]), patch.object(owned.os,"killpg",side_effect=OSError(code,"race")):
                self.assertFalse(owned.signal_owned_group(child,15,events))
            self.assertEqual(events[0]["errno"],code);self.assertFalse(events[0]["sent"])
            self.assertTrue(events[0]["afterError"]["quiescent"])
        events=[]
        with patch.object(owned,"checked_owned_group",return_value=live), patch.object(owned.os,"killpg",side_effect=PermissionError(1,"denied")):
            with self.assertRaisesRegex(OSError,r"killpg\(4321,15\) failed"): owned.signal_owned_group(child,15,events)
        self.assertEqual(events[0]["errno"],1);self.assertFalse(events[0]["sent"])

    def test_cleanup_keeps_exited_leader_unreaped_until_live_descendant_gone(self):
        order=[];child=SimpleNamespace(pid=4321,returncode=None)
        def wait(timeout): order.append("reap");child.returncode=0
        child.wait=wait
        def send(_child,sig,events=None,context=None,timeout_seconds=2):
            self.assertIsNone(child.returncode);order.append(sig);return True
        final={"quiescent":True,"members":[self.member(status=5)],"leaderExitedUnreaped":True}
        with patch.object(owned,"signal_owned_group",side_effect=send), \
             patch.object(owned,"checked_owned_group",return_value=final), \
             patch.object(owned.time,"monotonic",side_effect=[0,11,11,11,11]):
            result=owned.cleanup_owned(child)
        self.assertEqual(order,[owned.signal.SIGTERM,0,owned.signal.SIGKILL,"reap"])
        self.assertTrue(result["sigkillSentToOwnedGroup"])
        self.assertEqual(result["finalGroupBeforeReap"],final)

    def test_cleanup_unresolved_group_does_not_reap_or_claim_success(self):
        child=SimpleNamespace(pid=4321,returncode=None,wait=Mock());audit={}
        with patch.object(owned,"signal_owned_group",return_value=True), \
             patch.object(owned,"checked_owned_group",return_value={"quiescent":False}), \
             patch.object(owned.time,"monotonic",side_effect=[0,11,11,11,17,17]):
            with self.assertRaises(TimeoutError): owned.cleanup_owned(child,audit=audit)
        child.wait.assert_not_called();self.assertNotIn("exitCode",audit)
        self.assertTrue(audit["sigtermSentToOwnedGroup"])

    def test_supervision_directory_is_owned_and_exclusive_without_copy(self):
        allowed=self.root / "qa";allowed.mkdir()
        output=allowed / "next-run"
        self.assertEqual(owned.create_supervision_directory(output,allowed),output)
        self.assertEqual(output.stat().st_mode & 0o777,0o700)
        self.assertEqual(list(output.iterdir()),[])
        with self.assertRaises(FileExistsError):owned.create_supervision_directory(output,allowed)
        with self.assertRaises(ValueError):owned.create_supervision_directory(self.root / "outside",allowed)
        with self.assertRaises(ValueError):owned.create_supervision_directory(allowed,allowed)
        with self.assertRaises(ValueError):owned.create_supervision_directory(allowed / ".." / "escape",allowed)
        with self.assertRaises(ValueError):owned.create_supervision_directory(Path("relative"),allowed)
        linked=allowed / "alias";linked.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(ValueError):owned.create_supervision_directory(linked / "child",allowed)

    def test_eof_is_unregistered_instead_of_busy_polling(self):
        selector, pipe = Mock(), Mock()
        pipe.fileno.return_value = 123
        with patch.object(owned.os, "read", return_value=b""):
            self.assertEqual(owned.read_pipe_ready(selector, pipe), b"")
        selector.unregister.assert_called_once_with(pipe)

    def test_scheduler_status_change_does_not_change_start_identity(self):
        child = SimpleNamespace(pid=4321, returncode=None)
        context = owned.group_context()
        with patch.object(owned, "darwin_group_members", side_effect=[[self.member(status=2)], [self.member(status=3)]]), \
             patch.object(owned, "exited_without_reaping", return_value=False):
            result = owned.checked_owned_group(child, context)
        self.assertFalse(result["quiescent"])
        self.assertEqual(context["observations"][0]["before"][0]["status"], 2)
        self.assertEqual(context["observations"][0]["after"][0]["status"], 3)

    def test_reused_member_identity_is_fatal_even_with_matching_group_and_uid(self):
        child = SimpleNamespace(pid=4321, returncode=None)
        first = [self.member(), self.member(4322)]
        changed = [self.member(), {**self.member(4322), "startMicroseconds": "26"}]
        context = owned.group_context()
        with patch.object(owned, "darwin_group_members", side_effect=[first, changed]), \
             patch.object(owned, "exited_without_reaping", return_value=False), patch.object(owned.os, "killpg") as kill:
            with self.assertRaisesRegex(ValueError, "PID identity changed"):
                owned.signal_owned_group(child, owned.signal.SIGTERM, context=context)
        kill.assert_not_called()
        self.assertEqual(context["observations"][0]["after"], changed)
        self.assertEqual(context["observations"][0]["outcome"], "identity rejected")

    def test_unreadable_direct_child_needs_waitid_proof_not_assumed_zombie(self):
        child = SimpleNamespace(pid=4321, returncode=None)
        missing = {"pid": 4321, "identityUnavailable": True, "errno": owned.errno.ESRCH, "operation": "proc_pidinfo"}
        for exited in [False, True]:
            context = owned.group_context()
            with patch.object(owned, "darwin_group_members", return_value=[missing]), \
                 patch.object(owned, "exited_without_reaping", return_value=exited), patch.object(owned.os, "killpg") as kill:
                if exited:
                    self.assertFalse(owned.signal_owned_group(child, owned.signal.SIGTERM, context=context))
                    self.assertTrue(context["observations"][0]["leaderExitedAfter"])
                    self.assertNotIn("status", context["observations"][0]["after"][0])
                else:
                    with self.assertRaises(owned.TransientGroupRead):
                        owned.signal_owned_group(child, owned.signal.SIGTERM, context=context, timeout_seconds=0)
                kill.assert_not_called()

    def test_unreadable_other_member_never_inherits_direct_child_exit_proof(self):
        child = SimpleNamespace(pid=4321, returncode=None)
        members = [self.member(status=5), {"pid": 4322, "identityUnavailable": True, "errno": owned.errno.ESRCH}]
        with patch.object(owned, "darwin_group_members", return_value=members), \
             patch.object(owned, "exited_without_reaping", return_value=True), patch.object(owned.os, "killpg") as kill:
            with self.assertRaises(owned.TransientGroupRead):
                owned.signal_owned_group(child, owned.signal.SIGTERM, timeout_seconds=0)
            kill.assert_not_called()

    def test_foreign_member_after_unreadable_member_still_fails_immediately(self):
        child = SimpleNamespace(pid=4321, returncode=None)
        members = [{"pid": 4322, "identityUnavailable": True, "errno": owned.errno.ESRCH},
                   self.member(4323, uid=os.getuid()+1)]
        context = owned.group_context()
        with patch.object(owned, "darwin_group_members", return_value=members) as read, \
             patch.object(owned, "exited_without_reaping", return_value=True), patch.object(owned.os, "killpg") as kill:
            with self.assertRaisesRegex(ValueError, "foreign"):
                owned.signal_owned_group(child, owned.signal.SIGTERM, context=context)
            kill.assert_not_called()
            self.assertEqual(read.call_count, 1)
        self.assertEqual(context["observations"][0]["before"], members)

    def test_post_term_more_than_three_transient_reads_settle_without_extra_signal(self):
        child = SimpleNamespace(pid=4321, returncode=None)
        now = [0.0]; reads = [0]; order = []; audit = {}
        def read(_pgid):
            reads[0] += 1
            if reads[0] <= 2: return [self.member()]
            if reads[0] <= 6: raise ProcessLookupError(owned.errno.ESRCH, "exit transition")
            return [{"pid": 4321, "identityUnavailable": True, "errno": owned.errno.ESRCH}]
        def wait(timeout):
            order.append("reap"); child.returncode = -15
        child.wait = wait
        def kill(pgid, sig):
            self.assertEqual(pgid,4321); self.assertIsNone(child.returncode); order.append(sig)
        with patch.object(owned, "darwin_group_members", side_effect=read), \
             patch.object(owned, "exited_without_reaping", side_effect=lambda _child: reads[0] > 6), \
             patch.object(owned.os, "killpg", side_effect=kill), \
             patch.object(owned.time, "monotonic", side_effect=lambda: now[0]), \
             patch.object(owned.time, "sleep", side_effect=lambda delay: now.__setitem__(0, now[0]+delay)):
            result = owned.cleanup_owned(child, audit=audit)
        self.assertEqual(order, [owned.signal.SIGTERM, "reap"])
        self.assertEqual(result["exitCode"], -15)
        self.assertTrue(result["finalGroupBeforeReap"]["unreadableLeaderExitProven"])
        failed = [e for e in audit["groupObservations"] if e.get("errno") == owned.errno.ESRCH]
        self.assertEqual(len(failed), 4)
        self.assertGreaterEqual(now[0], .2)

    def test_transient_deadline_fails_closed_without_escalation_or_reap(self):
        child = SimpleNamespace(pid=4321, returncode=None, wait=Mock())
        now = [0.0]; reads = [0]; audit = {}
        def read(_pgid):
            reads[0] += 1
            if reads[0] <= 2: return [self.member()]
            raise ProcessLookupError(owned.errno.ESRCH, "unresolved selected group")
        with patch.object(owned, "darwin_group_members", side_effect=read), \
             patch.object(owned, "exited_without_reaping", return_value=False), \
             patch.object(owned.os, "killpg") as kill, \
             patch.object(owned.time, "monotonic", side_effect=lambda: now[0]), \
             patch.object(owned.time, "sleep", side_effect=lambda delay: now.__setitem__(0, now[0]+delay)):
            with self.assertRaises(owned.TransientGroupRead): owned.cleanup_owned(child, grace_seconds=.3, audit=audit)
        kill.assert_called_once_with(4321, owned.signal.SIGTERM)
        child.wait.assert_not_called()
        self.assertLessEqual(now[0], .301)
        self.assertGreater(len(audit["groupObservations"]), 3)
        self.assertNotIn("exitCode", audit)

    def test_audit_bound_refuses_signal_instead_of_dropping_evidence(self):
        child = SimpleNamespace(pid=4321, returncode=None)
        context = owned.group_context(); context["observations"] = [{}] * 512
        with patch.object(owned, "darwin_group_members", return_value=[self.member()]), \
             patch.object(owned, "exited_without_reaping", return_value=False), patch.object(owned.os, "killpg") as kill:
            with self.assertRaisesRegex(ValueError, "audit bound"):
                owned.signal_owned_group(child, owned.signal.SIGTERM, context=context)
            kill.assert_not_called()


if __name__ == "__main__":
    unittest.main()
