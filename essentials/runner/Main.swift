import Foundation
import Dispatch
import Darwin
import EssentialsCore

@main
struct EssentialsRunner {
    static func main() async {
        do {
            let args = Array(CommandLine.arguments.dropFirst())
            if args == ["--help"] || args.isEmpty {
                print("essentials-run run --config SPEC.json --output RUN.json\nessentials-run actions --config SPEC.json --output RUN.json\nessentials-run verify RUN.json")
                return
            }
            if args.count == 2 && args[0] == "verify" {
                let url = URL(fileURLWithPath: args[1])
                let size = try url.resourceValues(forKeys: [.fileSizeKey, .isRegularFileKey])
                guard size.isRegularFile == true, (size.fileSize ?? Int.max) <= 256 * 1_024 * 1_024 else {
                    throw EssentialsError.invalid("Run must be a regular JSON file no larger than 256 MB.")
                }
                struct FormatProbe: Decodable { let format: String? }
                let probe = try JSONDecoder().decode(FormatProbe.self, from: Data(contentsOf: url))
                if probe.format == ActionComparisonRecord.currentFormat {
                    let run = try ActionComparisonRecord.read(from: url)
                    _ = try run.verify()
                    print("Verified \(run.stepCount) action steps per arm, journal receipts, prompts, reply tape and applied feedback.")
                } else if probe.format == ExplorationRecord.currentFormat {
                    let run = try ExplorationRecord.read(from: url)
                    let report = try run.verify()
                    print("Verified \(report.checkedSteps) exploration steps, including applied controls, input, recurrent drive and exact states.")
                } else if probe.format == nil {
                    let run = try RunRecord.read(from: url)
                    print(try RunVerifier.verify(run).summary)
                } else {
                    throw EssentialsError.invalid("Unsupported run format: \(probe.format!).")
                }
                return
            }
            guard args.count == 5 && ["run", "actions"].contains(args[0]) else {
                throw EssentialsError.invalid("Use run or actions --config SPEC.json --output RUN.json, or verify RUN.json.")
            }
            var options: [String: String] = [:]
            for index in stride(from: 1, to: args.count, by: 2) {
                guard ["--config", "--output"].contains(args[index]), options[args[index]] == nil else {
                    throw EssentialsError.invalid("Unknown or duplicate command option.")
                }
                options[args[index]] = args[index + 1]
            }
            guard let config = options["--config"], let output = options["--output"] else {
                throw EssentialsError.invalid("Both --config and --output are required.")
            }
            let configURL = URL(fileURLWithPath: config), outputURL = URL(fileURLWithPath: output)
            guard configURL.standardizedFileURL != outputURL.standardizedFileURL else {
                throw EssentialsError.invalid("Output must be a separate file from the recipe.")
            }
            let size = try configURL.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? Int.max
            guard size <= 1_048_576 else { throw EssentialsError.invalid("Recipe exceeds 1 MB.") }
            let configData = try Data(contentsOf: configURL)
            if args[0] == "actions" {
                let spec = try JSONDecoder().decode(ActionComparisonSpecification.self, from: configData)
                try spec.validate()
                let journalDirectory = outputURL.deletingPathExtension().appendingPathExtension("journals")
                let store = try LocalActionJournalStore(directory: journalDirectory)
                let session = try ActionComparisonSession(specification: spec, journalStore: store)
                signal(SIGINT, SIG_IGN)
                let interrupt = DispatchSource.makeSignalSource(signal: SIGINT, queue: .global())
                interrupt.setEventHandler { Task { await session.stop() } }
                interrupt.activate()
                defer { interrupt.cancel() }
                let run = try await session.run()
                _ = try run.verify()
                try run.write(to: outputURL)
                print("\(run.status.rawValue.capitalized): \(run.stepCount) action steps per arm, \(run.right.actions.count) selected-arm actions. Saved \(outputURL.path)")
                if run.status == .failed {
                    FileHandle.standardError.write(Data((run.failure ?? "Action run failed.").utf8))
                    exit(1)
                }
                if run.status == .stopped { exit(130) }
                return
            }
            let spec = try JSONDecoder().decode(RunSpecification.self, from: configData)
            try spec.validate()
            let session = EssentialsSession()
            signal(SIGINT, SIG_IGN)
            let interrupt = DispatchSource.makeSignalSource(signal: SIGINT, queue: .global())
            interrupt.setEventHandler { Task { await session.stop() } }
            interrupt.activate()
            defer { interrupt.cancel() }
            let run = try await session.run(spec: spec)
            try RunVerifier.verify(run)
            try run.write(to: outputURL)
            print("\(run.status.rawValue.capitalized): \(run.frames.count) steps, \(run.turns.count) turns. Saved \(outputURL.path)")
            if run.status == .failed {
                FileHandle.standardError.write(Data((run.failure ?? "Language run failed.").utf8))
                exit(1)
            }
            if run.status == .stopped { exit(130) }
        } catch {
            FileHandle.standardError.write(Data("essentials-run: \(error.localizedDescription)\n".utf8))
            exit(1)
        }
    }
}
