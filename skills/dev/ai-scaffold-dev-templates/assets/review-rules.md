<!--
  Source: written in the ai-skills repository for its ai-scaffold-dev-templates
  skill. Not derived from a published template.
  License: MIT No Attribution (MIT-0).
-->

## Review rules

Mark a finding Important only when the change, as written, would:

- break behavior that worked before, or fail to do what its description claims;
- lose or corrupt data;
- open a security hole, such as a leaked secret, exposed personal data, or a
  skipped authorization check.

Use exactly these three severity levels:

- **Important**: one of the cases above. Fix it before merging.
- **Nit**: a real issue that is worth fixing and does not hold up the merge.
- **Pre-existing**: a defect this change did not introduce. Report it, and do
  not hold up the merge for it.

A style, naming, or refactoring preference is a Nit at most. Mark it as
optional, or leave it out.
