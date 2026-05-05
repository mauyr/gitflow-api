# gitflow-api

Modernized **GitLab-first** Git Flow automation library and CLI.

Current MVP status:
- ✅ GitLab provider
- ✅ feature start/finish
- ✅ hotfix start/finish
- ✅ release start/finish (only when `main != develop`)
- ✅ `launch` for real platform release creation
- ✅ changelog generation
- ✅ machine-friendly JSON output
- ❌ GitHub provider (not implemented yet)

## Installation

### From source

```bash
pip install -e .
```

### Build/package

```bash
python -m build
```

## Requirements

- Python 3.10+
- `git`
- GitLab project access token with API access

## Configuration

Preferred config file name:

```bash
.gitflow.toml
```

You can start from:

```bash
cp .gitflow.toml.example .gitflow.toml
```

Minimal example:

```toml
[provider]
type = "gitlab"
url = "https://gitlab.example.com"
token_env = "GITFLOW_GITLAB_TOKEN"

[branches]
main = "master"
develop = "staging"
feature_prefix = "feature/"
hotfix_prefix = "hotfix/"
release_prefix = "release/"

[merge_request]
feature_label = "story"
hotfix_label = "bug"
draft_prefix = "Draft: "
remove_source_branch = true

[changelog]
output_dir = "release_notes"
version_tag_pattern = "{project}-{version}"
include_labels = true
feature_labels = ["story", "feature"]
bug_labels = ["bug"]
technical_labels = ["technical debt"]
ignore_labels = ["ignore"]

[behavior]
require_clean_worktree = true
auto_push = true
```

Export the token referenced by `token_env`:

```bash
export GITFLOW_GITLAB_TOKEN=xxxxx
```

## CLI

The package installs the `gitflow` command.

### Health/config

```bash
gitflow version
gitflow config-check --json
```

### Feature flow

```bash
gitflow feature start my-feature --title "My Feature"
gitflow feature finish
```

### Hotfix flow

```bash
gitflow hotfix start urgent-fix --title "Urgent Fix"
gitflow hotfix finish
```

### Release flow

`release start` / `release finish` only make sense when the project uses two distinct long-lived branches, e.g. `master` and `staging`.

If `main == develop`, the command fails intentionally.

```bash
gitflow release start 1.2.3
gitflow release finish
```

Semantics:
- `release start` = freeze what is in `develop/staging`
- `release finish` = reintegrate the release branch into `main/master`
- `launch` = create tag + platform release in GitLab

### Launch

```bash
gitflow launch 1.2.3
```

### Changelog

```bash
gitflow changelog 1.2.3
```

## JSON output

Use `--json` for automation or future agent skill wrappers:

```bash
gitflow --json feature start my-feature
gitflow --json release start 1.2.3
gitflow --json launch 1.2.3
```

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests/unit -t . -v
```

## Notes

- This MVP is intentionally **GitLab-only**.
- The old GitHub claim was removed because it was fiction dressed as documentation.
- The future agent skill should wrap this CLI/library instead of reimplementing the workflow.
