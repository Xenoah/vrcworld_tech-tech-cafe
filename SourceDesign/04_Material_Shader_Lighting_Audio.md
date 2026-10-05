# Materials, flat-light shader, lighting and audio

## Visual target
The reference image should be interpreted as a **flat-light / stylized physically-informed** world. Geometry and value separation do more work than glossy realism.

## Flat-light world shader
Recommended behavior:
- Baked lightmap/GI is the primary light source.
- Quantize or compress diffuse response into 3 broad bands instead of smooth photoreal shading.
- Multiply in baked AO at low strength to keep corners readable.
- Optional subtle rim term only on hero materials; avoid anime-style full-outline rendering across architecture.
- Specular is broad and restrained. Metal can retain a narrow highlight, but most surfaces should read matte.
- Normal maps are low-amplitude; use them to create texture, not noisy microcontrast.
- Emission bypasses the quantized diffuse layer and is clamped before bloom.
- Distance fog / atmospheric grade should be done cheaply and consistently.

Conceptual lighting formula:
`final = albedo * (ambient + steppedDiffuse * key) * AO + restrainedSpecular + emission`

Suggested stepped diffuse bands: 0.32 / 0.62 / 1.00, softened around thresholds to avoid shimmering.

## PC material strategy
- One master opaque shader with toggles for metal/specular/emission.
- One transparent smoked-glass shader.
- One additive hologram shader.
- One unlit media shader.
- One cutout foliage shader.
- Minimize unique variants.

## Quest/mobile fallback
- Prefer baked albedo/lightmap and simplified vertex-lit or unlit variants.
- Replace transparent smoked glass with dithered or mostly opaque tinted surfaces.
- Remove real-time reflection/refraction.
- Hologram becomes a single additive texture + rotation.
- Disable foliage wind and expensive rim/specular features.

## Lighting
- Warm practicals 2700-3000 K visual appearance at bar/cafe.
- Neutral stage light around 4000-4500 K.
- Blue/cyan restricted to media, navigation and music systems.
- Default mode should not need multiple real-time shadow-casting lights.
- Bake the architecture and use reflection probes/cubemaps rather than screen-space reflections.

## Audio
- Background music should remain below conversation by default.
- Bar: light room tone and glass sounds, not constant crowd loops.
- DJ: low-frequency energy should be felt visually through lighting as much as acoustically.
- Quiet Room: substantially reduced BGM, minimal UI sounds.
- Avoid looping ambience with obvious short repetition.
