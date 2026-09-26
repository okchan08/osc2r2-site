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

The demo page is published under it, at
`https://okchan08.github.io/osc2r2-site/app/`. That directory is not authored
here: osc2r2 builds it and opens a pull request carrying it, so nothing under
`site/app/` should be edited by hand — the next publish overwrites it.

## Outbound links

`tools/check-links.py` rejects any absolute URL that is not in its
`ALLOWED_ABSOLUTE` set, so a new off-site link has to be added there as well as
to the page. The ones the site currently points at:

- the VS Code extension —
  <https://marketplace.visualstudio.com/items?itemName=okchan08.openscenario2>
  (`okchan08.openscenario2`, listed as *OpenSCENARIO 2.0*)
- this repository's issues, new-issue chooser, and private advisory form
