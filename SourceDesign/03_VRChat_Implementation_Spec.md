# VRChat implementation specification

## Operating modes
### Lounge mode
Warm practical lighting, low music, stage screen becomes ambient art/data visualization. Bar and cafe are primary social anchors.

### Academic mode
DJ visuals off. Stage key light active. Main screen prioritized. Audience seats/markers optionally appear. Poster bays display event content. Background music drops substantially.

### DJ mode
Stage becomes standing floor. DJ booth and ring lights activate. Screen becomes visualizer/video surface. Lighting animation remains slow enough to avoid visual fatigue and should include a reduced-motion toggle.

### Quiet Night mode
Most blue/cyan elements dim. Hologram motion slows. Warm local lamps dominate. Ideal for small late-night groups.

## Presentation system
- Main visual surface: 16:9, approx. 7.1 x 4.0 m effective image.
- Presenter positions: center + two panel positions.
- Session timer visible to presenter and optionally audience.
- Laser pointer should be replaced by a stable world-space pointer/reticle to avoid jitter.
- Separate Q&A indicator from voice amplification.
- Support still slides, video, and a 3D-demo pedestal next to stage.
- Poster area should be data-driven so images/titles can be replaced without remodeling.

## Social systems
- Topic cards can be enabled on bar/cafe tables.
- Drink props are optional conversation affordances, not progression mechanics.
- Avoid UI popups on spawn. Put controls on physical panels.
- Host controls belong in AV/BOH and a discreet presenter panel.
- Provide local-only comfort settings: bloom/emissive intensity, ambient motion, mirror, DJ visual intensity.

## Voice and audio zoning
Design spatially first; use scripted voice presets only as reinforcement. Bar, main lounge, terrace and Quiet Room should read as separate conversational clusters by distance and enclosure.

## Network philosophy
Keep all decorative state local where possible. Network only mode changes, shared event playback state, and interactions that genuinely need shared synchronization.
