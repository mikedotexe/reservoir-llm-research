import SwiftUI

struct GuidedTraceSeries {
    let title: String
    let color: Color
    let values: [Double]
}

/// All series share the declared numeric scale. Callers supply only the prefix
/// visible at the recorded cursor, so drawing cannot reveal future measurements.
struct GuidedLineTrace: View {
    let title: String
    let series: [GuidedTraceSeries]
    let lower: Double
    let upper: Double
    var reference: Double? = nil
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(title).font(.caption.weight(.medium))
                Spacer()
                Text("\(format(lower))–\(format(upper))").font(.caption2.monospacedDigit()).foregroundStyle(.secondary)
            }
            Canvas { context, size in
                let count = max(2, series.map { $0.values.count }.max() ?? 0)
                func y(_ value: Double) -> Double { size.height * (1 - min(1, max(0, (value - lower) / (upper - lower)))) }
                if let reference {
                    var path = Path(); path.move(to: CGPoint(x: 0, y: y(reference))); path.addLine(to: CGPoint(x: size.width, y: y(reference)))
                    context.stroke(path, with: .color(.white.opacity(0.5)), style: StrokeStyle(lineWidth: 1, dash: [4, 3]))
                }
                for item in series {
                    var path = Path()
                    for (index, value) in item.values.enumerated() {
                        let point = CGPoint(x: size.width * Double(index) / Double(count - 1), y: y(value))
                        if index == 0 { path.move(to: point) } else { path.addLine(to: point) }
                    }
                    context.stroke(path, with: .color(item.color), lineWidth: 1.7)
                    if item.values.count == 1, let value = item.values.first {
                        context.fill(Path(ellipseIn: CGRect(x: 0, y: y(value) - 2, width: 4, height: 4)), with: .color(item.color))
                    }
                }
            }.background(.black.opacity(0.15))
            HStack(spacing: 16) {
                ForEach(Array(series.enumerated()), id: \.offset) { _, item in
                    Text(item.title + (item.values.last.map { " · " + format($0) } ?? " · unavailable"))
                        .font(.caption2.monospacedDigit()).foregroundStyle(item.color)
                }
                Spacer()
                if let reference { Text("Dashed: \(format(reference))").font(.caption2).foregroundStyle(.secondary) }
            }
        }.accessibilityElement(children: .combine)
            .accessibilityLabel(title + ". Shared scale \(format(lower)) to \(format(upper)). "
                + series.map { $0.title + " latest " + ($0.values.last.map(format) ?? "unavailable") }.joined(separator: ". "))
    }
    private func format(_ value: Double) -> String { String(format: "%.3g", value) }
}

struct GuidedSpectrum: View {
    let title: String
    let values: [Double]
    let upper: Double
    let color: Color
    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            Text(title).font(.caption.weight(.medium))
            Canvas { context, size in
                guard !values.isEmpty, upper > 0 else { return }
                let width = size.width / Double(values.count)
                for (index, value) in values.enumerated() {
                    let height = size.height * min(1, max(0, value / upper))
                    let rectangle = CGRect(x: Double(index) * width, y: size.height - height, width: max(1, width - 1), height: height)
                    context.fill(Path(rectangle), with: .color(color))
                }
            }.background(.black.opacity(0.15))
            Text("Modes 1–\(values.count) · shared scale 0–\(String(format: "%.4g", upper))")
                .font(.caption2.monospacedDigit()).foregroundStyle(.secondary)
        }.accessibilityElement(children: .combine)
            .accessibilityLabel(title + ", \(values.count) measured sensory eigenvalues. Leading mode " + String(format: "%.5g", values.first ?? 0))
    }
}
