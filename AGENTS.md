# Agent instructions

## Purpose

Profile README of Tarek ElHussain on GitHub. It shows an animated header, a neofetch-style card, one live status card per public project, and a diagram of how a request reaches Bikelytics. The README is static: every visual is a generated SVG in `img/`.

## Maintenance

- Do not edit `img/*.svg` by hand. Change the generator in `scripts/` and regenerate.
- Regenerate one image: `python3 scripts/make_<name>.py`. Scripts use only the standard library. `--demo` runs the self-checks where a script has them.
- Regenerate all images: `<was-fehlt>`
- Project cards: list only projects that are publicly reachable and meant for the public. `.github/workflows/update-status.yml` refreshes their status every hour.
- `STATIC=1` renders a frozen neofetch frame for previewing. The key is listed in `.env.example`.

## Structure

- `README.md`: the profile page. It embeds the images from `img/`.
- `img/`: generated SVGs, one `-dark` and one `-light` variant each. Do not edit by hand.
- `scripts/`: Python generators for the SVGs. `theme.py` holds the shared font and palette, `make_info_card.py` the card that `make_neofetch_svg.py` embeds.
- `.github/workflows/`: `update-status.yml` refreshes the project status hourly. `gitleaks.yml` scans every push and pull request for secrets.
- `.gitattributes`, `.gitignore`, `.env.example`: repo settings. `.env` stays ignored and is never committed.
- `CLAUDE.md`: imports this file for Claude Code.

## Projektstandard

This repo follows the Projektstandard (version 0.2), profile minimal, class none. No exceptions apply.
