import Foundation
import MetalKit

@MainActor private func checkSharedCamera() throws {
    guard let device = MTLCreateSystemDefaultDevice() else { throw SurfaceRenderError("Metal unavailable") }
    let left = try StateSurfaceRenderer(device: device), right = try StateSurfaceRenderer(device: device)
    let independent = try StateSurfaceRenderer(device: device), camera = StateSurfaceCamera()
    var checks = 0
    func check(_ value: Bool, _ name: String) throws {
        guard value else { throw SurfaceRenderError("FAIL: " + name) }
        checks += 1; print("PASS \(checks): \(name)")
    }
    let original = independent.cameraPose
    left.orbit(dx: 8, dy: 5)
    left.useSharedCamera(camera); right.useSharedCamera(camera)
    try check(left.cameraPose == original && right.cameraPose == original,
              "Attaching two renderers starts from the same standard camera")
    left.orbit(dx: 12, dy: -7)
    try check(left.cameraPose == right.cameraPose && left.cameraPose != original,
              "Orbiting one surface updates both camera poses")
    try check(independent.cameraPose == original, "A baseline renderer outside the pair keeps its independent camera")
    right.zoom(delta: 25)
    try check(left.cameraPose == right.cameraPose && left.cameraPose.distance < original.distance,
              "Zooming the other surface updates both camera distances")
    right.useSharedCamera(nil)
    let detached = right.cameraPose
    left.orbit(dx: 15, dy: 5)
    try check(right.cameraPose == detached && left.cameraPose != detached,
              "Detaching a surface removes it from subsequent synchronized motion")
    right.useSharedCamera(camera)
    try check(right.cameraPose == left.cameraPose, "A reattached surface inherits the current shared pose")
    left.resetCamera()
    try check(left.cameraPose == original && right.cameraPose == original,
              "Reset from either view restores both standard poses")
    right.orbit(dx: 2, dy: 5); camera.reset()
    try check(left.cameraPose == original && right.cameraPose == original,
              "The workspace reset-view control restores both standard poses")
    independent.zoom(delta: -5)
    try check(independent.cameraPose != left.cameraPose && left.cameraPose == original,
              "Independent baseline motion cannot alter the pair")
    print("\(checks) shared-camera checks passed.")
}

Task { @MainActor in
    do { try checkSharedCamera(); exit(0) }
    catch { print(error.localizedDescription); exit(1) }
}
dispatchMain()
