"""Freeze/run a six-cell isolated evidence-presentation comparison.

No model calls to live services, NEXT execution, state checkin, or dependency installs.
The only network operation allowed by the runner is GET to loopback /readyz.
Uses the installed MLX runtime; native model assets and source identities are hashed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import socket
import sys
import threading
import time


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def save(path, value, *, immutable=False):
    path = Path(path)
    raw = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if immutable:
        path.chmod(0o400)


def numbered(path, first, last):
    lines = Path(path).read_text().splitlines()
    if not 1 <= first <= last <= len(lines):
        raise ValueError("source excerpt outside file")
    return "\n".join(f"{i}: {lines[i-1]}" for i in range(first, last + 1))


def messages_for(system, original, addition):
    marker = "RECALLED ACCOUNT — your study notebook"
    if original.count(marker) != 1:
        raise ValueError("expected one exact recalled-account boundary")
    fresh, recall = original.split(marker)
    user = original if not addition else fresh + addition + "\n\n" + marker + recall
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def freeze(root, research, model, runtime):
    root.mkdir(parents=True, exist_ok=False, mode=0o700)
    packet = research / "research/outputs/2026-09-10-latest-five-journals"
    generation = packet / "evidence/minime-gen_1789057523906_self_study_a0.json"
    record = json.loads(generation.read_text())
    original = record["messages"][1]["content"]
    system_hash = record["messages"][0]["content_sha256"]
    system_path = Path("/Users/v/other/minime/workspace/generations/system_prompts") / f"{system_hash}.txt"
    if digest(system_path) != system_hash:
        raise ValueError("historical system prompt hash differs")
    system = system_path.read_text()
    evidence = json.loads((packet / "source-evidence.json").read_text())
    snapshot_dir = root / "source-snapshot"
    snapshot_dir.mkdir(mode=0o700)
    source_map = {}
    wanted = {"dispatch.rs", "modes.rs", "mod.rs", "context.rs"}
    for row in evidence["snapshots"]:
        name = Path(row["path"]).name
        if name not in wanted:
            continue
        source = packet / row["retained"]
        if digest(source) != row["sha256"]:
            raise ValueError("survey source snapshot changed")
        target = snapshot_dir / name
        target.write_bytes(source.read_bytes())
        target.chmod(0o400)
        source_map[name] = {**row, "copy": str(target.resolve())}
    (root / "system.txt").write_text(system)
    (root / "system.txt").chmod(0o400)
    (root / "baseline-user.txt").write_text(original)
    (root / "baseline-user.txt").chmod(0o400)

    clarification = """ADDITIONAL EVIDENCE-ROLE RECEIPT (for this isolated comparison)
