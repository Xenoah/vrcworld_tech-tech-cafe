# Architectural specification

## Coordinate and scale
- CAD units: millimeters.
- World design units: meters.
- Origin: southwest outer corner.
- +X east, +Y north, +Z up.
- 1F datum: +0.000 m.
- 2F datum: +4.800 m.
- Roof datum: +9.600 m.

## Overall size
- 28.0 m x 18.0 m footprint.
- 504 m² gross first-floor envelope.
- Partial second floor surrounds a central double-height atrium.
- Primary circulation target 1.8 m clear; secondary 1.2 m.

## 1F
- Entrance/orientation at south center, 5.0 m wide zone.
- Main Bar along west side; bar acts as the social anchor rather than a decorative edge.
- Cafe tables at southwest for low-intensity entry and waiting.
- Central lounge converts between daily social seating, academic audience, and standing DJ floor.
- Stage is Ø4.8 m, 0.25 m high, centered north of the lounge.
- Main media wall visually anchors the north axis.
- East gallery contains poster/demo bays.
- East stair is the primary visible route to 2F; west stair completes a circulation loop.
- Back-of-house/AV remains visually quiet and partially hidden.

## 2F
- West: cafe mezzanine and work tables.
- North: gallery bridge with standing overlook.
- Center/north: suspended DJ booth facing the atrium.
- East: skyline terrace/overlook.
- Southeast: fully enclosed Quiet Room for 4-8 people.
- South bridge provides visual connection without creating a full second-floor lid.

## Spatial rule
Keep the central atrium visually continuous. The user should be able to locate the bar, stage, DJ booth and at least one escape/quiet destination from the entrance.

## VR locomotion notes
- Visual stairs may use simplified ramp colliders to prevent head-bob and controller snagging.
- Add an optional vertical portal/elevator for users who dislike stairs.
- Avoid 50-100 mm decorative level changes in walking areas.
- Keep railings visually ~1.05 m high but collider behavior should not trap avatars.
- Avoid narrow dead ends under 1.2 m.
