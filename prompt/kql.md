# QA construction for KQL

Research the supplied MITRE ATT&CK Technique and Procedures using public
technical documentation and incident research. Construct QA pairs that connect
attack behaviors to documented knowledge for KQL detection.

The procedures are evidence and search seeds, not output rows. Do not produce
one QA per procedure. You may merge procedures that expose the same observable,
split a procedure when distinct implementations need different conditions,
omit unsupported or redundant examples, and add documented behaviors within
the same Technique when research supports them.

## Questions

Each question must describe an attacker action, concrete mechanism, or short
attack process in the same semantic perspective as a downstream attack-behavior
description. Preserve implementation anchors that distinguish the behavior,
such as a command token, identity or permission operation, URL property,
protocol action, API, object type, or parent-child relationship.

Keep questions focused on the attacker's behavior. Put detection instructions
and query implementation details in the answer. Logs, tables, and similar
objects may appear when they are part of the attack itself. Replace actor,
campaign, malware family, and CVE identifiers with the underlying attack
mechanism.

## Answers

Each answer must contain source-supported implementation knowledge that can be
translated directly into a KQL detection. Include the minimum sufficient set
of:

- applicable Microsoft Sentinel, Defender XDR, Azure, Entra, Microsoft 365, or
  documented connector table names;
- concrete column names and values, operation names, object types, paths,
  binaries, command tokens, result codes, identity relationships, or URLs;
- required predicates, normalization, joins, aggregation keys, thresholds, and
  time windows when the behavior genuinely requires multiple records.

Combine facts from multiple documents when the detection need spans sources.

Answers may be detailed. A compact KQL fragment is allowed when it faithfully
expresses verified documentation, but do not copy or inspect an existing
detection rule. The downstream environment remains authoritative, so state
documented table or column alternatives when products expose the same behavior
through different schemas. Do not invent private aliases, local tables,
allowlists, thresholds, or organization-specific values.

## Coverage and sources

Privately identify the distinct, query-implementable mechanisms supported by
the technique input and research. Cover those mechanisms without imposing a
fixed number of QA entries. A procedure may yield no QA when it provides no
concrete observable, and multiple procedures may support one QA.

Prefer MITRE ATT&CK and its citations, Microsoft Learn and official product or
connector documentation, CISA/NVD, and vendor or incident research. Open and
verify every source used for implementation claims.

Do not inspect or cite Microsoft Sentinel analytics-rule repositories, hunting-
query repositories, evaluation data, gold/reference rules, previous QA
outputs, experiment results, or paper drafts.

## Submission

Call `submit_qa` alone with an `entries` list. Each entry must contain
`question`, `answer`, and `source_ids`. Cite only documents you have read.
The program assigns QA IDs and resolves source metadata.
If no QA is supported by the sources, submit an empty `entries` list.
