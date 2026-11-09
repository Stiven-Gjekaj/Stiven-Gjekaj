# Scripts

Two small tools keep the profile README current. Both need only the Python
standard library and run from the repository root.

## sync_versions.py

```bash
python3 scripts/sync_versions.py
```

- Sets the version tag at the end of each project line to that project's
  latest GitHub release. Projects owned by someone else are skipped.
- Writes `vX.Y` when the patch is 0, and the full tag otherwise. A tag that
  is already shown in full stays in full.
- Uses a pre-release, such as `v0.4-alpha`, only while a project has no full
  release.
- Sets the act and chapter counts of the Soultale line from the OPDS catalog
  of readsoultale.com.

`.github/workflows/sync-versions.yml` runs it once a day and commits any
change under the profile owner's name, with the list of changes in the commit
body. Run it by hand from **Actions > Sync versions > Run workflow**.

## build_stack.py

```bash
python3 scripts/build_stack.py
```

- Builds the tech stack rows in `assets/stack/` and the header icons in
  `assets/icons/`.
- `ROWS` at the top of the script sets which icons each row holds.
- Most icons come from skillicons.dev or Simple Icons. Official logos that
  neither has are kept in `assets/icons/src/`, with the source of each one in
  a comment next to the function that draws it.

Run it after changing `ROWS` or a logo, then commit the files it writes and
update the alt text of the matching row in the profile README.
