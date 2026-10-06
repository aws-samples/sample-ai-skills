# Resolving the forge situation

A repository is in exactly one of three **forge situations**:

| Situation | `origin` is on | Publish target |
|---|---|---|
| *GitHub-primary* | GitHub | ignored |
| *GitLab-primary* | GitLab | none, or one that is not on GitHub |
| *GitLab-primary with a GitHub publish target* | GitLab | a repository on `github.com` |

The situation comes from the dev-context block when the repository has one, and from the probe
otherwise. Neither source is ever combined with the other.

## The dev-context block

Read the root `AGENTS.md`, then the root `CLAUDE.md`. The block is the text between the two marker
lines:

```markdown
<!-- ai-skills:dev-context -->
- forge: gitlab
- publish-target: https://github.com/example-org/example.git
<!-- /ai-skills:dev-context -->
```

Only two keys are read, each on a line of its own, with or without the leading `- ` of a list item:

| Key | Values |
|---|---|
| `forge` | `github` or `gitlab` |
| `publish-target` | `none`, or the URL of the repository the project publishes to |

Every other line inside the block is ignored. The block is **absent**, and the probe runs instead,
when either key is missing, a value is anything other than the ones above, only one of the two
markers is present, or the root files hold more than one block. Say which of these applied.

The block maps to a situation as follows:

- `forge: github` is *GitHub-primary*. A `publish-target` is reported and ignored.
- `forge: gitlab` with `publish-target: none` is *GitLab-primary*.
- `forge: gitlab` with a URL whose host is `github.com` is *GitLab-primary with a GitHub publish
  target*.
- `forge: gitlab` with a URL on any other host is *GitLab-primary*. Report that the publish target
  is not on GitHub, so no set is written for it.

## The probe

### The origin host

Run `git remote get-url origin`. A repository with no `origin` has an undetermined forge. Take the
host and the path from the URL:

| URL form | Host | Path |
|---|---|---|
| `https://<host>[:<port>]/<path>` | `<host>` | `<path>` |
| `ssh://[<user>@]<host>[:<port>]/<path>` | `<host>` | `<path>` |
| `[<user>@]<host>:<path>` | `<host>` | `<path>` |
| a local path, or `file://…` | none | none |

Drop a leading `/` and a trailing `.git` from the path. `git@gitlab.example.com:acme/widgets.git` has
the host `gitlab.example.com` and the path `acme/widgets`.

Apply these rules in order. The first that holds decides:

1. The host is `github.com`: **GitHub**.
2. The host contains `gitlab`, or a `.gitlab-ci.yml` exists at the repository root: **GitLab**. The
   file is what identifies a self-managed GitLab whose hostname does not contain `gitlab`.
3. Anything else: **undetermined**. A host that is not recognized is not evidence of either forge.

The two signals **disagree** when the host is `github.com` and a root `.gitlab-ci.yml` exists. Rule 1
still gives the conclusion, but the conclusion is not confirmed: say that the two signals disagree,
and name both.

### The publish target

Read the root `.promote-target` as text. It is a list of `KEY=value` lines. Never source it or run
anything it contains. Blank lines, `#` comment lines, and lines without `=` are ignored.

- No file, or no `PUBLIC_TARGET` line: no publish target.
- Exactly one `PUBLIC_TARGET` line whose URL has the host `github.com`: a GitHub publish target.
- One `PUBLIC_TARGET` line on any other host: a publish target that is not on GitHub.
- More than one `PUBLIC_TARGET` line, or a value that is not a URL: **undetermined**.

### The conclusion

| Forge | Publish target | Situation |
|---|---|---|
| GitHub | anything | *GitHub-primary*. A `.promote-target` is reported and ignored. |
| GitLab | none, or not on GitHub | *GitLab-primary* |
| GitLab | on GitHub | *GitLab-primary with a GitHub publish target* |
| GitLab | undetermined | *GitLab-primary*, with the publish target reported as undetermined |
| undetermined | anything | undetermined |

## The strings the public set must not contain

In the *GitLab-primary with a GitHub publish target* situation, the files written for the publish
target are checked for two strings taken from `origin`'s URL: its **host** and its **path**. Compare
without regard to case. A web link to the internal project rarely contains an SSH host such as
`ssh.git.example.com`, but it does contain the path, which is why both are checked.

Leave the path out of the check when it equals the publish target's own path, as in
`acme/widgets` on both forges. A string that also names the public repository identifies nothing
internal. When `origin` has no host, there are no strings to check, and the report says so.
