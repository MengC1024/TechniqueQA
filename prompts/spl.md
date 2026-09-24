# QA construction for SPL

Research the supplied MITRE ATT&CK Technique and Procedures using public
technical documentation and incident research. Construct QA pairs that connect
attack behaviors to documented knowledge for SPL detection.

The procedures are evidence and search seeds, not output rows. Do not produce
one QA per procedure. You may merge multiple procedures, split one procedure
into multiple reusable behaviors, omit redundant actor examples, and add
documented behaviors within the same Technique when research supports them.

## Coverage

Before submitting QA, privately build a checklist of the concrete attack
mechanisms you found. Treat mechanisms as different when an implementer would
need a different executable, command token, registry or file path, DLL/API,
access mask, parent-child relationship, event type, or temporal sequence.

Research the technique itself in addition to following the supplied procedure
citations. Cover the distinct mechanisms supported by the sources.
Merge entries only when the same concrete rule conditions would implement
them. Do not output the private checklist.

## Questions

Every question must describe an attacker action, mechanism, or multi-step
attack process in the same semantic perspective as a downstream attack-
behavior description.

Keep questions focused on the attacker's behavior. Put detection instructions
and query implementation details in the answer. Logs, tables, and similar
objects may appear when they are part of the attack itself. Replace actor,
campaign, malware family, and CVE identifiers with the underlying attack
mechanism.

Good question forms include:

- How can an attacker use rundll32 and comsvcs.dll to dump LSASS memory?
- How does an attacker execute remote HTA content through mshta.exe?
- How can an attacker hijack a per-user registry association and trigger an
  auto-elevated utility to bypass UAC?

## Answers

Each answer must be implementation knowledge that can be translated directly
into an actual SPL detection rule, not a high-level detection idea. Include all
source-supported details needed for the specific mechanism:

- concrete event source or event type and exact event IDs when applicable;
- concrete field concepts and documented native, CIM, or common Splunk field
  names when available;
- exact executable, command-line token, DLL/API, registry path/value, file
  path, access right, network artifact, or other discriminating literal;
- required Boolean conditions, parent-child or entity relationships, joins,
  aggregation, and time ordering;
- concise SPL-compatible predicates, `where` expressions, or a compact search
  skeleton when they can be grounded in the sources.

Combine facts from multiple documents when the detection need spans sources.

The downstream environment remains authoritative. If multiple documented field
names or telemetry sources can represent the same evidence, state the mapping
as alternatives instead of silently choosing one. Do not invent a private
index, sourcetype, macro, lookup, or local alias.

Keep answers focused on documented detection knowledge. Exclude instructions
about the QA construction process.

## Sources and exclusions

Prefer MITRE ATT&CK and its citations, operating-system and product
documentation, official Splunk documentation, CISA/NVD, vendor research, and
incident reports. Open and verify the sources used for every implementation
claim.

Do not inspect or cite detection-rule repositories, rule code, evaluation
data, gold/reference rules, previous QA outputs, experiment results, or paper
drafts. In particular, do not use Splunk Security Content, SigmaHQ, Azure
Sentinel rule repositories, or mirrors and derivatives of those collections.

Let the available evidence determine the number of QA pairs.

## Submission

Call `submit_qa` alone with an `entries` list. Each entry must contain
`question`, `answer`, and `source_ids`. Cite only documents you have read.
The program assigns QA IDs and resolves source metadata.
If no QA is supported by the sources, submit an empty `entries` list.
