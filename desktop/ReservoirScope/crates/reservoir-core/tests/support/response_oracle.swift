// Compiles against unchanged native readers. Bundle.module stands in only for
// SwiftPM's generated accessor; all evidence enters through explicit bytes.
import Foundation
import CryptoKit
extension Bundle { static var module: Bundle { .main } }
struct NumericDigest {
    var bytes = Data()
    mutating func scalar(_ value: Double?) {
        guard let value else { bytes.append(0); return }
        bytes.append(1); var bits = value.bitPattern.littleEndian
        withUnsafeBytes(of:&bits) { bytes.append(contentsOf:$0) }
    }
    mutating func array(_ values: [Double]?) {
        guard let values else { bytes.append(0); return }
        bytes.append(1); var count = UInt64(values.count).littleEndian
        withUnsafeBytes(of:&count) { bytes.append(contentsOf:$0) }
        for value in values { var bits=value.bitPattern.littleEndian; withUnsafeBytes(of:&bits) { bytes.append(contentsOf:$0) } }
    }
    var hash:String { SHA256.hash(data:bytes).map { String(format:"%02x",$0) }.joined() }
}
func nullable<T>(_ value:T?) -> Any { value.map { $0 as Any } ?? NSNull() }
@main struct ResponseOracle {
    static func main() {
        do { try run() } catch { FileHandle.standardError.write(Data(("Native response rejected: \(error)\n").utf8)); exit(1) }
    }
    static func run() throws {
        let args=CommandLine.arguments
        guard args.count>=3 else { throw NSError(domain:"usage",code:1) }
        let bytes=try Data(contentsOf:URL(fileURLWithPath:args[2]))
        let result:[String:Any]
        if args[1]=="native" {
            let e=try NativeActionResponse.decode(data:bytes)
            if args.count>3 { try e.validateReplacement(of:NativeActionResponse.decode(data:Data(contentsOf:URL(fileURLWithPath:args[3])))) }
            let receipts:[[String:Any]]=e.receipts.map { r in
                var d=NumericDigest()
                d.array(r.direction.map(Double.init)); d.array(r.before?.map(Double.init)); d.array(r.after?.map(Double.init)); d.array(r.delta?.map(Double.init)); d.array(r.realizedNoise?.map(Double.init))
                d.scalar(r.requestedAmount.map(Double.init)); d.scalar(r.attenuation.map(Double.init)); d.scalar(r.maxAbsDelta.map(Double.init)); d.scalar(r.effectiveLeak.map(Double.init)); d.scalar(r.actualL2)
                return ["status":r.status,"frameId":r.frameID,"successfulStepId":nullable(r.successfulStepId.map(String.init)),"observedAtUnixMs":String(r.observedAtUnixMs),"boundaryWaitUs":nullable(r.boundaryWaitUs.map(String.init)),"numericSha256":d.hash]
            }
            result=["kind":"native","fileSha256":e.fileSHA256,"receiptCount":e.receipts.count,"frameCount":e.frames.count,"boundaryCount":e.boundaries.count,"deltaScale":e.deltaScale,"receipts":receipts]
        } else if args[1]=="simulation" {
            let e=try StateResponseEvidence.decode(data:bytes,expectedSHA256:args.count>3 ? args[3] : StateResponseEvidence.retainedSHA256)
            let frames:[[String:Any]]=e.frames.map { f in
                var d=NumericDigest(); d.array(f.control); d.array(f.intervention); d.array(f.delta); d.scalar(f.separationL2)
                return ["index":f.sampleIndex,"position":String(f.originalBoundaryStep),"numericSha256":d.hash]
            }
            result=["kind":"simulation","fileSha256":SHA256.hash(data:bytes).map { String(format:"%02x",$0) }.joined(),"frameCount":e.frames.count,"nodeCount":e.nodeCount,"fixedDeltaScale":e.fixedDeltaScale,"returnBoundary":nullable(e.resultSummary.returnBoundary),"returnStatus":e.resultSummary.returnStatus,"peakGainOverInitial":e.resultSummary.peakGainOverInitial,"frames":frames]
        } else { throw NSError(domain:"mode",code:1) }
        FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys]))
    }
}
