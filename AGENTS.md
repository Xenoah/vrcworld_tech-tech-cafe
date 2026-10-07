# Release requirements

- The owner requests screenshots attached to every release from v0.5.0 onward.
- Render or capture the actual model in that release. Include an overview and views of the changed area; inspect every image.
- List images and their rendering source in `Documentation/release_screenshots.json`, matching the release version. Do not describe Blender previews as Unity/VRChat runtime screenshots.
- Attach the PNG files as GitHub release assets and embed them in release notes. Include them in distribution checksums.
- Run `Blender/verify_release.py` after packaging. Missing, incomplete or invalid required screenshots must fail verification.
- CVS2 and VRC+ supply vehicles/drones. Do not add their systems or redistribute third-party assets unless separately requested and authorized.
