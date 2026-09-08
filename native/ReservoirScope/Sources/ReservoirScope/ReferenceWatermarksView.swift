import SwiftUI

/// Source-clock range generations overlap at half-life. Measured radii never
/// drift inward: old geometry fades while a fresh measured range takes shape.
struct ReferenceWatermarksView: View {
    let ranges: [FillWatermarkMemoryRange]
    let sourceTime: Double
    let scope: String
    let reducedMotion: Bool
    private let highColor = Color(red: 1, green: 0.79, blue: 0.39)
    private let lowColor = Color(red: 0.48, green: 0.68, blue: 1)

    var body: some View {
        GeometryReader { geometry in
            let size = geometry.size
            let labelWidth = min(190.0, max(138.0, size.width * 0.22))
            let left = size.width - labelWidth - 16
            let highY = max(113.0, size.height * 0.28)
            let lowY = min(size.height - 58, max(highY + 122, size.height * 0.67))
            VStack(alignment: .leading, spacing: 4) {
                Text("RECENT FILL").font(.system(size: 10, weight: .semibold)).tracking(1.2)
                Text("30s ranges · 60s trails").font(.system(size: 10)).foregroundStyle(.white.opacity(0.7))
                Text(scope).font(.system(size: 9)).foregroundStyle(.secondary)
                    .lineLimit(1).minimumScaleFactor(0.8)
            }
            .frame(width: labelWidth, alignment: .leading)
            .position(x: left + labelWidth / 2, y: 32)
            ForEach(ranges, id: \.startTime) { range in
                let collecting = range.isCollecting(at: sourceTime)
                let opacity = range.opacity(at: sourceTime, reducedMotion: reducedMotion)
                if let high = range.snapshot.high {
                    measuredLine(high, color: highColor, opacity: opacity, collecting: collecting,
                        angle: 0.076, labelY: highY, left: left, size: size)
                }
                if let low = range.snapshot.low {
                    measuredLine(low, color: lowColor, opacity: opacity, collecting: collecting,
                        angle: -0.052, labelY: lowY, left: left, size: size)
                }
            }
            if let current = ranges.last {
                let previous = ranges.dropLast().last
                let collecting = current.isCollecting(at: sourceTime)
                if let high = current.snapshot.high {
                    label(high, previous: previous?.snapshot.high, title: "HIGH WATER", symbol: "arrow.up",
                        color: highColor, collecting: collecting, labelY: highY, left: left, width: labelWidth)
                }
                if let low = current.snapshot.low {
                    label(low, previous: previous?.snapshot.low, title: "LOW WATER", symbol: "arrow.down",
                        color: lowColor, collecting: collecting, labelY: lowY, left: left, width: labelWidth)
                }
            } else {
                Text("Waiting for\nrecent fill")
                    .font(.callout).foregroundStyle(.secondary)
                    .frame(width: labelWidth, alignment: .leading)
                    .position(x: left + labelWidth / 2, y: highY)
            }
        }
        .allowsHitTesting(false)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Recent fill ranges. \(scope). \(accessibleRange)")
        .help("Each pair gathers 30 seconds of measured fill and fades away over 60 seconds of source time. At half-life a new measured pair forms. Solid lines are forming; dashed lines are earlier ranges. At 20× the fade takes three viewing seconds. Pausing freezes source time. Reduce Motion uses static phase contrast with the same replacement and expiry.")
    }

