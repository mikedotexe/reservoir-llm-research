// swift-tools-version: 5.9
import PackageDescription
import Foundation

let stagedRoot = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
    .deletingLastPathComponent().deletingLastPathComponent()
precondition(FileManager.default.fileExists(atPath: stagedRoot.appendingPathComponent("staged-inputs.json").path),
             "Stage this research package first with stage-sources.sh; open staged-repo/native/ReservoirScope in SwiftPM or Xcode.")

let package = Package(
    name: "ReservoirScope",
    platforms: [.macOS(.v14)],
    products: [.executable(name: "ReservoirScope", targets: ["ReservoirScope"])],
    dependencies: [.package(path: "../../essentials")],
    targets: [.executableTarget(name: "ReservoirScope",
        dependencies: [.product(name: "EssentialsCore", package: "essentials")],
        resources: [.copy("Resources")])]
)
