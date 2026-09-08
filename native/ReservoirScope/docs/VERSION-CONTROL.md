# Initial viewer snapshot

Git tracking began on September 7, 2026 Pacific at Mike's request. Neither the
mounted research folder nor its canonical folder on `volya` had an existing Git
repository. The first commit therefore captures Reservoir Scope 0.7.1 build 10
as a complete viewer snapshot, not as a reconstructed patch against an invented
prior commit.

The snapshot includes the verified 20 Swift sources and six bundled resources,
the build and native check tools, viewer documentation, build receipts, final
0.7.1 validation, and the two saved visualization inputs required by the build.
Watermark-specific probes, implementation accounts and board receipts accompany
it. The 0.7.0 and 0.7.1 build receipts retain the prior and current source hashes:
only FillWatermarkMemory.swift, ReferenceWatermarksView.swift and
ReservoirScopeApp.swift differ in the production source set.

Shared research notes, other studies and proposals, preliminary renders, and
unrelated work remain outside this initial commit. They were neither deleted nor
claimed as this viewer change. Historical documentation links may refer to that
existing research workspace; the committed viewer does not package the entire
research archive. Compiled app bundles and local build caches are also excluded.

The native build uses the committed saved resources. It can optionally refresh
the native action example from a research output if that file exists. No live
producer or being system is changed by building or versioning this viewer.