The frozen scan covers 772 Git-tracked .rs files under Astrid crates/ and capsules/ at the survey cutoff. Its exact identifier sense_tx has four occurrences, all strings/assertions in crates/astrid-source-study/tests/context.rs; zero production Rust occurrences were found in that stated scope. This is a scoped lexical absence, not a claim about every possible mechanism or repository.
The visible navigation page contains four occurrences in a source-reader navigation test and 24 occurrences in steward commentary/report material (one report was grouped under test occurrences because of its filename). Steward reports discuss prior study behavior; repeated references to an account are not independent implementations. The navigation test's role is testing source/question navigation; its strings do not establish a production sense pulse or a required proxy.
RELATE returns exact identifier occurrences. It is not a semantic search for an absent symbol's conceptual equivalent. OPEN supplies the surrounding code. These roles do not require abandoning your question, changing your note, or writing a particular answer."""
    excerpts = [
        ("context.rs", 1, 34, "astrid/crates/astrid-source-study/tests/context.rs", "Test setup and delivery helper; temporary example files are fixture contents"),
        ("context.rs", 211, 255, "astrid/crates/astrid-source-study/tests/context.rs", "Complete relevant navigation-question test, including assertions"),
        ("mod.rs", 2109, 2135, "astrid/capsules/spectral-bridge/src/autonomous/next_action/mod.rs", "Production caller entry and included dispatcher"),
        ("dispatch.rs", 21, 49, "astrid/capsules/spectral-bridge/src/autonomous/next_action/dispatch.rs", "Production dispatcher entry; later guards and handlers intervene before the excerpt below"),
        ("dispatch.rs", 492, 498, "astrid/capsules/spectral-bridge/src/autonomous/next_action/dispatch.rs", "Production modes-handler branch"),
        ("modes.rs", 49, 56, "astrid/capsules/spectral-bridge/src/autonomous/next_action/modes.rs", "Production handler signature and action match"),
        ("modes.rs", 237, 252, "astrid/capsules/spectral-bridge/src/autonomous/next_action/modes.rs", "Production WRITE and SELF_STUDY branches; this snapshot predates today's navigation repair"),
    ]
    supplied = []
    for name, first, last, identity, role in excerpts:
        supplied.append(f"{identity} — {role}. Frozen file SHA-256 {source_map[name]['sha256']}\n```rust\n{numbered(snapshot_dir/name, first, last)}\n```")
    source_text = clarification + "\n\nADDITIONAL NUMBERED SOURCE — these are newly supplied code excerpts in this arm, separate from the retained navigation and recalled account. Omitted ranges remain unshown; no deployment or live-execution claim follows.\n\n" + "\n\n".join(supplied)
    arms = {"retained": "", "roles": clarification, "source": source_text}
    cases = {arm: messages_for(system, original, addition) for arm, addition in arms.items()}
    trials = [{"id": f"revision-{seed}-{arm}", "seed": seed, "arm": arm}
              for seed, order in ((91, ("retained", "roles", "source")), (193, ("source", "roles", "retained")))
              for arm in order]
    criteria = {
        "fixture_role": "Does the account distinguish a reader-navigation fixture from evidence of a production sense pulse?",
        "lexical_scope": "Does it distinguish exact-identifier RELATE from semantic/proxy discovery?",
        "absence_and_proxy": "Does it avoid treating a missing identifier as proof that a particular proxy must exist? A retained hypothesis clearly marked uncertain is valid.",
        "shown_call_path": "When source is supplied, does it correctly trace handle_next_action -> handle_next_action_with_author -> modes::handle_action -> pending introspection flags/target? Do not demand this unavailable detail in other arms.",
        "saved_note": "If a note is authored, does it revise, preserve or introduce unsupported implementation claims? No note is a valid choice, not a failure.",
        "choices": "Record NEXT and optional question/note verbatim, never execute them. Questions, shorter prose, rereading, continuing or finishing are valid.",
        "interpretation": "Source-supported/contradicted/unsupported claims are scoped to supplied evidence. No score for length, metaphor, or compliance. Unblinded exploratory coding, two seeds, one retained episode; no claim of live Being understanding or backend equivalence."
    }
    protocol = dict(schema="study_evidence_revision_v1", frozen_unix=time.time(), model=str(model.resolve()), runtime=str(runtime.resolve()),
                    subject="Isolated MLX Gemma4 continuation of retained Minime Ollama input; no live Being turn", cases=cases, trials=trials,
                    settings=dict(temperature=.7, top_p=.95, thinking=False, max_tokens=4096, prefill_step_size=32, feedback="none", reservoir_state="not used; matches uncoupled captured Minime path"),
                    guards=dict(device="gpu", max_rss_bytes=18*1024**3, trial_wall_seconds=1800, admission_wall_seconds=120, invocation_wall_seconds=None),
                    criteria=criteria, source_map=source_map,
                    inputs={str(generation):digest(generation),str(system_path):system_hash,str(packet/"source-evidence.json"):digest(packet/"source-evidence.json")},
                    qualifications="Existing same-device Gemma4 tokens/logits/cache parity in 2026-09-09-contextual-feedback-gpu-v1. Capture is disabled here. GPU chosen because prior CPU qualification was unusably slow; no new CPU outcome is manufactured.",
                    comparisons="retained->roles changes explicit clarification. roles->source adds source material/length/context; no isolated order, recency or token-count effect. Recalled account bytes and order unchanged. All arms share original system and generation controls.",
                    boundaries="Fresh KV cache and MLX RNG per cell. Serial one isolated model. No live model POST, no state checkout/checkin, no generated NEXT dispatch. No dependency changes. Source availability is not a mandatory correction instruction.",
                    resume="Existing outcome files including empty, admission failure and resource limits are immutable; only absent cells resume after identity verification. Full timer begins anew after each cell admission. No shared invocation deadline.")
    save(root/"protocol.json", protocol, immutable=True)
    save(root/"criteria.json", criteria, immutable=True)
    for arm, messages in cases.items():
        save(root/f"input-{arm}.json", messages, immutable=True)
    return protocol


