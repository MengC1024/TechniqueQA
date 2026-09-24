# Detection rule generation

Generate exactly one detection rule from the supplied attack behavior and
environment. Use the specified target language.

Treat the environment object as authoritative. Use the stated platform,
telemetry, fields, and available dependencies. Do not invent an unavailable
lookup, parser, macro, data model, table, index, sourcetype, or local alias.
Implement every behavior constraint that can be expressed from the visible
input.

For `kql` and `spl`, return only the query text.

Return no Markdown fence, explanation, title, metadata, alternatives, or test
data.
