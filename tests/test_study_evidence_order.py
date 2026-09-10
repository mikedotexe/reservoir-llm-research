"""Protocol and serial-runner integrity checks; no model or live-service calls."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import socket
import sys
import tempfile
import types
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "probes/study_evidence_order.py"
spec = importlib.util.spec_from_file_location("study_evidence_order", MODULE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
PREVIOUS_SHA = "2899b26d5646c2460ee388d47ec1e970cbf2d60aa26a70859526bfbcf4d34bd1"
EVIDENCE = "ADDITIONAL EVIDENCE-ROLE RECEIPT (for this isolated comparison)\nsource λ\n```rust\n1: code();\n```\n\n"
RECALL = 'RECALLED ACCOUNT — your study notebook\n{"question":"Why?","previous":"earlier λ"}\nEnd of study notebook.\n'
PREFIX = "THIS TURN — current navigation\nYOUR CURRENT QUESTION — Why?\n\n"
SYSTEM = "Same system; no compulsory correction or minimum length.\n"


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n")


def fixture_previous(root):
    previous = root / "previous"
    (previous / "source-snapshot").mkdir(parents=True)
    source = previous / "source-snapshot/context.rs"
    source.write_bytes(b"// original fixture source\n")
    protocol = {
        "cases": {
            "source": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": PREFIX + EVIDENCE + RECALL}],
            "retained": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": PREFIX + RECALL}],
        },
        "source_map": {"context.rs": {"sha256": probe.digest(source), "path": "original/context.rs"}},
        "criteria": {"interpretation": "Old comparison used two seeds."},
        "model": str(root / "model"), "runtime": str(root / "runtime"),
        "settings": {"temperature": .7, "top_p": .95, "thinking": False, "max_tokens": 4096, "prefill_step_size": 32, "feedback": "none"},
        "guards": {"device": "gpu", "max_rss_bytes": 18 * 1024**3, "trial_wall_seconds": 1800, "admission_wall_seconds": 120, "invocation_wall_seconds": None},
        "subject": "Isolated historical replay", "qualifications": "Prior capture-disabled qualification",
        "boundaries": "Fresh cache; no live writes", "resume": "Retain every existing result",
    }
    write_json(previous / "protocol.json", protocol)
    return previous, protocol


def freeze_fixture(root):
    previous, prior = fixture_previous(root)
    destination = root / "new"
    real_digest = probe.digest
    # The semantic fixture has its own identity; the production freeze still
    # verifies the pinned real predecessor in a separate integration check.
    def fixture_digest(path):
        return PREVIOUS_SHA if Path(path) == previous / "protocol.json" else real_digest(path)
    with mock.patch.object(probe, "digest", side_effect=fixture_digest):
        protocol = probe.freeze(destination, previous)
    return destination, previous, prior, protocol


@contextlib.contextmanager
def fake_runtime(root, *, change_render_on=None):
    """Exercise the actual run loop with deterministic stand-ins at GPU seams."""
    runtime = root / "runtime"
    runtime.mkdir()
    model = root / "model"
    model.mkdir()
    names = {"weights.safetensors", "config.json", "generation_config.json", "tokenizer.json", "tokenizer_config.json", "chat_template.jinja"}
    for name in names:
        (model / name).write_text("immutable test asset\n")
    write_json(model / "model.safetensors.index.json", {"weight_map": {"weight": "weights.safetensors"}})
    calls = {"seeds": [], "controls": [], "generation": [], "caches": [], "renders": [], "timers": [], "admissions": 0}
    modules = {}
    for name in ("mlx", "mlx.core", "mlx_lm", "mlx_lm.generate", "mlx_lm.sample_utils", "mlx_lm.models", "mlx_lm.models.gemma4_text", "mlx_lm.models.cache", "generation_controls", "coupled_astrid_server", "real_model_coupling_study"):
        module = types.ModuleType(name)
        module.__path__ = []
        filename = name if "." not in name else name.replace(".", "_")
        path = runtime / f"{filename}.py"
        path.write_text("# deterministic test seam\n")
        module.__file__ = str(path)
        modules[name] = module
    mx = modules["mlx.core"]
    mx.gpu = "fake_gpu"
    mx.set_default_device = lambda device: None
    mx.set_cache_limit = lambda limit: None
    mx.clear_cache = lambda: None
    mx.array = lambda values: values
    mx.random = types.SimpleNamespace(seed=lambda seed: calls["seeds"].append(seed))
    class Controls:
        def __init__(self, **kwargs):
            self.values = kwargs
        def build(self):
            calls["controls"].append(self.values.copy())
            return "test_sampler", []
        def receipt(self):
            return self.values.copy()
    modules["generation_controls"].SamplingControls = Controls
    class Detokenizer:
        text = ""
        def reset(self):
            self.text = ""
        def add_token(self, token):
            self.text += f"visible-{token}"
        def finalize(self):
            pass
    class Tokenizer:
        detokenizer = Detokenizer()
        def apply_chat_template(self, messages, **kwargs):
            calls["renders"].append((messages, kwargs))
            rendered = messages[0]["content"] + "<user>" + messages[1]["content"] + "<assistant>"
            if len(calls["renders"]) == change_render_on:
                rendered += "changed"
            return rendered
        def encode(self, text):
            # Intentionally unequal counts: byte-preserving reordering need not
            # preserve tokens across boundaries, and the runner must record it.
            return [1, 2] if text.endswith(RECALL + "<assistant>") else [1, 3, 4]
    def make_cache(model):
        cache = [types.SimpleNamespace(offset=0)]
        calls["caches"].append(cache)
        return cache
    modules["mlx_lm.models.cache"].make_prompt_cache = make_cache
    def generate(prompt, model, **kwargs):
        calls["generation"].append((prompt, kwargs))
        cache = kwargs["prompt_cache"]
        cache[0].offset = len(prompt)
        for token in (9, 42, 0):
            cache[0].offset += 1
            yield token, None
    modules["mlx_lm.generate"].generate_step = generate
    server = modules["coupled_astrid_server"]
    server._load_mlx_runtime = lambda *args, **kwargs: (object(), Tokenizer(), 0, {"test_only": True})
    server._build_generation_token_policy = lambda tokenizer: ({0}, {9})
    server._clean_generated_text = lambda text: text
    server._termination_evidence = lambda tokenizer, token: {"kind": "eos" if token == 0 else "allowance"}
    def admission():
        calls["admissions"] += 1
    modules["real_model_coupling_study"].wait_for_capacity = admission
    class Timer:
        def __init__(self, seconds, callback):
            calls["timers"].append(seconds)
        def start(self):
            pass
        def cancel(self):
            pass
    with mock.patch.dict(sys.modules, modules), mock.patch.object(sys, "path", list(sys.path)), mock.patch.object(socket.socket, "connect", socket.socket.connect), mock.patch.object(probe.importlib.metadata, "version", return_value="test-version"), mock.patch.object(probe.threading, "Timer", Timer), mock.patch.dict(probe.os.environ, {}, clear=False), contextlib.redirect_stdout(io.StringIO()):
        yield calls


class EvidenceOrderTests(unittest.TestCase):
    def test_split_preserves_unicode_whitespace_json_and_complete_notebook(self):
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": PREFIX + EVIDENCE + RECALL}]
        self.assertEqual(probe.split_blocks(messages), (PREFIX, EVIDENCE, RECALL))

    def test_malformed_or_ambiguous_boundaries_are_rejected(self):
        malformed = [PREFIX + RECALL, PREFIX + EVIDENCE, PREFIX + EVIDENCE * 2 + RECALL, PREFIX + EVIDENCE + RECALL * 2, PREFIX + RECALL + EVIDENCE]
        for user in malformed:
            with self.subTest(user=user), self.assertRaises(ValueError):
                probe.split_blocks([{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}])
        for messages in ([], [{"role": "user", "content": "x"}], [{"role": "user", "content": SYSTEM}, {"role": "system", "content": PREFIX + EVIDENCE + RECALL}]):
            with self.subTest(messages=messages), self.assertRaises(ValueError):
                probe.split_blocks(messages)

    def test_freeze_keeps_blocks_questions_controls_sources_and_balanced_pairs(self):
        with tempfile.TemporaryDirectory() as temp:
            destination, previous, prior, protocol = freeze_fixture(Path(temp))
            arms = protocol["cases"]
            self.assertEqual(arms["evidence_then_recall"], prior["cases"]["source"])
            self.assertEqual(arms["recall_then_evidence"][1]["content"], PREFIX + RECALL + EVIDENCE)
            for messages in arms.values():
                self.assertEqual(messages[0], prior["cases"]["source"][0])
                self.assertEqual(messages[1]["content"].count("Why?"), 2)
                self.assertEqual(sorted(messages[1]["content"]), sorted(PREFIX + EVIDENCE + RECALL))
            for name, content in (("prefix", PREFIX), ("evidence", EVIDENCE), ("recall", RECALL)):
                self.assertEqual((destination / f"block-{name}.txt").read_bytes(), content.encode())
                self.assertEqual(protocol["blocks"][name], {"bytes": len(content.encode()), "sha256": hashlib.sha256(content.encode()).hexdigest()})
            self.assertEqual(protocol["settings"], prior["settings"])
            self.assertEqual(protocol["guards"], prior["guards"])
            self.assertEqual((destination / "source-snapshot/context.rs").read_bytes(), (previous / "source-snapshot/context.rs").read_bytes())
            self.assertEqual(json.loads((previous / "protocol.json").read_text()), prior)
            specs = protocol["trials"]
            self.assertEqual(len(specs), 8)
            self.assertEqual(len({row["id"] for row in specs}), 8)
            self.assertEqual([row["seed"] for row in specs], [307, 307, 419, 419, 631, 631, 887, 887])
            self.assertEqual([specs[i]["arm"] for i in (0, 2, 4, 6)].count("evidence_then_recall"), 2)
            for start in range(0, 8, 2):
                self.assertEqual({row["arm"] for row in specs[start:start + 2]}, set(arms))

    def test_unrecognized_predecessor_identity_fails_before_creating_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            previous, _ = fixture_previous(root)
            with self.assertRaisesRegex(ValueError, "protocol identity"):
                probe.freeze(root / "new", previous)
            self.assertFalse((root / "new").exists())

    def test_real_frozen_predecessor_is_copied_without_changes(self):
        previous = ROOT / "research/outputs/2026-09-10-evidence-revision-v1"
        if not previous.exists():
            self.skipTest("retained local historical packet unavailable")
        paths = [previous / "protocol.json", *sorted((previous / "source-snapshot").iterdir())]
        before = {path: path.read_bytes() for path in paths}
        with tempfile.TemporaryDirectory() as temp:
            protocol = probe.freeze(Path(temp) / "new", previous)
            self.assertEqual(protocol["blocks"]["prefix"]["bytes"], 7247)
            self.assertEqual(protocol["blocks"]["evidence"]["bytes"], 10151)
            self.assertEqual(protocol["blocks"]["recall"]["bytes"], 8319)
        self.assertEqual(before, {path: path.read_bytes() for path in paths})

    def test_actual_run_retains_rendering_fresh_cache_controls_and_existing_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            destination, _, _, protocol = freeze_fixture(root)
            first = protocol["trials"][0]
            saved_failure = {"spec": first, "outcome": "admission_unavailable", "result": None}
            probe.save(destination / f"{first['id']}.json", saved_failure, immutable=True)
            with fake_runtime(root) as calls:
                probe.run(destination)
                self.assertEqual(len(calls["generation"]), 7)
                self.assertEqual(calls["seeds"], [row["seed"] for row in protocol["trials"][1:]])
                self.assertEqual(calls["controls"], [{"temperature": .7, "top_p": .95}] * 7)
                self.assertEqual(len({id(cache) for cache in calls["caches"]}), 7)
                self.assertEqual(calls["timers"], [1800] * 7)
                for _, settings in calls["generation"]:
                    self.assertEqual(settings["max_tokens"], 4096)
                    self.assertEqual(settings["prefill_step_size"], 32)
                    self.assertEqual(settings["sampler"], "test_sampler")
                    self.assertEqual(settings["logits_processors"], [])
                for _, settings in calls["renders"]:
                    self.assertEqual(settings, {"tokenize": False, "add_generation_prompt": True, "enable_thinking": False})
                before = {p.name: p.read_bytes() for p in destination.glob("order-*.json")}
                probe.run(destination)
                self.assertEqual(len(calls["generation"]), 7)
                self.assertEqual(before, {p.name: p.read_bytes() for p in destination.glob("order-*.json")})
            self.assertEqual(json.loads((destination / f"{first['id']}.json").read_text()), saved_failure)
            counts = set()
            for arm in protocol["cases"]:
                row = json.loads((destination / f"rendered-{arm}.json").read_text())
                counts.add(row["token_count"])
                self.assertEqual(row["token_count"], len(row["token_ids"]))
                self.assertEqual(row["rendered_sha256"], hashlib.sha256(row["rendered_text"].encode()).hexdigest())
                self.assertIn(protocol["cases"][arm][1]["content"], row["rendered_text"])
            self.assertEqual(counts, {2, 3})
            for trial in protocol["trials"][1:]:
                result = json.loads((destination / f"{trial['id']}.json").read_text())["result"]
                self.assertEqual(result["initial_cache_positions"], [0])
                self.assertEqual((result["completion_tokens"], result["filtered_tokens"], result["terminal_tokens"]), (3, 1, 1))
                self.assertEqual(result["text"], "visible-42")
                self.assertEqual(result["finish"], "stop")

    def test_changed_rendering_stops_before_another_generation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            destination, _, _, protocol = freeze_fixture(root)
            with fake_runtime(root, change_render_on=3) as calls:
                with self.assertRaisesRegex(RuntimeError, "rendered prompt changed"):
                    probe.run(destination)
                self.assertEqual(len(calls["generation"]), 2)
            self.assertFalse((destination / f"{protocol['trials'][2]['id']}.json").exists())
            self.assertFalse((destination / "completed.json").exists())

    def test_immutable_save_cannot_replace_retained_partial_or_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "cell.json"
            probe.save(path, {"outcome": "cell_wall_resource_limit"}, immutable=True)
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                probe.save(path, {"outcome": "preferred answer"}, immutable=True)
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
