"""Deterministic public release builder; never includes local environments or data."""
import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def files_in(path):
    candidates = [path] if path.is_file() else sorted(path.rglob("*"))
    for f in candidates:
        if f.is_symlink():
            raise ValueError(f"Refusing symbolic link: {f}")
        if "__pycache__" in f.parts or f.suffix in {".pyc", ".pyo"} or f.name == ".DS_Store":
            continue
        if f.is_file():
            yield f

def public_files(root=ROOT):
    for relative in PUBLIC_PATHS:
        path = root / relative
        if not path.exists():
            raise FileNotFoundError(path)
        yield from files_in(path)

def write_zip(path, entries):
    with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as archive:
        for name, f in sorted(entries):
            info=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0))
            info.create_system=3
            info.external_attr=0o100644 << 16
            archive.writestr(info,f.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    with zipfile.ZipFile(path) as archive:
        if archive.testzip():raise ValueError("Corrupt ZIP")


NAME="zotero-10-local-plugin"
VERSION="1.0.1"
PACKAGE_KIND="plugin"
PUBLIC_PATHS=['.agents', '.github', '.gitignore', 'plugins', 'scripts', 'README.md', 'README.zh-CN.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md']

def package_entries(root):
    base=root/"plugins/zotero-10"
    return [(f"zotero-10/{f.relative_to(base).as_posix()}",f) for f in files_in(base)]

def build(output, root=ROOT):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    version=VERSION
    source=output / f"{NAME}-source-v{version}.zip"
    write_zip(source,[(f"{NAME}/{f.relative_to(root).as_posix()}",f) for f in public_files(root)])
    extra=output / f"{NAME}-{PACKAGE_KIND}-v{version}.zip"
    write_zip(extra,package_entries(root))
    paths=[source,extra]
    (output/"SHA256SUMS.txt").write_text("".join(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}\n" for f in paths),encoding="utf-8")
    return paths

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT/"dist")
    args=parser.parse_args()
    for f in build(args.output):print(f"Built {f.name}: {f.stat().st_size} bytes")
