# Optimization and production budget

These are **design targets, not VRChat hard limits**. Re-profile on the actual target SDK and hardware.

## PC target
- Main-view world geometry: aim for <= 0.8-1.2 M visible triangles after LOD/occlusion.
- Batches/setpass: target <= 150 in normal lounge view.
- Real-time shadowed lights: 0-1 during normal operation.
- Reflection: baked probes/cubemaps; no dependency on screen-space reflection.
- Texture sizes: hero surfaces 2K, most props 1K, atlas small props/signage.
- Mirrors: local toggle, default off, constrained to one small area.

## Quest/mobile target
- Main-view geometry target <= 200-300k visible triangles.
- Aggressive material atlas and mesh combining.
- Transparent surfaces minimized.
- No real-time shadows in standard mode.
- Simplified hologram and DJ visuals.
- LOD or impostors for city exterior.

## Occlusion strategy
- Use the bar back, stair cores, Quiet Room, BOH wall and poster spine as deliberate occluders.
- The central atrium remains open, so optimize hero assets and skyline heavily.
- Divide the world into meaningful static occlusion groups by zone rather than hundreds of tiny renderers.

## Build phases
1. Graybox: geometry + colliders + spawn + stairs + sight-line testing.
2. Social prototype: voice distances, seating clusters, presentation mode.
3. Art pass 1: architecture materials + baked lighting.
4. Systems: media, posters, DJ, topic/drink interactions.
5. Art pass 2: signage, plants, skyline, hologram.
6. Optimization / Quest fallback.
7. Event test with 20-40 real users.
