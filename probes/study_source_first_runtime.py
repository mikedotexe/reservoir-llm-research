"""Serial isolated runtime for source-first dependency plans.

Retains the qualified evidence-order generation core verbatim. The changes are
explicit plan/input preparation, per-trial prompt receipts, and source identities.
One model instance; fresh cache/RNG per trial; loopback readiness GET only.
No live generation POST, model/state checkin, generated command execution or installs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import resource
import socket
import sys
import threading
import time


_helper_path = Path(__file__).with_name("study_evidence_order.py")
_helper_spec = importlib.util.spec_from_file_location("qualified_order_runtime", _helper_path)
_helper = importlib.util.module_from_spec(_helper_spec)
_helper_spec.loader.exec_module(_helper)
digest, save, cache_positions = _helper.digest, _helper.save, _helper.cache_positions


def run_plan(root, prepare_trial):
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
    local_sources = [Path(__file__).resolve(), Path(__file__).with_name("study_source_first.py"), Path(__file__).with_name("study_source_first_review.py"), Path(__file__).with_name("study_evidence_order.py"), *[Path(protocol["runtime"])/name for name in ("generation_controls.py", "coupled_astrid_server.py", "real_model_coupling_study.py")]]
    local_sources.extend(Path(importlib.import_module(name).__file__) for name in ("mlx_lm.generate", "mlx_lm.sample_utils", "mlx_lm.models.gemma4_text", "mlx_lm.models.cache"))
    manifest = dict(protocol_sha256=digest(root/"protocol.json"), assets={name:digest(model_path/name) for name in names},
                    sources={str(path):digest(path) for path in local_sources}, versions={name:importlib.metadata.version(name) for name in ("mlx", "mlx-lm", "numpy", "transformers", "tokenizers")},
                    frozen_files={str(path):digest(path) for path in [root/"protocol.json", root/"criteria.json", root/"system.txt", *sorted(root.glob("block-*.txt"))]}, source_snapshots={str(path):digest(path) for path in sorted((root/"source-snapshot").iterdir())})
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
        prepared = prepare_trial(root, protocol, spec)
        if "outcome" in prepared:
            save(output, dict(spec=spec, **prepared), immutable=True)
            print(json.dumps(dict(stage="cell_dependency_unavailable", id=spec["id"], reason=prepared["reason"])), flush=True)
            continue
        messages = prepared["messages"]
        print(json.dumps(dict(stage="cell_admission", id=spec["id"])), flush=True)
        admitted = time.monotonic()
        try:
            wait_for_capacity()
        except Exception as error:
            save(output, dict(spec=spec, outcome="admission_unavailable", error=str(error), result=None, seconds=time.monotonic()-admitted), immutable=True)
            continue
        admission_seconds = time.monotonic()-admitted
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        prompt = tokenizer.encode(text)
        prompt_record = dict(arm=spec["arm"], id=spec["id"], rendered_text=text, token_ids=prompt,
                             token_count=len(prompt), rendered_sha256=hashlib.sha256(text.encode()).hexdigest())
        prompt_path = root / f"rendered-{spec['id']}.json"
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
