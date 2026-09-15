# Read the state as a landscape

Reservoir Scope 0.10.0 adds **Surface / Topography** inside both Essentials views.
Topography is the default: positive values rise in cyan, negative values form
purple valleys, and a light contour marks the boundary where the interpolated
field crosses zero. Other contours are spaced by **0.2 activation units**.

**Height** changes the display exaggeration. Set it to zero to compare the contour
map on a smooth sphere, or select **Surface** to return to the original view.
Neither control changes the reservoir, its inputs, its recordings or replay time.
Node selection still shows the original exact coordinate value in the inspector.

## What the landscape represents

This is the topography of a projection of the state, not the reservoir's network
wiring or a physical shape. Each coordinate keeps its original fixed Fibonacci
location. A smooth weighted field fills the space between those sites. Therefore
adjacent patches and connected contours depend on this drawing map; they do not
establish neural connections, dynamical attractors, or fractal structure.

Color, height and contour positions use the same interpolated scalar field. Exact
node markers retain the original coordinate values. The smoothed field at a marker
can differ from that coordinate because neighboring coordinates contribute to the
interpolation. There is no synthetic noise, texture, animation or inserted detail.

At a unit direction p, the original map uses normalized spherical Gaussian weights:

    w_i(p) = exp(24 × (p · site_i − 1)) / Σ_j exp(24 × (p · site_j − 1))
    field(p) = Σ_i w_i(p) × state_i

For Essentials' fixed −1 to +1 scale, radial position is:

    radius(p) = 0.82 + Height × clamp(field(p), −1, +1)

Height defaults to 0.16 and ranges from 0 to 0.20. The neutral radius is fixed.
There is no normalization against the current minimum, maximum, mean or volume.
Consequently a uniform positive state expands the landscape, and a uniform negative
state contracts it. **Volume in Topography does not represent fill.** Experimental
fill, when available in Stage 4, remains a separate numerical measurement.

## How seams and contours are drawn

The old Essentials surface uses the renderer's full-size endpoint, which intentionally
disables its volume-preserving relief. Its patches therefore show mainly through
color. Its graticule rings are drawing references, not state boundaries.

Topography uses a denser closed mesh (64 latitude divisions, 128 longitude divisions)
with the same coordinate sites and Gaussian kernel. The field is evaluated at mesh
vertices, interpolated across each triangle, then converted to color in the fragment
shader. This preserves the scalar zero crossing before applying the two palette
branches. Surface normals supply slope lighting. The decorative graticule is removed.

Contour widths are antialiased using screen-space derivatives of the field. They
mark fixed activation levels rather than triangle edges. A constant field has no
isolated boundary and receives no contour wash. Resolution changes the smoothness
of this rendering, not the reservoir's number of coordinates.

The cut face is unmeasured and remains uniformly dark. It carries no contour field,
and picking does not pass through it to a hidden surface coordinate. Rotation,
selection and scrubbing work as before. Accepted observations are shown without
temporal easing, so returning to the same state and view settings reproduces the
same geometry and pixels.

## Implementation and checks

- [StateSurface.swift](../Sources/ReservoirScope/StateSurface.swift) defines the
  optional dense atlas and fixed signed radial map. The original default atlas
  and volume-preserving surface remain unchanged.
- [StateSurfaceScene.swift](../Sources/ReservoirScope/StateSurfaceScene.swift)
  selects the presentation, computes the scalar palette and contour lines on the
  GPU, and keeps picking attached to the rendered mesh.
- [Implementation account](../../../analyses/2026-09-09-state-topography.md) and
  [current build receipt](../build-receipt.json) retain numerical, renderer,
  compatibility and native-window validation.

The baseline Minime & Astrid views keep their original presentation. All changes
are in the research viewer; the beings and their state generation remain untouched.
