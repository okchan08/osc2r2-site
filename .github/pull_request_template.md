## Summary

<!-- What changes, and why. One or two sentences is usually enough. -->

## Related issue

<!-- e.g. Closes #12. Delete this section if there is none. -->

## Screenshots

<!--
For anything that changes what a visitor sees, paste a before/after.
Delete this section for changes with no visual effect.
-->

| Before | After |
| ------ | ----- |
|        |       |

## Checks

- [ ] Previewed locally (`python3 -m http.server -d site 8000`)
- [ ] `python3 tools/check-links.py` passes
- [ ] Checked at a narrow viewport as well as a wide one
- [ ] No credentials, tokens, or private osc2r2 source in the diff

<!--
Reminders:
- Only `site/` is published. README, tools/, and workflows stay out of the
  deployed tree.
- CI runs the link check on pull requests; deployment happens on push to main.
-->
