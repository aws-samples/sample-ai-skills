# Trackers reached through MCP tools: Asana, Jira

Read when the configured tracker is a work-management system this session exposes as MCP tools rather
than a git forge. Tool names vary by server, so the sequence below is the pattern; discover the actual
names with `ToolSearch` (e.g. `ToolSearch "+asana create task"`) and fetch their schemas before
calling them — an MCP tool cannot be invoked from its name alone.

The general shape is the same everywhere:

1. Resolve the destination (project / board / workspace) — never guess an ID.
2. Read the destination's field schema: sections, custom fields, and their **allowed enum values**.
3. Search for a duplicate.
4. Create the task, then set fields and section membership.
5. Report the permalink.

## Resolve the destination

Prefer an ID the project wrote down. `CLAUDE.md` links are the usual source:

```
https://app.asana.com/1/<workspace-gid>/project/<project-gid>/   → project gid
https://<host>/browse/ABC-123                                    → Jira project key ABC
```

A URL in the repo's own docs is authoritative. If you have only a name, list projects and match — and
if two plausibly match, that is worth one question, because filing into the wrong board is invisible
to the reporter and confusing to everyone on the right board.

## Read the field schema before drafting

Work-management trackers carry the equivalent of a template as **custom fields**, and they are often
required by the team's process even when the API accepts a task without them:

- Asana: `GetProject` (custom field settings), `GetProjectSections` — sections are frequently the
  triage state ("Inbox", "Triage", "In progress"), so a task created without one lands nowhere.
- Jira: the create-meta for the project and issue type lists required fields and allowed values.

A custom field that is an enum accepts only its declared options. Pick the closest existing option;
do not invent one, and leave the field unset rather than forcing a bad fit.

**Map the issue body onto the tool's fields:** title → task name, the Phase 4 body → description
(these trackers take markdown or rich text; if the field is plain text, keep the structure with plain
`## ` headings rather than dropping it). Kind, severity, and area usually belong in custom fields
rather than the body — set them there, and do not duplicate them in the text.

## Check for duplicates

Search the workspace or project for the distinctive error text and the affected component
(`AsanaSearch`, `SearchTasksInWorkspace`, Jira JQL `project = ABC AND text ~ "…" AND statusCategory != Done`).
Include completed-recently items in what you read: a task closed last week that describes the same
symptom means a regression, which is worth saying in the new issue.

## Create it

Create with name + description + project, then follow up for anything the create call does not take:

- Asana: `CreateTask` (`projects: [<gid>]`, `name`, `notes` or `html_notes`), then `AddTaskToSection`
  for the triage column and `UpdateTask` for custom fields. `html_notes` requires Asana's restricted
  HTML subset — plain `notes` is safer unless you know the subset.
- Jira: create with the required fields from create-meta in one call; transitions are separate.

Do not add followers, assignees, or due dates unless the project's conventions call for them —
an unasked-for assignment notifies a human and quietly moves work onto their plate.

## Report and cross-link

Report the task permalink, not just the GID — a bare ID is unusable to the human. For a split batch,
add a comment on each task naming its siblings by permalink (`CreateTaskStory` in Asana), since these
trackers have no `#<n>` shorthand.

## When the tracker is unreachable

A missing MCP server, a failed auth, or a project you cannot write to is not a reason to lose the
observation: write the local markdown file from the skill's Phase 6, report the path, and say plainly
that it still needs filing by hand.
