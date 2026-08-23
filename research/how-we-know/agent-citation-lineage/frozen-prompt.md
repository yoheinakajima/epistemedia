# Frozen public trace prompt

You are participating in a disclosure-safe research pilot. Work only from this prompt and public,
credential-free sources. Do not use inherited conversation context, private data, logged-in
sessions, paid APIs, or unpublished provider information.

Research question:

> What empirical evidence published or publicly posted by 2026-08-22 measures whether citations
> produced by deep-research agents resolve and actually support the claims made from them?

Find the strongest relevant primary research and authoritative project artifacts available within
that cutoff. Do not presuppose that agent citations fail or succeed.

For every concrete empirical result you report:

1. give the exact source URL, title, authors or responsible organization, date, and stable
   identifier when available;
2. identify the examined edition and a precise locator;
3. provide the shortest exact source quotation needed to verify the result;
4. state the numerator, denominator, rate, comparison, or other quantitative basis exactly as the
   source reports it, and say `unknown` when it is unavailable;
5. preserve the source's scope, including model, agent, dataset, tool, population, time, and metric;
6. distinguish at least these failure classes when the source does: nonexistent URL, non-resolving
   URL, inaccessible source, irrelevant source, duplicate or shared source, and a real source that
   supports a weaker proposition than the agent asserted;
7. identify material limitations, counterevidence, and unresolved definitions or artifacts; and
8. prefer primary research or official project documentation over commentary, search snippets, or
   model-generated summaries.

Separate verified source facts from your interpretation. Do not count different reports, URLs,
agent names, or runtime profiles as independent evidence without checking whether they share the
same source work, edition, span, upstream citation, data, method, retrieval path, or derivation.
Do not generalize this bounded literature to all agents.

Return one self-contained JSON object with these top-level keys:

`question`, `cutoff`, `answer`, `results`, `sources`, `counterevidence`, `limitations`,
`unresolved`, and `search_notes`.

Each item in `results` must include:

`result_id`, `proposition`, `reported_value`, `scope`, `source_ids`, `exact_span_ids`, and
`interpretation`.

Each item in `sources` must include:

`source_id`, `url`, `title`, `authors_or_org`, `date`, `identifier`, `edition`, `retrieval_status`,
`media_type`, `license`, and `exact_spans`.

Each item in `exact_spans` must include:

`span_id`, `locator`, `quote`, and `supports`.

Use empty arrays for no findings and the literal string `unknown` for requested values you cannot
verify. Output JSON only, without a Markdown fence.
