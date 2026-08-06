# gitflow-api

Modernized Git Flow automation library and CLI for GitLab and GitHub.

Current MVP status:
- ✅ GitLab provider
- ✅ GitHub provider
- ✅ feature start/finish
- ✅ hotfix start/finish
- ✅ release start/finish (only when `main != develop`)
- ✅ `launch` for real platform release creation
- ✅ changelog generation
- ✅ machine-friendly JSON output

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
- GitLab project access token with API access, or GitHub token with repo access

## Configuration

The CLI resolves configuration in this order:

1. Explicit file passed with `--config`
2. Project config in the target repository: `gitflow.toml` or `.gitflow.toml`
3. Global config: `GITFLOW_CONFIG`, then `$XDG_CONFIG_HOME/gitflow/gitflow.toml`, then `~/.gitflow.toml`
4. Built-in defaults

Preferred project config file name:

```bash
gitflow.toml
```

You can start from:

```bash
cp .gitflow.toml.example gitflow.toml
```

Or let the CLI create the file:

```bash
gitflow install
```

The installer asks whether the config should be created for the project or globally,
which provider to use, and the token to store in the generated config.

Non-interactive examples:

```bash
gitflow install --scope global --provider github --token "$GITHUB_TOKEN" --non-interactive
gitflow --repo /path/to/project install --scope project --provider gitlab --token "$GITFLOW_GITLAB_TOKEN" --non-interactive
```

Use `--force` to overwrite an existing config file.
For local setup, prefer the interactive command so the token is read without showing up in shell history.

Minimal GitLab example:

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

GitHub example:

```toml
[provider]
type = "github"
url = "https://api.github.com"
token_env = "GITHUB_TOKEN"
```

For GitHub Enterprise, prefer the API base URL, e.g. `https://github.company.com/api/v3`.

Export the token referenced by `token_env`:

```bash
export GITFLOW_GITLAB_TOKEN=xxxxx
# or
export GITHUB_TOKEN=xxxxx
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
- `launch` = create tag + platform release in the configured provider

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

- Internal naming still uses `merge_request` in a few interfaces; on GitHub that maps to pull requests.
- The future agent skill should wrap this CLI/library instead of reimplementing the workflow.
