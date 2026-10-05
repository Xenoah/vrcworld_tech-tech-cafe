# THE COMMONS - Compact Edition | Work handoff

## What is authoritative
This folder supersedes contradictions in the concept image. Use `world_spec.json`, the DXF drawings, and this handoff as the geometry/feature authority. The image in `Reference/` is mood and composition reference only.

## One-line brief
Build a compact, vertically layered VRChat social venue where bar/cafe conversation, academic presentations, poster demos, and DJ nights share one coherent room without becoming a giant event hall.

## Fixed design decisions
- Gross footprint: **28.0 m x 18.0 m**.
- Two occupied levels: **1F +0.000**, **2F +4.800 m**.
- Roof datum: **+9.600 m**; feature lighting/hologram can reach **+10.800 m**.
- Comfortable population: **32**, event target **48**, design max **64**.
- Central atrium remains open across both levels.
- Visual language: dark neo-industrial structure, warm bar/cafe practicals, restrained cyan/blue neon, flat-light stylization.
- 1F is the active public floor; 2F is the slower overlook layer.
- Main academic stage and DJ system occupy the same visual axis but switch by mode rather than competing simultaneously.

## Build priority
1. Architectural blockout and avatar-scale validation.
2. Social distances / sight lines / voice-zone behavior.
3. Stage, screen and event-mode switching.
4. Bar/cafe/quiet/poster zones.
5. Flat-light material system and baked lighting.
6. DJ / AudioLink polish.
7. Decorative skyline, hologram and micro-detail.

## Files
- `CAD/The_Commons_Compact_Master.dxf`: 1F + 2F CAD plans side-by-side.
- `CAD/A-101_1F_Plan.dxf`, `CAD/A-102_2F_Plan.dxf`, `CAD/A-201_Section_AA.dxf`: individual CAD sheets.
- `CAD/The_Commons_Compact_Blockout.scad`: parametric-ish massing source.
- `CAD/The_Commons_Compact_Blockout.stl`: quick 3D massing export if available.
- `Drawings/The_Commons_Compact_Drawing_Set.pdf`: human-readable plan/section set.
- `The_Commons_Compact_Design_Packet.pdf`: detailed concept + implementation packet.
- `world_spec.json`: dimensions and zones in machine-readable form.
- `Schedules/*.csv`: room/material/light/interaction schedules.

## Critical implementation instruction
Do **not** model the reference image literally. Preserve its mood, density and vertical composition, but use the supplied dimensions and circulation. Keep architecture readable at avatar eye height (~1.6 m) and avoid decorative clutter in the main walkable 1.8 m circulation bands.
