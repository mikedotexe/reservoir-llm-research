"""Generate NEW bounded Unicode codec fixtures from unchanged native Swift.
No provider, recordings or live sources. Requires macOS Swift; refuses overwrite.
The scalar alphabet and explicit non-composable clusters are a qualification
boundary, not a claim covering every Unicode version or arbitrary grapheme.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import random
import subprocess
import tempfile

RANGES = [(0, 0x7f), (0x80, 0x36f), (0x370, 0x52f), (0x590, 0x6ff),
          (0x900, 0x97f), (0x1e00, 0x1eff), (0x2000, 0x206f),
          (0x20a0, 0x20cf), (0x2150, 0x21ff), (0x2600, 0x27bf),
          (0x3000, 0x30ff), (0x3400, 0x4dbf), (0x4e00, 0x9fff),
          (0xac00, 0xd7a3), (0xfe00, 0xfe0f), (0xff00, 0xffef),
          (0x1f1e6, 0x1f1ff), (0x1f300, 0x1faff)]
CLUSTERS = ["\r\n", "i\u0307", "!\u0301", ".\u0301", "?\u0301", " \u0301",
            "a\u0301\u0308", "שָ", "مُ", "कि", "क्ष", "क्\u200dष",
            "👩🏽‍💻", "👨‍👩‍👧‍👦", "👍🏿", "❤️", "🏳️‍🌈", "🇺🇸", "🇯🇵", "1️⃣", "#️⃣"]
TEXTS = ["", " ", "\u200b", "\u200b\u0085\u00a0", "\u001c", "\u00ad",
 "é e\u0301 É E\u0301 à Å A\u030a", "İ I i ı i\u0307", "ΟΣ ΟΣΑ Σ σ ς",
 "I I\u0301 I\u0307 I\u0328", "Straße STRASSE ß ẞ ﬀ", "é e\u0301 é e\u0301",
 "Привет МИР Ёлка", "Ελληνικά ΑΒΓ Ωμέγα", "שלום שָ", "مرحبا مُ",
 "नमस्ते कि क्ष क्\u200dष", "中文 日本語 かな カナ", "한글 가 각 힣",
 "½ Ⅲ ² ١ ۲ ९ １２３", "“I wonder,” she said. ‘Perhaps?’ Don't don’t can't can’t.",
 "👩🏽‍💻 👨‍👩‍👧‍👦 👍🏿 ❤️ 🏳️‍🌈 🇺🇸🇯🇵 1️⃣ #️⃣",
 "- one\u0085\u00a0* two\u2028\u200b• three\u2029plain\n\nlast",
 "a...\u0301b .\u0301 ?\u0301 !\u0301", "- \u0301line\n* line\n• line", "a\r\nb\r\nc",
 "perhaps MAYBE must don't i YOU warm pressure wonder reflect now small",
 "e\u0301 e\u0301 é é", "a\u0301\u0308 a\u0308\u0301", "\t\v\f\r\n\u0085\u1680\u2000\u2028\u2029\u202f\u205f\u3000"]

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,required=True); args=p.parse_args()
 if args.output.exists(): p.error('output exists; generate a new evidence file')
 crate=Path(__file__).resolve().parents[2]; repo=crate.parents[3]
 source=repo/'essentials/spectral_bridge/TextCodec.swift'; emitter=Path(__file__).with_name('emit_unicode_codec.swift')
 # Seeded mixes cover scalar, grapheme, case, canonical equality and separator boundaries.
 alphabet=list("aAZ9 .!?\n\t'\"")+list("éÉΣςİЖя中日한글½Ⅲ١९“”•")+CLUSTERS
 rng=random.Random(20261012); texts=TEXTS+CLUSTERS+[f"a {c} Z! {c}" for c in CLUSTERS]
 texts += [''.join(rng.choice(alphabet) for _ in range(rng.randrange(1,50))) for _ in range(384)]
 # Each declared scalar is exercised in an independent native encoding chunk.
 # Separator prevents accidental multi-scalar clusters; corpus includes admitted
 # and deliberately unsupported text, classified by portable tests separately.
 scalars=[chr(c) for a,b in RANGES for c in range(a,b+1)]
 texts += [' | '.join(scalars[i:i+64]) for i in range(0,len(scalars),64)]
 request={'ranges':RANGES,'clusters':CLUSTERS,'texts':texts}
 with tempfile.TemporaryDirectory(prefix='reservoir-unicode-oracle-') as tmp:
  exe=Path(tmp)/'oracle'
  cmd=['swiftc','-O',str(source),str(emitter),'-o',str(exe)]
  subprocess.run(cmd,check=True,capture_output=True,text=True,timeout=120)
  result=subprocess.run([str(exe)],input=json.dumps(request),capture_output=True,text=True,check=True,timeout=120)
  value=json.loads(result.stdout)
  value.update(schema='reservoir-unicode-codec-oracle-v1',createdAtUTC=datetime.now(timezone.utc).isoformat(),
    host=platform.platform(),swiftVersion=subprocess.check_output(['swiftc','--version'],text=True).strip(),
    source={'path':str(source.relative_to(repo)),'sha256':digest(source)},
    emitter={'path':str(emitter.relative_to(repo)),'sha256':digest(emitter)},
    generator={'path':str(Path(__file__).resolve().relative_to(repo)),'sha256':digest(Path(__file__))},
    executableSha256=digest(exe),scalarRanges=RANGES,scalarCount=len(scalars),modelsContacted=False,
    scope='Bounded scalar alphabet, canonical-composable graphemes and listed multi-scalar clusters; independent native codec vectors; no universal Unicode/parser parity claim')
 args.output.parent.mkdir(parents=True,exist_ok=True)
 with args.output.open('x',encoding='utf-8') as f: json.dump(value,f,ensure_ascii=True,indent=2); f.write('\n')
 print(json.dumps({'output':str(args.output),'sha256':digest(args.output),'vectors':len(texts),'scalars':len(scalars),'propertyRanges':len(value['properties'])}))
if __name__=='__main__': main()