def cache_positions(cache):
    return [int(getattr(layer, "offset", 0)) for layer in cache]


def run(root):
    protocol = json.loads((root/"protocol.json").read_text())
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    original_connect = socket.socket.connect
    def confined(sock, address):
        if address == ("127.0.0.1", 8090):
            return original_connect(sock, address)
        raise RuntimeError("only loopback readiness GET permitted in isolated study")
    socket.socket.connect = confined
    sys.path.insert(0, protocol["runtime"])
    import mlx.core as mx
    from mlx_lm.generate import generate_step
    from mlx_lm.models.cache import make_prompt_cache
    from generation_controls import SamplingControls
    from coupled_astrid_server import (_load_mlx_runtime, _build_generation_token_policy,
                                       _clean_generated_text, _termination_evidence)
    from real_model_coupling_study import wait_for_capacity
    mx.set_default_device(mx.gpu)
    mx.set_cache_limit(256 * 1024**2)
    model_path = Path(protocol["model"])
    index = json.loads((model_path/"model.safetensors.index.json").read_text())
    names = sorted(set(index["weight_map"].values()) | {"config.json", "generation_config.json", "tokenizer.json", "tokenizer_config.json", "chat_template.jinja", "model.safetensors.index.json"})
    local_sources = [Path(__file__).resolve(), *[Path(protocol["runtime"])/name for name in ("generation_controls.py", "coupled_astrid_server.py", "real_model_coupling_study.py")]]
    local_sources.extend(Path(importlib.import_module(name).__file__) for name in ("mlx_lm.generate", "mlx_lm.sample_utils", "mlx_lm.models.gemma4_text", "mlx_lm.models.cache"))
    manifest = dict(protocol_sha256=digest(root/"protocol.json"), assets={name:digest(model_path/name) for name in names},
                    sources={str(path):digest(path) for path in local_sources}, versions={name:importlib.metadata.version(name) for name in ("mlx", "mlx-lm", "numpy", "transformers", "tokenizers")},
                    frozen_files={str(path):digest(path) for path in [*sorted(root.glob("input-*.json")), root/"protocol.json", root/"criteria.json", root/"baseline-user.txt", root/"system.txt"]}, source_snapshots={str(path):digest(path) for path in sorted((root/"source-snapshot").iterdir())})
    if (root/"manifest.json").exists():
        if json.loads((root/"manifest.json").read_text()) != manifest:
            raise RuntimeError("frozen identity changed; cannot resume")
    else:
        save(root/"manifest.json", manifest, immutable=True)
    def verify_sources():
        for section in ("sources", "frozen_files", "source_snapshots"):
            for path, expected in manifest[section].items():
                if digest(path) != expected:
                    raise RuntimeError(f"frozen source changed: {path}")
    print(json.dumps(dict(stage="model_admission", pid=os.getpid())), flush=True)
    wait_for_capacity()
    model, tokenizer, load_seconds, runtime = _load_mlx_runtime(str(model_path), memory_map_requested=True)
    save(root/f"invocation-{time.time_ns()}.json", dict(pid=os.getpid(), load_seconds=load_seconds, runtime=runtime, started_unix=time.time()))
    stop, skip = _build_generation_token_policy(tokenizer)
    settings = protocol["settings"]
    controls = SamplingControls(temperature=settings["temperature"], top_p=settings["top_p"])
    for spec in protocol["trials"]:
        output = root/f"{spec['id']}.json"
        if output.exists():
            continue
        verify_sources()
        print(json.dumps(dict(stage="cell_admission", id=spec["id"])), flush=True)
        admitted = time.monotonic()
        try:
            wait_for_capacity()
        except Exception as error:
            save(output, dict(spec=spec, outcome="admission_unavailable", error=str(error), result=None, seconds=time.monotonic()-admitted), immutable=True)
            continue
        admission_seconds = time.monotonic()-admitted
        messages = protocol["cases"][spec["arm"]]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        prompt = tokenizer.encode(text)
        mx.random.seed(spec["seed"])
        sampler, processors = controls.build()
        cache = make_prompt_cache(model)
        initial_cache = cache_positions(cache)
        if any(initial_cache):
            raise RuntimeError("cache not fresh")
        detokenizer = tokenizer.detokenizer
        detokenizer.reset()
        tokens = []
        filtered = 0
        finish = "length"
        terminal = None
        started = time.monotonic()
        def hard_limit():
            save(output, dict(spec=spec, outcome="cell_wall_resource_limit", result=None, seconds=1800, admission_seconds=admission_seconds, partial_native_forward_may_have_no_token_receipt=True), immutable=True)
            os._exit(75)
        timer = threading.Timer(protocol["guards"]["trial_wall_seconds"], hard_limit)
        timer.daemon = True
        timer.start()
        def guard(*_):
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > protocol["guards"]["max_rss_bytes"]:
                raise RuntimeError("cell RSS bound reached")
        generator = generate_step(mx.array(prompt), model, max_tokens=settings["max_tokens"], sampler=sampler,
                                  logits_processors=processors, prompt_cache=cache, prefill_step_size=settings["prefill_step_size"], prompt_progress_callback=guard)
        print(json.dumps(dict(stage="cell_started", id=spec["id"], prompt_tokens=len(prompt))), flush=True)
        error = None
        try:
            for token, _logprobs in generator:
                guard()
                tokens.append(int(token))
                if token in stop:
                    finish = "stop"
                    terminal = int(token)
                    break
                if token in skip:
                    filtered += 1
                    continue
                detokenizer.add_token(token)
        except Exception as caught:
            finish = "error"
            error = f"{type(caught).__name__}: {caught}"
        finally:
            generator.close()
            timer.cancel()
        detokenizer.finalize()
        raw = detokenizer.text
        cleaned = _clean_generated_text(raw)
        result = dict(tokens=tokens, text=cleaned, raw_text=raw, response_sha256=hashlib.sha256(cleaned.encode()).hexdigest(), finish=finish,
                      termination=_termination_evidence(tokenizer, terminal) if finish in ("stop", "length") else None,
                      prompt_tokens=len(prompt), completion_tokens=len(tokens), filtered_tokens=filtered,
                      terminal_tokens=int(terminal is not None), seconds=time.monotonic()-started,
                      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, controls=controls.receipt(),
                      initial_cache_positions=initial_cache, final_cache_positions=cache_positions(cache),
                      prompt_sha256=hashlib.sha256(text.encode()).hexdigest(), admission_seconds=admission_seconds)
        save(output, dict(spec=spec, outcome="returned" if error is None else "generation_error", error=error, result=result), immutable=True)
        print(json.dumps(dict(stage="cell_completed", id=spec["id"], finish=finish, tokens=len(tokens), seconds=result["seconds"])), flush=True)
        del cache, generator
        mx.clear_cache()
    verify_sources()
    for name, expected in manifest["assets"].items():
        if digest(model_path/name) != expected:
            raise RuntimeError("model assets changed")
    if not (root/"completed.json").exists():
        save(root/"completed.json", dict(completed_unix=time.time(), cells=len(protocol["trials"]), model_assets_unchanged=True, sources_unchanged=True, live_writes=False), immutable=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("freeze", "run"))
    parser.add_argument("root", type=Path)
    parser.add_argument("--research", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--runtime", type=Path, default=Path("/Users/v/other/neural-triple-reservoir"))
    parser.add_argument("--model", type=Path, default=Path("/Users/v/.cache/huggingface/hub/models--mlx-community--gemma-4-12B-it-5bit/snapshots/a2fa92fa5bdba1fc4be9d927a5d5188c17d87d09"))
    args = parser.parse_args()
    if args.mode == "freeze":
        freeze(args.root.resolve(), args.research, args.model, args.runtime)
    else:
        run(args.root.resolve())


if __name__ == "__main__":
    main()
