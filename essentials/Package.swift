// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "Essentials",
    platforms: [.macOS(.v14)],
    products: [.library(name: "EssentialsCore", targets: ["EssentialsCore"]),
               .executable(name: "essentials-run", targets: ["EssentialsRunner"])],
    targets: [
        .target(name: "EssentialsCore", path: ".", exclude: ["README.md", "EXPLORE.md", "ACTIONS.md", "build.sh", "check.sh", "tests", "runner", "examples", "reservoir/README.md", "spectral_bridge/README.md", "regulation/README.md", "llm/README.md", "stages/README.md", "stages/ACTIONS-AND-COMPARISONS.md", "actions/recipes", "stages/01-reservoir.json", "stages/02-spectral-bridge.json", "stages/03-llm-loop.json", "stages/04-regulation.json", "stages/04-regulation-disabled.json"],
                sources: ["reservoir", "spectral_bridge", "regulation", "llm", "stages", "actions"],
                linkerSettings: [.linkedFramework("Accelerate")]),
        .executableTarget(name: "EssentialsRunner", dependencies: ["EssentialsCore"], path: "runner", exclude: ["README.md"]),
        .testTarget(name: "EssentialsTests", dependencies: ["EssentialsCore"], path: "tests", exclude: ["README.md", "runtime-validation.log", "http_smoke.py", "action_cli_smoke.py", "action_http_smoke.py", "__pycache__"])
    ]
)
