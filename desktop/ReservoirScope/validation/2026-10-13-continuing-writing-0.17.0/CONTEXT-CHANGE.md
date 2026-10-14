# What v5 changes in the supplied context

V5 gives the continuing journal more prominence and reduces the numerical scaffold.
It does not shorten the previous entry or change the feedback mechanism. This is a
context-design change; synthetic qualification cannot establish a better voice,
attention, self-reflection or an emergent result.

There are two existing return paths. After a complete accepted entry is saved and
read back, deterministic textual features become a reduced numerical signal eligible
for application at the next step. The reservoir then continues with that held input,
forcing, noise and regulation. Separately, the **complete latest applied entry** is
read back and supplied as prose memory at the next writing opportunity. That full
text is not reconstructed from the reduced signal. It is one eligible entry, not
proof that the model received or understood the whole journal archive.

V4 supplies the full coordinate and sensory-eigenvalue arrays, eight current/prior
measurement rows, provenance IDs/hashes and a longer measurement-oriented scaffold,
with previous prose before the readout. V5 supplies a short open invitation, a brief
mechanism description, then only step/time, current/prior RMS and sensory fill with
signed differences, and coordinate L2 distance. The complete JSON-quoted prior entry
follows those readings, before a final open invitation. No subject, persona, feeling,
heading, length or reflective performance is assigned.

The complete observation and prior scalar snapshot remain retained unchanged. The
human reader still has the eight-row measurement reference, raw observation, exact
prompt and source/application evidence. Missing prior measurements stay unavailable;
they are not inferred from prose. A prior reached observation and the latest eligible
journal remain different identities when an opportunity failed or was skipped.

## Exact fixture byte comparison

The [script](measure_context_01.py) ran once and the [receipt](context-bytes-01.json)
passed. It compares two matched deterministic fixtures: seed `18446744073709551615`,
cadence 10, the first observation at step 10 and the later observation at step 20.
The latter follows an explicit preparation retry and application at step 11 of the
same supplied 89-byte text. The script checks common displayed readings and exact
previous text, rather than assuming they match.

“Scaffold” here means all prompt UTF-8 bytes except the prior-text JSON string literal
including its quotation marks. Its marker, provenance labels, section boundaries and
final invitation remain scaffold. These counts are not tokens.

| Fixture | V4 whole prompt | V5 whole prompt | V4 scaffold | V5 scaffold | Reduction |
| --- | ---: | ---: | ---: | ---: | ---: |
| First, step 10 | 4,445 bytes | 1,437 bytes | 4,445 bytes | 1,437 bytes | 3,008 bytes |
| With memory, step 20 | 4,829 bytes | 1,627 bytes | 4,738 bytes | 1,536 bytes | 3,202 bytes |

The later prior-text JSON literal is exactly 91 bytes in both versions and decodes
to the same 89 UTF-8 bytes. All four prompts have no trailing newline. Fixture hashes:

| Fixture | SHA-256 |
| --- | --- |
| v4 first | `26bae96991e12bb591ba517c46345aeac167abbbdaf79858c514a35b8986f75f` |
| v5 first | `5c9c1dbdb29e1058b59d23174cdab186c0aa60d76293f29bb99827b217025dd6` |
| v4 later | `d51753e1eddd68fd193ba46da49e6f909aaebdef328471ddf79e3b134b10c2c0` |
| v5 later | `a828b3390d049b22faf115f74644374f2c86f74a4ac47fd806a5e69920de99fd` |

The [v5 fixture provenance](../../crates/reservoir-core/tests/fixtures/sustained-prompts/v5-provenance.json)
records independent expected-byte assembly from the approved template and unchanged
v4 numerical references. Engine tests, production replay, physical save/readback and
native UI qualification are separate evidence. This small static comparison measures
neither actual provider tokenization nor context coverage, attention or writing quality.

Legacy v1–v4 prompts and exports remain historical contracts. Fresh v5 changes no
numeric codec, weights, RNG, cadence, generation limits, completeness condition,
save/readback rule, next-step timing or memory eligibility. Different writing can
still yield different feedback and later states; numerical equivalence requires
identical supplied replies. Real-model writing belongs to a separately bounded,
admitted episode, not to this synthetic package qualification.
