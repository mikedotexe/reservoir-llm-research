import Foundation

struct FixtureInput: Decodable { let cases: [CaseInput] }
struct CaseInput: Decodable {
    let name: String
    let activations: [Double]
    let mean: [Double]
    let components: [[Double]]
    let selections: [[Int]]
}
struct SelectionOutput: Encodable {
    let selectedModes: [Int]
    let reconstruction: [Double]
    let residual: [Double]
    let reconstructedEnergy: Double
    let residualEnergy: Double
    let reconstructionOutOfRangeCount: Int
    let residualOutOfRangeCount: Int
}
struct FieldOutput: Encodable {
    let magnitude: [Double]
    let deviation: [Double]
    let magnitudeOutOfRangeCount: Int
    let deviationOutOfRangeCount: Int
    let scores: [Double]
    let centeredEnergy: Double
    let selections: [SelectionOutput]
}
struct CaseOutput: Encodable {
    let name: String
    let activations: [Double]
    let mean: [Double]
    let components: [[Double]]
    let selections: [[Int]]
    let expected: FieldOutput
}
struct Output: Encodable { let cases: [CaseOutput] }
@main struct StateFieldsOracle {
    static func main() throws {
        let input = try JSONDecoder().decode(FixtureInput.self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1])))
        let cases = try input.cases.map { c in
            let magnitude = try StateSurfaceMath.field(.magnitude, activations: c.activations)
            let deviation = try StateSurfaceMath.field(.referenceDeviation, activations: c.activations, mean: c.mean)
            let selections = try c.selections.map { modes in
                let reconstruction = try StateSurfaceMath.field(.reconstruction, activations: c.activations, mean: c.mean, components: c.components, selectedModes: modes)
                let residual = try StateSurfaceMath.field(.residual, activations: c.activations, mean: c.mean, components: c.components, selectedModes: modes)
                return SelectionOutput(selectedModes: reconstruction.selectedModes,
                    reconstruction: reconstruction.values, residual: residual.values,
                    reconstructedEnergy: reconstruction.reconstructedEnergy!, residualEnergy: reconstruction.residualEnergy!,
                    reconstructionOutOfRangeCount: reconstruction.outOfRangeCount, residualOutOfRangeCount: residual.outOfRangeCount)
            }
            let base = try StateSurfaceMath.field(.referenceDeviation, activations: c.activations, mean: c.mean, components: c.components, selectedModes: [])
            return CaseOutput(name: c.name, activations: c.activations, mean: c.mean, components: c.components, selections: c.selections,
                expected: FieldOutput(magnitude: magnitude.values, deviation: deviation.values,
                    magnitudeOutOfRangeCount: magnitude.outOfRangeCount, deviationOutOfRangeCount: deviation.outOfRangeCount,
                    scores: base.scores, centeredEnergy: base.centeredEnergy!, selections: selections))
        }
        let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
        FileHandle.standardOutput.write(try encoder.encode(Output(cases: cases)))
    }
}
