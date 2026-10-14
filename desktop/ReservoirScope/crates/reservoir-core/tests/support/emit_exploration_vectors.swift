// Offline Swift oracle for the portable exploration verifier. No provider/live input.
// Compile against a freshly built EssentialsCore, then pass an owned output directory.
import Foundation
import EssentialsCore

guard CommandLine.arguments.count == 2 else {
    fatalError("usage: emit-exploration-vectors OUTPUT_DIRECTORY")
}
let directory = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
func save(_ name: String, _ engine: ExplorationEngine) throws {
    try engine.record.write(to: directory.appendingPathComponent(name + ".json"))
    print("\(name): \(engine.frames.count) steps; seed \(engine.seed)")
}

try save("empty-u64-max", ExplorationEngine(seed: UInt64.max))
var quiet = try ExplorationEngine()
for _ in 0..<8 { try quiet.advance(controls: ExplorationControls()) }
try save("quiet-defaults", quiet)

var forcing = try ExplorationEngine(seed: 99)
for step in 1...32 {
    let controls = ExplorationControls(repeatInput: true, inputStrength: step == 32 ? 0.25 : 1)
    try forcing.advance(controls: controls, pulse: step == 32)
}
try save("pulsed-forcing", forcing)

var transitions = try ExplorationEngine(seed: UInt64.max)
for step in 0..<18 {
    let controls = ExplorationControls(
        leak: step == 15 ? 0 : step == 16 ? 1 : step < 5 ? 0.3 : 0.7,
        recurrenceEnabled: step > 2, recurrenceStrength: step == 17 ? 0 : 0.6,
        repeatInput: step % 3 == 0, inputStrength: step == 17 ? 0 : 0.4,
        noiseAmplitude: step > 8 ? 0.04 : 0, biasEnabled: step == 4 || step == 16,
        sensoryEnabled: step % 4 != 0, retention: step == 14 ? 0.82 : step == 15 ? 0.995 : 0.92)
    try transitions.advance(controls: controls, pulse: step == 7 || step == 15)
}
try save("control-transitions-u64-max", transitions)

var field = try ExplorationEngine(seed: 9_007_199_254_740_993)
for step in 0..<6 {
    let controls = ExplorationControls(sensoryEnabled: step != 3, retention: 0.9)
    try field.advance(controls: controls, pulse: step == 1 || step == 2 || step == 4)
}
try save("sensory-restarts-u64-large", field)
