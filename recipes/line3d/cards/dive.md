# Dive: the surface becomes the next world

The camera accelerates into the hero object; its surface cells fill the frame and are, without a cut, the cells of the next scene's ground.

**Use when:** going from an overview to a detail: the world to a city, a chip to a circuit, a dashboard to one record. The best scene change in the grammar (principles: transitions, 1).

**Duration and energy:** ≈ 0.9 s in all: ≈ 0.6 s of ease-in fall, ≈ 0.3–0.4 s of the new world decelerating. High energy, once per film or per act.

## Intent
The viewer never loses the thread: the thing they were looking at is the place they land in. The two worlds share one structure (the cell pitch), so the hand-over is a change of scale, not a change of picture.

## Motion core (measured at 60 fps)
- **Turn first, then fall:** `K.dive(k, from, p, n, up, endHeight, { swing: 0.55, push: 0.6, ease: "power3.in" })`. Over the first 55 % the camera swings onto the surface normal (`power2.inOut`) and pushes in to 60 % of its distance, so the object never shrinks while it turns; the fall along the normal is `power3.in`. A dive that falls at a graze reads as skidding over the surface.
- **Speed:** on the sphere's edge 2 px a frame at the start, 10 px a frame 0.25 s later, frame filled after ≈ 0.5 s.
- **Hand-over:** at the swap the camera is straight above the target cell (`endHeight` ≈ 0.34 cell-heights × scale); the new world is built at the same angular pitch (`sphereCells` cell = `cellGrid` cell), centred on `K.cellCentre(lat, lon, cell)`, in units of one cell = 1. Same view, same cells: no cut.
- **After the swap: keep falling into the world.** The new rig starts at the swap pose and continues with the fall's speed (`expo.out` over ≈ 0.4–0.55 s), then tilts toward a perspective view. The reference keeps diving and rolling with lines smeared; ours (pilot) slows and settles: it reads as arriving, not as being inside a world that pulls you in. Next time: keep the speed up longer and add roll.
- **Spin stops with the dive:** the object's own rotation decelerates to zero over the dive (`k - k²/2`), so the target holds still under the camera.

## Parameters
| Parameter | Value | Push up | Push down |
|---|---|---|---|
| dive length | 0.62 s | over 0.9 s: a zoom, not a dive | under 0.4 s: a cut with blur |
| `swing` | 0.55 | the fall starts late and hits hard | under 0.3: the camera turns while falling, the surface skids |
| `push` | 0.6 | (1) the object shrinks while the camera turns | under 0.4: the turn already fills the frame |
| `endHeight` | ≈ 4 cells of view | the swap shows many cells, the new world starts far | under 2: one cell fills the frame, the pitch is lost |

## Pitfalls
- **The target must face the camera when the dive starts.** Choose its longitude in view space and subtract the spin up to the dive (`lon = lonView - SPIN * T_DIVE`).
- Fog is in each world's units: switch it at the swap (globe 2.6–6.5, city 5–22).
- The HUD that belongs to the old world leaves before the swap (a 0.25 s slide out), not after.

## Reference
Built in `recipes/line3d/globe-dive.html` (`surfaceFrame`, `K.dive`).
