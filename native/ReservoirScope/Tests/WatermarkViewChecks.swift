// Staged with the exact production FillWatermarks, FillWatermarkMemory,
// ReferenceLens declaration, and ReferenceWatermarksView. Synthetic observations
// only: no window, live source, or system preference is touched.
import AppKit
import CoreGraphics
import SwiftUI

private struct WatermarkViewCheckFailure: LocalizedError {
    let message: String
    var errorDescription: String? { message }
}

@MainActor private struct WatermarkViewChecks {
    private var passed = 0
    private var artifacts: [[String: Any]] = []
    private var renderedImages = 0
    private let background = Color(red: 0.009, green: 0.017, blue: 0.031)

    private mutating func check(_ condition: Bool, _ description: String) throws {
        guard condition else { throw WatermarkViewCheckFailure(message: description) }
        passed += 1
        print("PASS \(passed): \(description)")
    }

    private mutating func render(ranges: [FillWatermarkMemoryRange], sourceTime: Double,
                        width: Int, height: Int, reducedMotion: Bool = false,
                        destination: URL) throws -> [UInt8] {
        let view = ReferenceWatermarksView(ranges: ranges, sourceTime: sourceTime,
            scope: "Recording · recent measured fill", reducedMotion: reducedMotion)
            .frame(width: CGFloat(width), height: CGFloat(height))
            .environment(\.colorScheme, .dark)
            .background(background)
        let renderer = ImageRenderer(content: view)
        renderer.scale = 1
        renderer.proposedSize = ProposedViewSize(width: CGFloat(width), height: CGFloat(height))
        guard let image = renderer.cgImage, image.width == width, image.height == height else {
            throw WatermarkViewCheckFailure(message: "SwiftUI did not produce the requested finite image dimensions")
        }
        let bitmap = NSBitmapImageRep(cgImage: image)
        guard let png = bitmap.representation(using: .png, properties: [:]) else {
            throw WatermarkViewCheckFailure(message: "Cannot encode offscreen watermark PNG")
        }
        try png.write(to: destination, options: .atomic)
        renderedImages += 1

        var pixels = [UInt8](repeating: 0, count: width * height * 4)
        let didDraw = pixels.withUnsafeMutableBytes { storage -> Bool in
            guard let colorSpace = CGColorSpace(name: CGColorSpace.sRGB),
                  let context = CGContext(data: storage.baseAddress, width: width, height: height,
                    bitsPerComponent: 8, bytesPerRow: width * 4, space: colorSpace,
                    bitmapInfo: CGBitmapInfo.byteOrder32Big.rawValue | CGImageAlphaInfo.premultipliedLast.rawValue)
            else { return false }
            context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
            return true
        }
        guard didDraw else { throw WatermarkViewCheckFailure(message: "Cannot inspect offscreen RGBA image") }
        return pixels
    }

    private func brightness(_ pixels: [UInt8]) -> UInt64 {
        var total: UInt64 = 0
        for offset in stride(from: 0, to: pixels.count, by: 4) {
            total += UInt64(pixels[offset])
            total += UInt64(pixels[offset + 1])
            total += UInt64(pixels[offset + 2])
        }
        return total
    }

    private func differentPixelCount(_ a: [UInt8], _ b: [UInt8]) -> Int {
        var count = 0
        for offset in stride(from: 0, to: min(a.count, b.count), by: 4) {
            if a[offset] != b[offset] || a[offset + 1] != b[offset + 1] || a[offset + 2] != b[offset + 2] {
                count += 1
            }
        }
        return count
    }

    private func coloredPixelCount(_ pixels: [UInt8], width: Int, height: Int,
                                   xRange: Range<Int>, yRange: Range<Int>) -> Int {
        var count = 0
        for y in yRange where y >= 0 && y < height {
            for x in xRange where x >= 0 && x < width {
                let offset = (y * width + x) * 4
                if Int(pixels[offset]) + Int(pixels[offset + 1]) + Int(pixels[offset + 2]) > 100 {
                    count += 1
                }
            }
        }
        return count
    }

    private func geometryDifference(_ a: [UInt8], _ b: [UInt8], width: Int, height: Int,
                                    labelLeft: Int) -> UInt64 {
        var difference: UInt64 = 0
        for y in 45..<(height - 20) {
            for x in 0..<max(0, labelLeft - 15) {
                let offset = (y * width + x) * 4
                for channel in 0..<3 {
                    difference += UInt64(abs(Int(a[offset + channel]) - Int(b[offset + channel])))
                }
            }
        }
        return difference
    }

