// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "ReservoirScope",
    platforms: [.macOS(.v14)],
    products: [.executable(name: "ReservoirScope", targets: ["ReservoirScope"])],
    targets: [.executableTarget(name: "ReservoirScope", resources: [.copy("Resources")])]
)
