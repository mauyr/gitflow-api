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

Without `--config`, global configuration is loaded first and the project file is
merged over it. This lets a project add a deploy profile without duplicating a
shared provider credential configuration.

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

`launch` calculates the changelog before creating the tag, so the platform release
receives the complete range of changes. Its title is configurable:

```toml
[launch]
release_name_template = "v{version}"
```

Templates may use `{project}`, `{version}` and `{tag}`.

### Deployments

Deployments are explicit and profile-based. A normal `launch` never deploys by
surprise. This keeps the core release flow reusable across projects while allowing
each project to choose its own production mechanism.

```bash
gitflow deploy production --version 1.2.3 --dry-run
gitflow deploy production --version 1.2.3
gitflow launch 1.2.3 --deploy staging
```

Profiles live in TOML and must not contain credentials. The built-in `command`
driver runs a trusted argument array without a shell:

```toml
[[deploy.profiles]]
name = "production"
driver = "command"
command = ["./scripts/deploy-production.sh", "--version", "{version}"]
working_directory = "."
timeout_seconds = 1800
```

The command receives `{version}`, `{tag}`, `{repo_path}`, `{remote_url}` and
`{release_url}` template variables. Additional deployment drivers can be installed
as Python entry points in the `gitflow_api.deployment_extensions` group.

The built-in `digitalocean-app` driver uses the locally authenticated `doctl`
command. It requires every source that belongs to the release to be listed in
`components`; before deployment, each configured release tag must resolve to the
same commit as `origin/<branch>`.

Set `enabled = false` while a profile is being prepared; the CLI will refuse to
execute it until it is explicitly enabled.

```toml
[[deploy.profiles]]
name = "legal-lite-production"
driver = "digitalocean-app"
app_id = "<digitalocean-app-id>"
context = "production"
wait = true
timeout_seconds = 1800
components = [
  { path = "/workspace/lite/bff", branch = "master", tag = "{version}" },
  { path = "/workspace/lite/frontend", branch = "master", tag = "{version}" },
]
```

For a product whose DigitalOcean App bundles multiple repositories, run the
component launches first and the deployment profile last. This prevents a deployment
from using a component that has not yet received its release tag.

The `examples/legallite.gitflow.toml` file is a safe starting point for the
LegalLite App. It remains disabled until the BFF, frontend and user-guide share a
release-tag convention.

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
