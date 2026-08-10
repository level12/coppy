Get rid of dependency on hatch cli and related

This is a breaking change if a project:

- Uses Hatch environments or other Hatch CLI functionality
- Customizes the old `bump` task or has built automations on it
- Depends on a "v" prefix in the version in `version.py` (a "v" is still present in the Git tag
  added by version bumping)

CLI replacements:

- `hatch build` → `mise run build`
- `hatch version` → `mise run version show`
- `mise run bump` → `mise run version bump`
