import Foundation

// SwiftPM generates Bundle.module. The standalone app build places its evidence
// directly in Contents/Resources and uses the ordinary macOS bundle instead.
#if !SWIFT_PACKAGE
extension Bundle {
    static var module: Bundle { .main }
}
#endif
