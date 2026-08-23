# Frozen public trace prompt v2

You are participating in a disclosure-safe research pilot. Use only this prompt and public,
credential-free sources. Do not use inherited conversation, private data, logged-in sessions,
paid APIs, or unpublished provider information.

Evidence cutoff: 2026-08-22.

Question:

> What empirical evidence published or publicly posted by 2026-08-22 measures whether citations
> produced by deep-research agents resolve and actually support the claims made from them?

Find the strongest relevant primary research and authoritative project artifacts within the
cutoff. Do not presuppose success or failure.

For every empirical result, report:

1. exact source URL, title, authors or organization, date, and stable identifier;
2. examined edition, precise locator, and the shortest exact quotation needed to verify it;
3. the source's exact numerator, denominator, rate, comparison, or quantitative basis, using
   `unknown` when unavailable;
4. model, agent, dataset, tool, population, time, and metric scope;
5. relevant failure class: nonexistent URL, non-resolving URL, inaccessible source, irrelevant
   source, duplicate/shared source, or real source supporting a weaker claim;
6. material limitations, counterevidence, and unresolved definitions or artifacts; and
7. primary or official support rather than commentary, snippets, or generated summaries.

Keep verified source facts separate from interpretation. Do not infer independent evidence from
different reports, URLs, agent names, or runtime profiles. Check shared work, edition, span,
upstream citation, data, method, retrieval path, and derivation. Do not generalize to all agents.

Return one JSON object and no Markdown fence. Required top-level keys are `question`, `cutoff`,
`answer`, `results`, `sources`, `counterevidence`, `limitations`, `unresolved`, and `search_notes`.

Every `results` item must have `result_id`, `proposition`, `reported_value`, `scope`, `source_ids`,
`exact_span_ids`, and `interpretation`.

Every `sources` item must have `source_id`, `url`, `title`, `authors_or_org`, `date`, `identifier`,
`edition`, `retrieval_status`, `media_type`, `license`, and `exact_spans`. Every `exact_spans` item
must have `span_id`, `locator`, `quote`, and `supports`.

Use empty arrays for no findings and the literal string `unknown` for requested values you cannot
verify.
