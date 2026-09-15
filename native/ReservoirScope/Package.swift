// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "ReservoirScope",
    platforms: [.macOS(.v14)],
    products: [.executable(name: "ReservoirScope", targets: ["ReservoirScope"])],
    dependencies: [.package(path: "../../essentials")],
    targets: [.executableTarget(name: "ReservoirScope",
        dependencies: [.product(name: "EssentialsCore", package: "essentials")],
        resources: [.copy("Resources")])]
)
