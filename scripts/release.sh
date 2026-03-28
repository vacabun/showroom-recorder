#!/usr/bin/env bash

set -euo pipefail

usage() {
    echo "Usage: $0 <version> [remote]"
    echo "Example: $0 0.7.16"
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
    usage
    exit 1
fi

version="$1"
remote="${2:-origin}"

if [[ "$version" == v* ]]; then
    echo "Pass the bare version number, not a tag. Use 0.7.16, not v0.7.16." >&2
    exit 1
fi

if [[ ! "$version" =~ ^[0-9]+(\.[0-9]+)*([.-][0-9A-Za-z]+)*$ ]]; then
    echo "Unsupported version format: $version" >&2
    exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

version_file="src/showroom_recorder/version.py"
tag="v$version"
branch="$(git branch --show-current)"

if [[ -z "$branch" ]]; then
    echo "Detached HEAD is not supported for releases. Check out a branch first." >&2
    exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
    echo "Working tree is not clean. Commit or stash changes before releasing." >&2
    exit 1
fi

if git rev-parse "$tag" >/dev/null 2>&1; then
    echo "Tag already exists locally: $tag" >&2
    exit 1
fi

if git ls-remote --exit-code --tags "$remote" "refs/tags/$tag" >/dev/null 2>&1; then
    echo "Tag already exists on $remote: $tag" >&2
    exit 1
fi

python3 - "$version_file" "$version" <<'PY'
import pathlib
import re
import sys

path = pathlib.Path(sys.argv[1])
version = sys.argv[2]
text = path.read_text(encoding="utf-8")
updated, count = re.subn(
    r"^__version__ = ['\"]([^'\"]+)['\"]$",
    f"__version__ = '{version}'",
    text,
    count=1,
    flags=re.MULTILINE,
)

if count != 1:
    raise SystemExit(f"Could not update version in {path}")

path.write_text(updated, encoding="utf-8")
PY

git add "$version_file"
git commit -m "release: $tag"
git tag -a "$tag" -m "$tag"
git push "$remote" "$branch" "refs/tags/$tag"

echo "Released $tag from branch $branch and pushed to $remote."
echo "GitHub Actions will publish to PyPI after the tag workflow succeeds."
