DEFAULT_CONFIG: dict = {
    "provider": {
        "type": "gitlab",
        "url": "",
        "token_env": "GITFLOW_GITLAB_TOKEN",
    },
    "branches": {
        "main": "master",
        "develop": "staging",
        "feature_prefix": "feature/",
        "hotfix_prefix": "hotfix/",
        "release_prefix": "release/",
    },
    "merge_request": {
        "feature_label": "story",
        "hotfix_label": "bug",
        "draft_prefix": "Draft: ",
        "remove_source_branch": True,
    },
    "changelog": {
        "output_dir": "release_notes",
        "version_tag_pattern": "{project}-{version}",
        "include_labels": True,
        "feature_labels": ["story", "feature"],
        "bug_labels": ["bug"],
        "technical_labels": ["technical debt"],
        "ignore_labels": ["ignore"],
    },
    "behavior": {
        "require_clean_worktree": True,
        "auto_push": True,
    },
}
