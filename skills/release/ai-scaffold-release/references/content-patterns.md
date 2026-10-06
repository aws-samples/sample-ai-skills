# Content scan pattern classes

**The base promote path runs no content scan.** This is the starting set for a
repository that writes one, because the patterns are any single organisation's
and cannot be shipped as a default. `references/promote-extensions.md` says
where such a scan belongs: a job dependency on a scan the pipeline already
runs, not the gate hook, which is reserved for what must run inside the push
transaction.

A path filter cannot see content written into three artifacts that travel
with a publish regardless of which paths ship: the tag annotation body, the
tag object's `tagger` line, and the public release body. A scan over those three
covers five pattern classes. Report findings and refuse; never redact —
redaction hides the finding from the person who most needs to see it and fix
the source.

1. **Internal hostnames** — the organisation's internal-only domains, which
   mean nothing to a public reader and confirm its infrastructure.
2. **Internal forge paths** — namespace paths such as `<group>/<subgroup>/…`
   that reveal internal project structure even without a hostname attached.
3. **Internal aliases** — usernames or handles meaningful only inside the
   internal directory.
4. **Ticket identifiers** — internal ticket-tracker patterns (for example
   `TICKET-12345`, or a single-letter-prefixed review identifier) that are
   meaningless externally and confirm which internal tracker the project uses.
5. **Internal CI variable names carrying literal values** — not the variable
   name itself (a bare token name is harmless documentation), but an actual
   assigned value such as `<TOKEN_NAME>=<literal>` appearing in text that will
   be published.

The concrete values behind classes 1–4 are the installing organisation's to
supply. Writing them into this reference would ship one organisation's internal
hostnames and namespace paths inside the very tree a publish carries — the
mistake `assets/promote-target.template` exists to not repeat.

## What the scan never covered

The predecessor's scan read the annotation, the `tagger` line, and the release
body, and **never opened a file in the tree**. Nothing in it stopped an internal
string inside a shipped file from publishing. A repository implementing this
class of protection should implement it where it can see the tree, and should
not assume a scan of those three artifacts is coverage of the publish.

## Publisher identity defaults to neutral

`PUBLISHER_IDENTITY` in `.promote-target` defaults to a neutral, non-internal
address. This is deliberate: the tag object's `tagger` line is one of the three
artifacts a publish carries whatever the filter does, and a default of a real
internal address (for example an internal CI service account) would put an
internal identity on every public tag.

Overriding it to a real address is allowed and the base asks for no
acknowledgement of that choice — the predecessor's `ACK_CONTENT_EXPOSURE` is
retired with the rest of the gates. A repository that wants the choice
acknowledged deliberately rather than inherited from a template puts the check
in `scripts/promote-gates.sh`, where it can read the configured identity and
refuse.
