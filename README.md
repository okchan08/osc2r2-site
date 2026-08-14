# osc2r2-site

The landing page for **osc2r2**, a toolchain for ASAM OpenSCENARIO 2.0 and
OpenDRIVE. Published with GitHub Pages.

This repository holds the website only. The osc2r2 source lives elsewhere and is
not public.

## Contact

Please use this repository's
[issues](https://github.com/okchan08/osc2r2-site/issues) as the contact point
for osc2r2 itself — questions, bug reports, and feature requests, alongside
issues with the site. Templates for each are in `.github/ISSUE_TEMPLATE/`.
Anything sensitive should go through a private security advisory rather than a
public issue.

## Local preview

Open `site/index.html` in a browser, or serve the directory so relative paths
behave exactly as they will in production:

```sh
python3 -m http.server -d site 8000
# → http://localhost:8000
```

## Checks

To check every link is valid, run

```sh
python3 tools/check-links.py
```

## Deployment

Deployment is automated in CI. Refer to `.github/workflows/deploy.yml`. The CI is triggered on every push to `main`.

### URL

`https://okchan08.github.io/osc2r2-site/`
