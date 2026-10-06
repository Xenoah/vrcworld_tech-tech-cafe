"""Verify packaged bytes against the checkout; emit release hashes and a report.

Run after package_release.py. This checks distribution integrity, not Unity or
VRChat runtime behavior. Uses only the Python standard library.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "Unity/Assets/TheCommons"
version = json.loads((ASSET_ROOT / "Data/world_manifest.json").read_text())["version"]
assert re.fullmatch(r"\d+\.\d+\.\d+", version), "Unexpected release version"
package = ROOT.parent / f"The_Commons_Compact_v{version}.unitypackage"
bundle = ROOT.parent / f"The_Commons_Compact_v{version}_Full.zip"


def digest(data):
    return hashlib.sha256(data).hexdigest()


paths = [ASSET_ROOT] + [
    p for p in ASSET_ROOT.rglob("*")
    if p.suffix != ".meta" and "Generated" not in p.parts
    and not p.name.endswith(".tmp")
]
required = {
    "Models/TheCommons_PC.fbx", "Models/TheCommons_Quest.fbx",
    "Models/TheCommons_PC.tcmesh.bytes", "Models/TheCommons_Quest.tcmesh.bytes",
    "Data/world_manifest.json",
    "Textures/relay_controller_albedo.png", "Textures/bar_labels_albedo.png",
    "Textures/cafe_props_albedo.png",
}
assert all((ASSET_ROOT / p).is_file() for p in required), "Missing required assets"
assert len(list((ASSET_ROOT / "Textures").glob("*_albedo.png"))) == 9

expected_tar = {}
guids = set()
for path in paths:
    meta = Path(str(path) + ".meta").read_bytes()
    matches = re.findall(rb"^guid: ([0-9a-f]{32})$", meta, re.MULTILINE)
    assert len(matches) == 1, f"Invalid GUID: {path}"
    guid = matches[0].decode()
    assert guid not in guids, f"Duplicate GUID: {path}"
    guids.add(guid)
    values = {
        "pathname": path.relative_to(ROOT / "Unity").as_posix().encode(),
        "asset.meta": meta,
        "asset": path.read_bytes() if path.is_file() else b"",
    }
    expected_tar.update({f"{guid}/{key}": digest(value) for key, value in values.items()})

with tarfile.open(package, "r:gz") as archive:
    members = archive.getmembers()
    assert len(members) == len(expected_tar), "Unexpected Unity package entry count"
    assert {p.name for p in members} == set(expected_tar), "Unity package asset set differs"
    for member in members:
        assert member.isfile(), f"Unexpected tar entry type: {member.name}"
        assert digest(archive.extractfile(member).read()) == expected_tar[member.name], member.name

names = subprocess.check_output(
    ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
).decode().split("\0")
files = {name: ROOT / name for name in names if name and (ROOT / name).is_file()}
source_hashes = {name: digest(path.read_bytes()) for name, path in files.items()}
with zipfile.ZipFile(bundle) as archive:
    expected_zip = {f"{ROOT.name}/{name}": sha for name, sha in source_hashes.items()}
    assert len(archive.namelist()) == len(expected_zip), "Unexpected full archive entry count"
    assert set(archive.namelist()) == set(expected_zip), "Full archive source set differs"
    for name, sha in expected_zip.items():
        assert digest(archive.read(name)) == sha, name

listed_hashes = {}
for line in (ROOT / "SHA256SUMS.txt").read_text().splitlines():
    sha, name = line.split("  ", 1)
    assert name not in listed_hashes, f"Duplicate checksum: {name}"
    listed_hashes[name] = sha
assert listed_hashes == {name: sha for name, sha in source_hashes.items() if name != "SHA256SUMS.txt"}

report = {
    "version": version,
    "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
    "scope": "Archive integrity only; Unity/Udon compilation and VRChat runtime not tested.",
    "passed": True,
    "unity_assets_including_folders": len(paths),
    "unique_unity_guids": len(guids),
    "full_archive_files": len(files),
    "checks": ["exact_asset_set", "unique_guids", "metadata_preserved", "all_bytes_match_source", "source_checksums"],
    "assets": {p.name: {"bytes": p.stat().st_size, "sha256": digest(p.read_bytes())} for p in (package, bundle)},
}
report_path = ROOT.parent / f"release-validation-v{version}.json"
report_path.write_text(json.dumps(report, indent=2) + "\n")
sums_path = ROOT.parent / f"SHA256SUMS-v{version}.txt"
sums_path.write_text("".join(f"{digest(p.read_bytes())}  {p.name}\n" for p in (package, bundle, report_path)))
print(json.dumps(report, indent=2))