    @ViewBuilder private func measuredLine(_ observation: FillWatermarkObservation, color: Color,
                                           opacity: Double, collecting: Bool, angle: Double,
                                           labelY: Double, left: Double, size: CGSize) -> some View {
        let inCrop = (ReferenceLens.lowerFillPct...ReferenceLens.upperFillPct).contains(observation.fillPct)
        let anchor = ReferenceLens.point(fillPct: observation.fillPct, angle: angle, width: size.width, height: size.height)
        if inCrop, anchor.x.isFinite, anchor.y.isFinite {
            ZStack {
                Path { path in
                    let span = collecting ? 0.023 : 0.034
                    for index in 0...32 {
                        let theta = angle - span + Double(index) / 32 * span * 2
                        let point = ReferenceLens.point(fillPct: observation.fillPct, angle: theta, width: size.width, height: size.height)
                        let position = CGPoint(x: point.x, y: point.y)
                        if index == 0 { path.move(to: position) } else { path.addLine(to: position) }
                    }
                }
                .stroke(color, style: StrokeStyle(lineWidth: collecting ? 2 : 1.5,
                    lineCap: .round, dash: collecting ? [] : [3, 3]))
                .shadow(color: color.opacity(collecting ? 0.45 : 0), radius: 5)
                Path { path in
                    path.move(to: CGPoint(x: anchor.x, y: anchor.y))
                    path.addLine(to: CGPoint(x: anchor.x + 13, y: anchor.y))
                    path.addLine(to: CGPoint(x: max(anchor.x + 13, left - 12), y: labelY))
                    path.addLine(to: CGPoint(x: left, y: labelY))
                }.stroke(color.opacity(0.7), style: StrokeStyle(lineWidth: 1, dash: collecting ? [3, 3] : [1, 5]))
                Circle().fill(color).frame(width: collecting ? 5 : 3, height: collecting ? 5 : 3)
                    .position(x: anchor.x, y: anchor.y)
            }.opacity(opacity)
        }
    }

    private func label(_ observation: FillWatermarkObservation, previous: FillWatermarkObservation?,
                       title: String, symbol: String, color: Color, collecting: Bool,
                       labelY: Double, left: Double, width: Double) -> some View {
        let inCrop = (ReferenceLens.lowerFillPct...ReferenceLens.upperFillPct).contains(observation.fillPct)
        return VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 3) {
                Image(systemName: symbol).font(.system(size: 8, weight: .bold))
                Text(title).font(.system(size: 9, weight: .semibold)).tracking(0.3)
                Spacer(minLength: 0)
                Text(collecting ? "FORMING" : "FADING").font(.system(size: 7, weight: .medium))
                    .foregroundStyle(.white.opacity(0.65))
            }
            Text(String(format: "%.2f%%", observation.fillPct))
                .font(.system(size: 25, weight: .light, design: .rounded)).monospacedDigit()
            Text(Self.sourceLabel(observation.sourceTime)).font(.system(size: 10)).monospacedDigit()
                .foregroundStyle(.white.opacity(0.65))
            if !inCrop { Text("Outside view").font(.system(size: 9)).foregroundStyle(.white.opacity(0.6)) }
            Text(previous.map { String(format: "Earlier %.2f%% · fading", $0.fillPct) }
                 ?? (collecting ? "Tracking this interval" : "Awaiting next reading"))
                .font(.system(size: 9)).monospacedDigit().foregroundStyle(.white.opacity(0.5))
                .frame(height: 12, alignment: .leading)
        }
        .foregroundStyle(color)
        .padding(10)
        .frame(width: width, alignment: .leading)
        .background(Color(red: 0.035, green: 0.045, blue: 0.065).opacity(0.9), in: RoundedRectangle(cornerRadius: 9))
        .overlay(RoundedRectangle(cornerRadius: 9).strokeBorder(color.opacity(collecting ? 0.3 : 0.15), lineWidth: 1))
        .position(x: left + width / 2, y: labelY)
    }

    private var accessibleRange: String {
        guard let current = ranges.last, let high = current.snapshot.high, let low = current.snapshot.low else {
            return "No recent measured observations."
        }
        let phase = current.isCollecting(at: sourceTime) ? "Forming" : "Fading"
        var result = String(format: "%@ range. High water %.2f percent at %@. Low water %.2f percent at %@. %d observations in this interval.",
            phase, high.fillPct, Self.sourceLabel(high.sourceTime), low.fillPct, Self.sourceLabel(low.sourceTime), current.snapshot.count)
        if let previous = ranges.dropLast().last, let high = previous.snapshot.high, let low = previous.snapshot.low {
            result += String(format: " Earlier fading range: high %.2f percent at %@, low %.2f percent at %@.",
                high.fillPct, Self.sourceLabel(high.sourceTime), low.fillPct, Self.sourceLabel(low.sourceTime))
        }
        return result
    }

    private static let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.timeZone = TimeZone(identifier: "America/Los_Angeles")
        formatter.dateFormat = "MMM d · HH:mm:ss 'PT'"
        return formatter
    }()
    private static func sourceLabel(_ time: Double) -> String { dateFormatter.string(from: Date(timeIntervalSince1970: time)) }
}
