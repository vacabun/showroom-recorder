# Development

## Repository layout

```text
.
├── .github/workflows/publish.yml   # Publish to PyPI on version tags
├── config.example.json             # Example local runtime configuration
├── doc/                            # User and developer documentation
├── scripts/release.sh              # Local release helper
├── src/showroom_recorder/          # Package source
├── test/                           # Test suite
└── Makefile                        # Common development commands
```

## Local setup

1. Create and activate a virtual environment.
2. Install the project in editable mode if you are developing locally.
3. Install `ffmpeg` separately.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel build
python -m pip install -e .
```

Copy `config.example.json` to `config.json` and adjust the rooms and upload settings for your local machine.

## Common commands

```bash
make clean
make build
make reinstall
make release VERSION=0.7.16
```

`make clean` removes build artifacts, `__pycache__` directories, and `.DS_Store` files.

## Release flow

The local release helper does the following:

1. Validates the requested version string.
2. Refuses to run if the working tree is not clean.
3. Updates `src/showroom_recorder/version.py`.
4. Creates a commit.
5. Creates an annotated `vX.Y.Z` tag.
6. Pushes the current branch and tag to `origin`.

After the tag is pushed, GitHub Actions publishes to PyPI through Trusted Publishing.

## Local-only files

These files should stay out of Git:

- `config.json`
- `cookies.json`
- `.pypirc`
- `videos/`
- build artifacts such as `dist/` and `build/`
