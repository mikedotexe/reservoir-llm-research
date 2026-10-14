// Compiled alongside the actual unchanged native Evidence.swift. Bundle.module
// is only a stand-in for the SwiftPM generated accessor; the oracle passes URLs.
import Foundation
import CryptoKit
extension Bundle { static var module: Bundle { .main } }
func digest(_ values: [Double?]) -> String {
    var data = Data()
    for value in values {
        if let value {
            data.append(1)
            var bits = value.bitPattern.littleEndian
            withUnsafeBytes(of: &bits) { data.append(contentsOf: $0) }
        } else { data.append(0) }
    }
    return SHA256.hash(data:data).map { String(format:"%02x",$0) }.joined()
}
@main struct ObservatoryOracle {
    static func main() {
        do { try run() } catch {
            FileHandle.standardError.write(Data(("Native evidence rejected: \(error)\n").utf8))
            exit(1)
        }
    }
    static func run() throws {
        guard CommandLine.arguments.count == 2 else { throw NSError(domain:"usage",code:1) }
        let root=URL(fileURLWithPath:CommandLine.arguments[1])
        let store=try EvidenceStore.load(historicalURL:root.appendingPathComponent("data.json"),geometryURL:root.appendingPathComponent("state-geometry.json"))
        guard let states=store.stateReplay else { throw NSError(domain:"missing states",code:2) }
        let h=store.historical
        let history:[Double?]=h.samples.flatMap { x in [x.tS,x.fillPct,x.cascade[0],x.cascade[1],x.cascade[2],x.fillRatePctPerS,x.esnCovLambda1,x.geomRadius,x.geomRel,x.esnLeak,x.esnLambda] }
        let activations:[Double?]=states.frames.flatMap { $0.activations.map(Optional.some) }
        let geometry:[Double?]=states.frames.flatMap { frame in
            let x=frame.geometry
            return [x.pc[0],x.pc[1],x.pc[2],x.stateRms,x.centeredRms,x.projectedRms,x.reconstructionRmse,x.centeredNorm,x.projectedNorm,x.residualNorm].map(Optional.some)
        }
        let b=h.bands
        let bands:[Double?]=[b.shelfMinPct,b.shelfEntryPct,b.targetPct,b.shelfMaxPct,b.elevatedReleasePct,b.strongRailPct,b.forceRailPct]
        let identities:[[String:Any]]=h.samples.map { x in
            let ids:Any=x.sourceIds.map { ids in ids.map { id -> Any in id.map { String($0) } ?? NSNull() as Any } } ?? NSNull() as Any
            return ["utc":x.tUtc,"session":String(x.sessionId),"sourceIds":ids]
        }
        let result:[String:Any]=["historyCount":h.samples.count,"stateRows":states.frames.count,"dimensions":states.dimensions,
            "historyNumericSHA256":digest(history),"stateNumericSHA256":digest(activations),"geometryNumericSHA256":digest(geometry),"bandsNumericSHA256":digest(bands),
            "historyIdentities":identities,"sourceSHA256":states.sourceSHA256,"geometrySHA256":states.geometrySHA256,"capturedAtUtc":states.capturedAtUtc ?? NSNull() as Any]
        FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys]))
    }
}
