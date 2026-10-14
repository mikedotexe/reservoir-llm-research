// Development-only oracle, linked to the unchanged EssentialsCore. No model or
// source data access. Writes a JSON fixture to stdout; redirect to a NEW file.
import EssentialsCore
import Foundation

let texts = [
    "", "\n  ",
    "I wonder how this warm field changes. Perhaps we can explore it together?",
    "ABC 123 $ + < = > ^ ` | ~ ! \" # % & ' ( ) * , - . / : ; ? @ [ \\ ] _ { }",
    "One. Two!?  Three... Four....",
    "- first\n  * second\nplain line\n\nlast paragraph",
    "a\r\nb\r\nc", "A\tb\u{000B}C\u{000C}d\rE\nf",
    "we don't know; perhaps my questions won't change your mind.",
    "\"quote\"\n\n\n\nI notice pressure before and after."
]
let vectors = texts.map { ["text": $0, "features": TextCodec.encode($0)] as [String: Any] }
let fixture: [String: Any] = [
    "schema": "reservoir-ascii-codec-vectors-v1",
    "source": "essentials/spectral_bridge/TextCodec.swift",
    "scope": "ASCII codec oracle; Unicode conformance remains incomplete",
    "vectors": vectors
]
FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject: fixture, options: [.sortedKeys, .prettyPrinted]))
FileHandle.standardOutput.write(Data("\n".utf8))
