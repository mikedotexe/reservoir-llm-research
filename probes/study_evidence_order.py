"""Freeze/run an eight-cell isolated byte-preserving evidence-order comparison.

The qualified serial execution loop is retained from study_evidence_revision.py;
that predecessor runner and its frozen experiment remain unchanged.

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


def split_blocks(messages):
    """Extract exact historical blocks without normalizing whitespace or JSON."""
    if len(messages) != 2 or [m["role"] for m in messages] != ["system", "user"]:
        raise ValueError("expected the historical two-message input")
    user = messages[1]["content"]
    evidence_marker = "ADDITIONAL EVIDENCE-ROLE RECEIPT (for this isolated comparison)"
    recall_marker = "RECALLED ACCOUNT — your study notebook"
    if user.count(evidence_marker) != 1 or user.count(recall_marker) != 1:
        raise ValueError("expected unique exact evidence and recall boundaries")
    a, b = user.index(evidence_marker), user.index(recall_marker)
    if a >= b:
        raise ValueError("predecessor order differs")
    return user[:a], user[a:b], user[b:]


def freeze(root, previous):
    predecessor_path = previous / "protocol.json"
    expected = "2899b26d5646c2460ee388d47ec1e970cbf2d60aa26a70859526bfbcf4d34bd1"
    if digest(predecessor_path) != expected:
        raise ValueError("historical protocol identity differs")
    prior = json.loads(predecessor_path.read_text())
    system = prior["cases"]["source"][0]["content"]
    prefix, evidence, recall = split_blocks(prior["cases"]["source"])
    if prefix + recall != prior["cases"]["retained"][1]["content"]:
        raise ValueError("prefix/recall do not exactly reconstruct original retained input")
    root.mkdir(parents=True, exist_ok=False, mode=0o700)
    source_dir = root / "source-snapshot"
    source_dir.mkdir(mode=0o700)
    source_map = {}
    for name, row in prior["source_map"].items():
        source = previous / "source-snapshot" / name
        if digest(source) != row["sha256"]:
            raise ValueError("historical source changed")
        target = source_dir / name
        target.write_bytes(source.read_bytes()); target.chmod(0o400)
        source_map[name] = {**row, "copy": str(target.resolve())}
    blocks = {"prefix": prefix, "evidence": evidence, "recall": recall}
    block_receipt = {}
    for name, content in blocks.items():
        path = root / f"block-{name}.txt"
        path.write_bytes(content.encode()); path.chmod(0o400)
        block_receipt[name] = {"bytes": len(content.encode()), "sha256": digest(path)}
    cases = {}
    for arm, text in (("evidence_then_recall", prefix + evidence + recall),
                      ("recall_then_evidence", prefix + recall + evidence)):
        cases[arm] = [{"role": "system", "content": system}, {"role": "user", "content": text}]
        save(root / f"input-{arm}.json", cases[arm], immutable=True)
    for name, text in (("system.txt", system), ("baseline-user.txt", prefix + evidence + recall)):
        path = root / name; path.write_bytes(text.encode()); path.chmod(0o400)
    seeds = (307, 419, 631, 887)
    arms = tuple(cases)
    trials = [{"id": f"order-{seed}-{arm}", "seed": seed, "arm": arm}
              for index, seed in enumerate(seeds)
              for arm in (arms if index % 2 == 0 else tuple(reversed(arms)))]
    criteria = dict(prior["criteria"])
    criteria["primary"] = "Proxy necessity: explicit revision/retraction or uncertainty versus retaining an asserted production-proxy premise. Merely calling a name phantom/fixture-only is not correction. Absent assessment remains unassessed."
    criteria["coding"] = "First-pass source-grounding annotations use arm-blind response IDs where feasible. Record exact quotes and response hashes before revealing arm/seed. Report four paired seeds, one episode; no independent-eight-example or live-Being inference."
    criteria["interpretation"] = "Exploratory first-pass arm-blind coding, four paired seeds from one retained episode. Reveal arm and seed only after hash-checked annotations are retained. No population or live-Being learning inference."
    protocol = dict(schema="study_evidence_order_v1", frozen_unix=time.time(),
        previous={"path": str(predecessor_path.resolve()), "sha256": expected},
        model=prior["model"], runtime=prior["runtime"], cases=cases, trials=trials,
        settings=prior["settings"], guards=prior["guards"], criteria=criteria, blocks=block_receipt,
        source_map=source_map, inputs={str(predecessor_path.resolve()): expected},
        subject=prior["subject"], qualifications=prior["qualifications"], boundaries=prior["boundaries"], resume=prior["resume"],
        comparisons="P+E+R versus P+R+E. Same byte-identical blocks, system and question content; no new footer or demand. Block boundaries, adjacency and last-position content move together. Rendered prompt/token IDs/counts recorded; equal token counts are not assumed. Four paired fresh seeds with balanced serial arm order. This local presentation experiment does not isolate a general recency mechanism or test live Being learning.")
    save(root / "criteria.json", criteria, immutable=True)
    save(root / "protocol.json", protocol, immutable=True)
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
                    frozen_files={str(path):digest(path) for path in [*sorted(root.glob("input-*.json")), root/"protocol.json", root/"criteria.json", root/"baseline-user.txt", root/"system.txt", *sorted(root.glob("block-*.txt"))]}, source_snapshots={str(path):digest(path) for path in sorted((root/"source-snapshot").iterdir())})
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
        prompt_record = dict(arm=spec["arm"], rendered_text=text, token_ids=prompt,
                             token_count=len(prompt), rendered_sha256=hashlib.sha256(text.encode()).hexdigest())
        prompt_path = root / f"rendered-{spec['arm']}.json"
        if prompt_path.exists():
            if json.loads(prompt_path.read_text()) != prompt_record:
                raise RuntimeError("rendered prompt changed between paired trials")
        else:
            save(prompt_path, prompt_record, immutable=True)
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
    parser.add_argument("--previous", type=Path, default=Path(__file__).resolve().parents[1] / "research/outputs/2026-09-10-evidence-revision-v1")
    args = parser.parse_args()
    if args.mode == "freeze":
        freeze(args.root.resolve(), args.previous.resolve())
    else:
        run(args.root.resolve())


if __name__ == "__main__":
    main()