    mutating func run(output: URL) throws {
        try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
        let origin = 1_788_829_432.0
        let observations = [(0.0, 65.0), (8, 73.58), (20, 59.26),
                            (30, 66), (37, 69.42), (44, 63.80)].enumerated().map {
            FillWatermarkObservation(fillPct: $0.element.1,
                sourceTime: origin + $0.element.0, ordinal: UInt64($0.offset))
        }
        let history = FillWatermarkMemoryHistory(observations: observations)
        var outsideMemory = FillWatermarkMemory()
        outsideMemory.observe(FillWatermarkObservation(fillPct: 95.04,
            sourceTime: origin, ordinal: 0), context: "outside-crop")
        outsideMemory.observe(FillWatermarkObservation(fillPct: 22.31,
            sourceTime: origin + 20, ordinal: 1), context: "outside-crop")
        var equalMemory = FillWatermarkMemory()
        equalMemory.observe(FillWatermarkObservation(fillPct: 65,
            sourceTime: origin, ordinal: 0), context: "equal")
        equalMemory.observe(FillWatermarkObservation(fillPct: 65,
            sourceTime: origin + 20, ordinal: 1), context: "equal")

        let forming = history.ranges(through: 2, at: origin + 20)
        let half = history.ranges(through: 3, at: origin + 30)
        let overlap = history.ranges(through: 5, at: origin + 45)
        let expiring = history.ranges(through: 5, at: origin + 59.9)
        let expired = history.ranges(through: 5, at: origin + 60)
        let empty = history.ranges(through: 5, at: origin + 90)
        try check(forming.count == 1 && forming[0].isCollecting(at: origin + 20),
            "The first rendered range is still collecting measured extrema")
        try check(half.count == 2 && half[0].opacity(at: origin + 30) == 0.5
            && half[1].isCollecting(at: origin + 30),
            "At the half-life, a fresh measured range coexists with the half-faded old range")
        try check(overlap.count == 2 && overlap[1].snapshot.high?.fillPct == 69.42
            && overlap[1].snapshot.low?.fillPct == 63.80,
            "The new pair forms from recent rise and fall without beating the previous range")
        try check(expired.count == 1 && expired[0].startTime == origin + 30,
            "The actual production model retires the old range at its exact sixty-second expiry")
        try check(empty.isEmpty,
            "A source gap retires all old ranges without inventing fresh observations")

        let cases: [(name: String, ranges: [FillWatermarkMemoryRange], age: Double, reducedMotion: Bool)] = [
            ("first-forming", forming, 20, false),
            ("half-life-new-forming", half, 30, false),
            ("overlap", overlap, 45, false),
            ("expiring", expiring, 59.9, false),
            ("expired-old", expired, 60, false),
            ("empty-gap", empty, 90, false),
            ("equal", equalMemory.ranges(at: origin + 20), 20, false),
            ("outside-crop", outsideMemory.ranges(at: origin + 20), 20, false),
            ("reduced-motion", overlap, 45, true),
            ("reduced-motion-expiry", expired, 60, true)
        ]
        for (width, height) in [(524, 300), (840, 469)] {
            let labelWidth = min(190.0, max(138.0, Double(width) * 0.22))
            let left = Int(Double(width) - labelWidth - 16)
            for fill in [0.0, 54, 65, 82, 100] {
                let point = ReferenceLens.point(fillPct: fill, angle: 0.076,
                    width: Double(width), height: Double(height))
                try check(point.x.isFinite && point.y.isFinite,
                    "\(width) × \(height): \(fill)% projects to finite lens coordinates")
            }
            var captured: [String: [UInt8]] = [:]
            for sample in cases {
                let stem = "\(width)x\(height)-\(sample.name)"
                let pixels = try render(ranges: sample.ranges, sourceTime: origin + sample.age,
                    width: width, height: height, reducedMotion: sample.reducedMotion,
                    destination: output.appendingPathComponent(stem + ".png"))
                captured[sample.name] = pixels
                try check(pixels.count == width * height * 4,
                    "\(stem): exact requested dimensions produce a complete RGBA image")
                try check(coloredPixelCount(pixels, width: width, height: height,
                    xRange: left..<width, yRange: 45..<(height - 20)) > 100,
                    "\(stem): the measured labels or empty-state explanation remain visible")
                let geometryPixels = coloredPixelCount(pixels, width: width, height: height,
                    xRange: 0..<max(0, left - 15), yRange: 45..<(height - 20))
                if sample.name == "outside-crop" || sample.name == "empty-gap" {
                    try check(geometryPixels == 0,
                        "\(stem): no false in-crop arcs or leaders appear without in-crop observations")
                } else {
                    try check(geometryPixels > 10,
                        "\(stem): measured range geometry renders separately from the label column")
                }
                artifacts.append(["case": sample.name, "width": width, "height": height,
                    "source_seconds_since_first_observation": sample.age,
                    "visible_ranges": sample.ranges.count, "reduced_motion": sample.reducedMotion,
                    "rgb_sum": brightness(pixels), "geometry_pixels_above_threshold": geometryPixels,
                    "png": stem + ".png"])
            }

            let current = [overlap[1]]
            let withoutOld45 = try render(ranges: current, sourceTime: origin + 45,
                width: width, height: height,
                destination: output.appendingPathComponent("\(width)x\(height)-overlap-current-only.png"))
            let withoutOld59 = try render(ranges: current, sourceTime: origin + 59.9,
                width: width, height: height,
                destination: output.appendingPathComponent("\(width)x\(height)-expiring-current-only.png"))
            let withoutOld60 = try render(ranges: current, sourceTime: origin + 60,
                width: width, height: height,
                destination: output.appendingPathComponent("\(width)x\(height)-expired-current-only.png"))
            let reducedMotionLate = try render(ranges: expiring, sourceTime: origin + 59.9,
                width: width, height: height, reducedMotion: true,
                destination: output.appendingPathComponent("\(width)x\(height)-reduced-motion-late.png"))
            let earlyDifference = geometryDifference(captured["overlap"]!, withoutOld45,
                width: width, height: height, labelLeft: left)
            let lateDifference = geometryDifference(captured["expiring"]!, withoutOld59,
                width: width, height: height, labelLeft: left)
            try check(earlyDifference > 100,
                "\(width) × \(height): the older range remains visibly distinct during overlap")
            try check(lateDifference < earlyDifference / 8,
                "\(width) × \(height): the older geometry fades toward zero without requiring a new record")
            try check(differentPixelCount(captured["expired-old"]!, withoutOld60) == 0,
                "\(width) × \(height): expiry leaves exactly the newer measured range")
            try check(differentPixelCount(captured["overlap"]!, captured["reduced-motion"]!) > 10,
                "\(width) × \(height): Reduce Motion has a separately rendered static age treatment")
            try check(differentPixelCount(captured["reduced-motion"]!, reducedMotionLate) == 0,
                "\(width) × \(height): Reduce Motion keeps identical geometry between phase boundaries")
            artifacts.append(["case": "aging-geometry-comparison", "width": width, "height": height,
                "older_geometry_rgb_difference_at_age_45": earlyDifference,
                "older_geometry_rgb_difference_at_age_59_9": lateDifference,
                "current_only_pngs": ["\(width)x\(height)-overlap-current-only.png",
                    "\(width)x\(height)-expiring-current-only.png",
                    "\(width)x\(height)-expired-current-only.png"],
                "reduced_motion_late_png": "\(width)x\(height)-reduced-motion-late.png"])
        }
        let receipt: [String: Any] = ["checks_passed": passed, "rendered_images": renderedImages,
            "scope": "Synthetic measured fill; exact production aging model, SwiftUI overlay and lens geometry; no Metal backdrop or app window",
            "artifacts": artifacts]
        let data = try JSONSerialization.data(withJSONObject: receipt, options: [.prettyPrinted, .sortedKeys])
        try data.write(to: output.appendingPathComponent("checks.json"), options: .atomic)
        print("\(passed) watermark view checks passed; \(renderedImages) finite offscreen PNGs saved to \(output.path).")
    }

}

do {
    guard CommandLine.arguments.count == 2 else {
        throw WatermarkViewCheckFailure(message: "Expected one output directory argument")
    }
    var checks = WatermarkViewChecks()
    try checks.run(output: URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true))
} catch {
    FileHandle.standardError.write(Data("FAIL: \(error.localizedDescription)\n".utf8))
    exit(1)
}
