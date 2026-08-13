# Coppy Agent Instructions


## System Changes / Agent Permissions

IMPORTANT: the files you edit should only be in this local repo, NEVER anywhere else on
the system.

You, the agent, should NEVER run commands on the system that would make permanent changes
outside the project's repo directory (excepting temporary files).

If a command/process you want to run would affect non-temporary files outside the
project directory, the command/process MUST BE READ-ONLY.

If you are ever confused about what you have permission to do, stop and ask.


### Exception: temporary files / directories

Exceptions to the permission policies:

- Ok: changes to files inside known system temporary directories like `/tmp`.
- Ok: create/update runtime artifacts like `.pyc`
- Ok: to make changes with uv that impact this project's venv ONLY
- Ok: tests may create, modify, and delete test artifacts under
  `/home/coppy-tests`.
- Ok: test commands may execute processes as the existing `coppy-tests` user.


### Conditional Instructions Index

1. At the start of every session, before responding to the first user prompt or doing any
   task-related work, you MUST ALWAYS look for the index file at
   `~/projects/agent-configs/conditional-instructions-local.yaml` and load it if present.
2. If the local index file is not present, load the remote
   [index file](https://raw.githubusercontent.com/rsyring/agent-configs/refs/heads/main/conditional-instructions.yaml).
3. You MUST NOT load any linked documents from the index UNLESS that document's `when`
   condition applies to the current task.
4. If neither index file can be loaded, stop and report that failure before answering the
   user substantively.
5. WHEN you load a document from the index, notify the user.


## System Commands

- Use ripgrep `/usr/bin/rg` instead of `grep` because it's faster
- `__MISE_SESSION` doesn't indicate mise is active for you. You ALWAYS have to run mise
  tools through `mise exec`


## File paths prefer dashes

UNLESS it's a `*.py` file, prefer dashes (`-`) in file paths and names instead of
underscores.


## Clarify coppy vs copier template at ./template

This project is `coppy`. It has it's own project config files like mise.toml .

It houses a [copier](https://copier.readthedocs.io) template at `./template`.

It's CRITICAL, when doing work, that you understand if the operator wants you to be
changing code for `coppy` or the copier template.


## Testing: copier.run_copy uses the local dirty working tree

When verifying template tests: `copier.run_copy(..., vcs_ref='HEAD')` uses the local dirty
working tree, not just committed changes. Do not blame uncommitted template changes for
missing generated output.


## Running tests that use the `coppy-tests` system user

Run pytest as the normal project user from the repository root. Do **not** run pytest as
`coppy-tests`; the test harness uses `sudo` internally to run generated-project commands
as that user with the correct `HOME` and `PATH`.

Use mise for every installed test command:

```shell
# Targeted template tests
mise exec -- pytest tests/coppy_tests/test_template.py::TestTemplateGen

# Full test suite
mise exec -- pytest
```

The outer pytest process creates and rotates test directories and a `pytest-run-current`
symlink under `/home/coppy-tests/tmp` during test collection. Therefore:

- Run these commands with filesystem access to `/home/coppy-tests`; in a sandboxed agent
  environment, request the required escalation for the test command.
- A sandbox failure such as
  `Read-only file system: /home/coppy-tests/tmp/pytest-run-current` means the outer pytest
  process lacks that access. Do not work around it by changing the test, its paths,
  ownership, or permissions.
- Do not run multiple pytest processes concurrently because they share and rotate the same
  `/home/coppy-tests/tmp/pytest-run-*` directories.
