import Foundation

@main
enum GeometryBookmarkChecks {
    typealias Object = [String: Any]

    static func json(_ object: Any) -> String {
        String(data: try! JSONSerialization.data(withJSONObject: object, options: [.sortedKeys]), encoding: .utf8)!
    }
    static func object(_ text: String) -> Object {
        try! JSONSerialization.jsonObject(with: Data(text.utf8)) as! Object
    }
    static func editEntry(_ body: inout Object, _ index: Int, _ change: (inout Object) -> Void) {
        var history = body["history"] as! Object
        var records = history["records"] as! [Object]
        var entry = object(records[index]["body_json"] as! String)
        change(&entry)
        records[index]["body_json"] = json(entry)
        history["records"] = records; body["history"] = history
    }
    static func editSnapshot(_ body: inout Object, _ index: Int = 0, _ change: (inout Object) -> Void) {
        editEntry(&body, index) { entry in
            var snapshot = entry["snapshot"] as! Object
            change(&snapshot); entry["snapshot"] = snapshot
        }
    }
    static func editFrames(_ body: inout Object, _ change: (inout [Object]) -> Void) {
        editSnapshot(&body) { snapshot in
            var frames = snapshot["frames"] as! [Object]
            change(&frames); snapshot["frames"] = frames
        }
    }

    /// Rebuild every dependent reference as well as the chain, so semantic failures
    /// cannot pass merely because their original capture or prediction ID changed.
    static func seal(_ original: Object) -> Data {
        var body = original
        var history = body["history"] as! Object
        var records = history["records"] as! [Object]
        var replacements: [String: String] = [:]
        var previous = "empty"
        for index in records.indices {
            let oldID = records[index]["id"] as! String
            var entry = object(records[index]["body_json"] as! String)
            for field in ["baseline", "prediction", "observation", "target"] {
                if let old = entry[field] as? String, let replacement = replacements[old] {
                    entry[field] = replacement
                }
            }
            records[index]["body_json"] = json(entry)
            records[index]["previous"] = previous
            let record = records[index]
            let id = geometryHash([previous, geometryHash(record["request_id"] as! String),
                                   record["request_sha256"] as! String, geometryHash(record["body_json"] as! String)].joined(separator: "\n"))
            records[index]["id"] = id; replacements[oldID] = id; previous = id
        }
        history["records"] = records; body["history"] = history
        let text = json(body)
        return Data(json(["format": "question-geometry-v1", "body_json": text, "body_sha256": geometryHash(text)]).utf8)
    }

