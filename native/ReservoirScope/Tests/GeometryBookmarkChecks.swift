import Foundation

@main
enum GeometryBookmarkChecks {
    static func main() throws {
        guard CommandLine.arguments.count == 3 else { fatalError("Pass the two synthetic Rust/adapter exports") }
        var checks = 0
        func check(_ value: Bool, _ name: String) throws {
            guard value else { throw GeometryBookmarkError.invalid("Check failed: \(name)") }
            checks += 1
        }
        func rejects(_ data: Data) -> Bool { (try? GeometryBookmarkPacket.decode(data)) == nil }
        for path in CommandLine.arguments.dropFirst() {
            let data = try Data(contentsOf: URL(fileURLWithPath: path))
            let packet = try GeometryBookmarkPacket.decode(data)
            try check(packet.records.count == 5, "Five real helper records decoded")
            try check(packet.records[0].snapshot?.gaps.count == 1, "Recorder gaps survive export")
            try check(packet.records[3].thresholdMet == false && abs(packet.records[3].rmsDistance! - 0.1) < 1e-12, "Swift recomputed Rust comparison")
            try check(packet.records[4].text?.hasPrefix("Synthetic revision:") == true, "Authored revision preserved")
            var envelope = try JSONSerialization.jsonObject(with: data) as! [String: Any]
            let originalBody = envelope["body_json"] as! String
            envelope["body_json"] = originalBody + " "
            try check(rejects(try JSONSerialization.data(withJSONObject: envelope)), "Changed packet hash rejected")
            var body = try JSONSerialization.jsonObject(with: Data(originalBody.utf8)) as! [String: Any]
            let original = body
            for mutation in 0..<7 {
                body = original
                var history = body["history"] as! [String: Any]
                var records = history["records"] as! [[String: Any]]
                if mutation == 0 { history["owner"] = "wrong-owner" }
                if mutation == 1 { records[0]["previous"] = "changed" }
                if mutation == 2 { records[1]["request_id"] = records[0]["request_id"] }
                if mutation >= 3 {
                    let index = mutation == 6 ? 3 : 0
                    var entry = try JSONSerialization.jsonObject(with: Data((records[index]["body_json"] as! String).utf8)) as! [String: Any]
                    if mutation == 6 { entry["rms_distance"] = 0.0 }
                    else {
                        var snapshot = entry["snapshot"] as! [String: Any]
                        if mutation == 3 { snapshot["scope"] = "recurrent_matrix_eigenvectors" }
                        if mutation == 4 { snapshot["frames"] = [] }
                        if mutation == 5 { snapshot["source"] = "/private/secret" }
                        entry["snapshot"] = snapshot
                    }
                    records[index]["body_json"] = String(data: try JSONSerialization.data(withJSONObject: entry, options: [.sortedKeys]), encoding: .utf8)!
                    // Re-seal the entire chain: semantic checks must reject even self-consistent forged packets.
                    var previous = "empty"
                    for i in records.indices {
                        records[i]["previous"] = previous
                        let record = records[i]
                        let id = geometryHash([previous, geometryHash(record["request_id"] as! String), record["request_sha256"] as! String, geometryHash(record["body_json"] as! String)].joined(separator: "\n"))
                        records[i]["id"] = id; previous = id
                    }
                }
                history["records"] = records; body["history"] = history
                let bodyString = String(data: try JSONSerialization.data(withJSONObject: body, options: [.sortedKeys]), encoding: .utf8)!
                envelope["body_json"] = bodyString; envelope["body_sha256"] = geometryHash(bodyString)
                try check(rejects(try JSONSerialization.data(withJSONObject: envelope)), "Malformed/resealed packet \(mutation) rejected")
            }
        }
        try check(rejects(Data()), "Empty input rejected")
        try check(rejects(Data(repeating: 32, count: 4 * 1024 * 1024 + 1)), "Oversized input rejected")
        print("Geometry bookmark checks: \(checks) passed")
    }
}