    static func main() throws {
        guard CommandLine.arguments.count == 3 else { fatalError("Pass the two synthetic fixture exports") }
        var checks = 0
        func check(_ value: Bool, _ name: String) throws {
            guard value else { throw GeometryBookmarkError.invalid("Check failed: \(name)") }
            checks += 1
        }
        func rejects(_ data: Data, _ expected: String) throws {
            do {
                _ = try GeometryBookmarkPacket.decode(data)
                throw GeometryBookmarkError.invalid("Accepted malformed fixture; expected: \(expected)")
            } catch {
                try check(error.localizedDescription == expected,
                          "Expected '\(expected)', got '\(error.localizedDescription)'")
            }
        }
        for path in CommandLine.arguments.dropFirst() {
            let data = try Data(contentsOf: URL(fileURLWithPath: path))
            let packet = try GeometryBookmarkPacket.decode(data)
            try check(packet.records.count == 5, "Five synthetic records decoded")
            try check(packet.records[0].snapshot?.gaps.count == 1, "Recorder gaps survive export")
            try check(packet.records[3].thresholdMet == false && abs(packet.records[3].rmsDistance! - 0.1) < 1e-12, "Comparison independently recomputed")
            try check(packet.records[4].text?.hasPrefix("Synthetic revision:") == true, "Authored revision preserved")
            for index in [0, 1, 4] {
                let entry = packet.records[index]
                let text = index == 0 ? entry.note : index == 1 ? entry.expectation : entry.text
                try check(entry.authoredText == text, "Authored account follows record kind")
            }
            try check(packet.records[3].authoredText == nil, "Comparison has no invented authored account")
            var envelope = object(String(data: data, encoding: .utf8)!)
            let original = object(envelope["body_json"] as! String)
            envelope["body_json"] = (envelope["body_json"] as! String) + " "
            try rejects(Data(json(envelope).utf8), "Unsupported packet or changed body bytes")
            var valid = original
            editEntry(&valid, 0) { $0["note"] = "Synthetic resealed control: all dependent references must still resolve." }
            let control = try GeometryBookmarkPacket.decode(seal(valid))
            try check(control.records.count == 5 && control.records[3].thresholdMet == false,
                      "Changed capture body and resealed dependent references remain valid")
            try check(control.body.history.records[0].id != packet.body.history.records[0].id,
                      "Valid control actually changes capture identity")

            func mutation(_ expected: String, _ change: (inout Object) -> Void) throws {
                var body = original; change(&body)
                try rejects(seal(body), expected)
            }
            try mutation("Question owner mismatch") { body in
                var history = body["history"] as! Object; history["owner"] = "wrong-owner"; body["history"] = history
            }
            try mutation("Broken geometry chain or conflicting operation identity") { body in
                var history = body["history"] as! Object; var records = history["records"] as! [Object]
                records[1]["request_id"] = records[0]["request_id"]; history["records"] = records; body["history"] = history
            }
            for (field, value) in [("scope", "recurrent_matrix_eigenvectors"), ("source", "/private/secret"),
                                   ("identity", "known-layout"), ("source_sha256", "invalid")] {
                try mutation("Unsupported source identity") { editSnapshot(&$0) { $0[field] = value } }
            }
            try mutation("Invalid interval limits") { editSnapshot(&$0) { $0["frames"] = [Object]() } }
            try mutation("Invalid interval limits") { editSnapshot(&$0) { $0["requested_seconds"] = 0 } }
            try mutation("Invalid activation vector") { editFrames(&$0) { $0[0]["activations"] = Array(repeating: 0, count: 127) } }
            try mutation("Invalid activation vector") { editFrames(&$0) { $0[0]["activations"] = Array(repeating: 2, count: 128) } }
            try mutation("Duplicate or reversed recorder clock") { editFrames(&$0) { $0[1]["t_ms"] = $0[0]["t_ms"] } }
            try mutation("Duplicate or reversed recorder clock") { editFrames(&$0) { $0[1]["wall_clock_unix_ms"] = $0[0]["wall_clock_unix_ms"] } }
            try mutation("Invalid capture clock or interval") { editSnapshot(&$0) { $0["requested_seconds"] = 1 } }
            try mutation("Invalid capture clock or interval") { editSnapshot(&$0) { $0["captured_at_unix_ms"] = 0 } }
            try mutation("Invalid prediction bound") { editEntry(&$0, 1) { $0["maximum_rms_distance"] = 3 } }
            try mutation("Prediction has no earlier baseline or authored expectation") { editEntry(&$0, 1) { $0["baseline"] = "unavailable" } }
            try mutation("Invalid authored text length") { editEntry(&$0, 1) { $0["expectation"] = "  " } }
            try mutation("Invalid authored text length") { editEntry(&$0, 0) { $0["note"] = String(repeating: "x", count: 2001) } }
            try mutation("Insufficient observations") { editFrames(&$0) { $0 = [$0.last!] } }
            try mutation("Overlapping intervals or recorder restart") { body in
                let history = body["history"] as! Object; let records = history["records"] as! [Object]
                let snapshot = object(records[0]["body_json"] as! String)["snapshot"]!
                editEntry(&body, 2) { $0["snapshot"] = snapshot }
            }
            for (field, value) in [("rms_distance", 0.0 as Any), ("threshold_met", true as Any), ("recipe", "unverified" as Any)] {
                try mutation("Comparison does not match its frozen vectors") { editEntry(&$0, 3) { $0[field] = value } }
            }
            try mutation("Revision needs an earlier record and authored text") { editEntry(&$0, 4) { $0["target"] = "unavailable" } }
            try mutation("Invalid authored text length") { editEntry(&$0, 4) { $0["text"] = "" } }
            for (index, field) in [(0, "text"), (1, "note"), (3, "note"), (4, "note"), (4, "future_field")] {
                let kind = packet.records[index].kind
                try mutation("Unexpected fields for \(kind): \(field)") { editEntry(&$0, index) { $0[field] = "Unvalidated extra account" } }
            }
            for index in [1, 3, 4] {
                try mutation("Unexpected fields for \(packet.records[index].kind): snapshot") { body in
                    let history = body["history"] as! Object; let records = history["records"] as! [Object]
                    var snapshot = object(records[0]["body_json"] as! String)["snapshot"] as! Object
                    snapshot["frames"] = [Object]()
                    editEntry(&body, index) { $0["snapshot"] = snapshot }
                }
            }
            try mutation("Unsupported geometry record kind") { editEntry(&$0, 4) { $0["kind"] = "unknown" } }
            var matched = original
            editEntry(&matched, 1) { $0["maximum_rms_distance"] = 0.2 }
            editEntry(&matched, 3) { $0["threshold_met"] = true }
            try check(try GeometryBookmarkPacket.decode(seal(matched)).records[3].thresholdMet == true,
                      "Valid threshold-met comparison remains supported")
            var empty = original
            empty["history"] = ["records": [Object]()] as Object
            try check(try GeometryBookmarkPacket.decode(seal(empty)).records.isEmpty, "Empty history supported")
        }
        try rejects(Data(), "Packet must be at most 4 MiB")
        try rejects(Data(repeating: 32, count: 4 * 1024 * 1024 + 1), "Packet must be at most 4 MiB")
        print("Geometry bookmark checks: \(checks) passed (synthetic fixtures; no producer-authenticity claim)")
    }
}
