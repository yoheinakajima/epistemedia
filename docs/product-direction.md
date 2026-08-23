# Product Direction: How We Know

Status: owner-directed product brief, 2026-08-21.

This document records product and experience direction. It does not amend the constitution, establish protocol semantics, admit factual claims, or authorize a task to evaluate or merge itself. Implementation authority remains in immutable task contracts and accepted repository policy.

## Product decision

Epistemedia's first outward-facing knowledge realm will be presented to people as **How We Know**.

Its scope line is:

> Truth, evidence, knowledge, and information—where they agree, where they differ, and how we can tell.

The realm is about external ideas, arguments, observations, and evidence concerning knowledge. It is not another collection of pages about Epistemedia. The existing self-describing repository realm remains useful operating proof and moves to the Explore and project-documentation surfaces rather than serving as the public front door.

The homepage tagline remains:

> Knowledge that can show its work.

## Verified starting point

The accepted repository and live site already prove several parts of the operating substrate:

- Git-canonical contribution and protected merge behavior;
- deterministic compilation and manifest identity;
- disclosure isolation for excluded private paths;
- shared HTML, Markdown, JSON, API, MCP, and CLI catalog identity;
- public Pages hosting at `https://epistemedia.org` with HTTPS enforced;
- visible catalog, frontier, accepted commit, and compiler receipts.

Before the first reviewed vertical slice, the reader experience remained a bootstrap projection:

- the homepage is a directory of eleven project-self topics;
- public objects are principally repository files represented by path, text, media type, and digest;
- topic pages enumerate included repository artifacts rather than synthesizing a sourced dossier;
- seven lens names exist, but they do not yet produce materially different arguments from the shared object set;
- the visual shell is legible but spacious, generic, and missing a distinctive evidence interaction;
- duplicate topic headings and stale public-status prose undermine finish and trust.

The accepted research dossier and EM-0020 compiler work address that first-vertical-slice gap in
repository source: the homepage leads with an external question, source spans are inspectable,
lineage counts are derived, and two named policies materially differ. Wider coverage, hosted
API/MCP activation, and evidence from real-reader comprehension remain open work. Deployment is
only live when the Pages provider and public routes pass read-back.

## Product promise

A reader should be able to:

1. read a concise, useful account of a question;
2. select a material sentence or clause and inspect the exact source edition and span behind it;
3. distinguish raw mentions from independent evidence lineages;
4. see contradiction, qualification, missing evidence, and unresolved defeaters;
5. switch between at least two named policies and understand why the result changes;
6. carry the same object and projection identities into Markdown, JSON, API, MCP, or CLI use;
7. reproduce the page from its accepted commit, frontier, policy, and compiler receipt.

The stranger test is not "does this look like a documentation site?" It is whether a reader notices that apparently separate support collapses under lineage inspection and can see exactly why.

## First dossier selection

The first selected case is:

> Does repeating misinformation in a correction make it more believable?

Its accepted research packet contains exact source spans, known and unknown lineages,
counterevidence, qualifications, and independent review. The application presents its conclusion
as policy-relative and bounded; the selection does not establish a universal rule about every
repetition, correction, audience, delay, or outcome.

Later research questions and candidate case-file titles include:

1. **When many sources are really one source** — another lineage-collapse case with exact upstream evidence.
2. **Information is not meaning** — distinctions among syntactic information, semantic content, and truth.
3. **When justified true belief still is not knowledge** — luck, defeaters, and responses to Gettier-style cases.
4. **Why repetition can change belief without adding evidence** — a broader conceptual treatment beyond the first correction dossier.
5. **What can an AI responsibly claim to know?** — attribution, retrieval, calibration, memory, and uncertainty.

Future dossiers retain the same admission bar: accessible primary or authoritative sources, exact
spans, defensible license and snapshot treatment, meaningful dependence structure, relevant
counterevidence, and no provenance dead ends. A failed candidate records a negative result rather
than manufacturing a demonstration.

The accepted editorial continuation is recorded separately in
[`editorial/how-we-know-case-roadmap.md`](editorial/how-we-know-case-roadmap.md). It selects an
agent-citation-lineage question for Case 002 only as a future research direction and retains a
multi-case library queue. The Greek and modern conceptual territory behind the product is preserved
in [`editorial/epistemic-vocabulary.md`](editorial/epistemic-vocabulary.md); it is orientation, not a
case, protocol ontology, or substitute for sourced philosophical research.

## Visual direction

The recommended design language is **forensic editorial**: a readable publication combined with an inspectable evidence docket.

Keep:

- warm paper, dark ink, and forest green;
- the existing public tagline;
- restrained typography and visible projection receipts;
- human and machine surfaces compiled from the same public projection.

Add:

- a denser, more compact first viewport;
- source-span highlighting and margin annotations;
- dependence brackets and lineage-collapse summaries;
- dossier numbers, edition labels, and accepted-frontier stamps;
- amber as a qualification or contested-evidence accent;
- status communicated by text and shape, never color alone;
- accessible disclosure controls with useful no-JavaScript fallbacks.

Avoid decorative network animation, generic knowledge-graph wallpaper, unsupported numerical claims, traffic-light "truth" colors, or a giant manifesto hero that delays the first substantive finding.

The distinctive brand behavior is the evidence interaction itself: select a sentence, inspect its source, and watch copied support collapse into its actual lineages.

## Homepage direction

With an accepted dossier, the homepage becomes a compiled findings surface:

1. one featured dossier with a real finding and exact scope;
2. raw mention count beside independent lineage count;
3. unresolved challenges or defeaters;
4. a source-span inspection action;
5. an encyclopedia/skeptical policy switch;
6. a small recent frontier section;
7. an honest coverage line;
8. project and protocol material below the product proof;
9. the catalog/frontier/commit receipt.

Feature selection must be an explicit, versioned input to the compiler. The homepage may be editorially selected through accepted policy, but it must not become manually maintained marketing detached from the public catalog.

## First-release lens policy

Only lenses with observable semantic or selection differences should be promoted as product controls.

The first dossier targets two:

- **Encyclopedia:** the most useful coherent account permitted by the accepted public evidence and named policy.
- **Skeptical:** conclusions restricted or qualified by stronger independence, method, scope, and unresolved-defeater requirements.

Other lens names may remain machine-readable experimental metadata, but the public interface must not imply that seven differentiated products exist before their policies and outputs materially diverge.

## Implementation sequence

1. Correct stale status language, duplicate headings, scope disclosure, and misleading projection affordances.
2. Implement the compact forensic-editorial design system without inventing product evidence.
3. Add a reversible application-level dossier model for source works, editions, spans, propositions, assertions, evidence relations, dependence, and claim families.
4. Research and admit one real lineage-collapse dossier under explicit source, license, span, and review requirements.
5. Compile sentence X-ray, lineage collapse, two real policy views, and the featured homepage from the same dossier objects.
6. Pilot five claim families and measure extraction fidelity, review time, lineage precision, policy divergence, and reader comprehension.
7. Only after the pilot passes, build conversation import, newsletter capture, high-volume extraction, consolidation proposals, hosted API/MCP activation, and broader realm growth.

## Pilot measurements and stop conditions

Measure:

- human-verified span-to-proposition extraction accuracy;
- broken or inaccessible source-span rate;
- sampled precision of asserted same-source and dependence relations;
- minutes, tokens, and reviewer interventions per claim family;
- naive mention count versus independent-lineage count;
- material policy-output differences on a fixed reference set;
- real-reader comprehension of the finding, evidence, and uncertainty;
- public-projection noninterference under private-only fixture mutations.

Stop and improve the extractor or model before scaling when:

- a featured statement lacks an exact inspectable source path;
- lineage grouping cannot be reviewed reliably;
- the two promoted lenses differ mainly in styling or labels;
- most pilot claims collapse to undifferentiated "insufficient evidence";
- the public projection changes when only private fixtures change;
- the median review burden makes a larger seed corpus impractical.

Synthetic usability checks may validate mechanics. Claims about human understanding require real readers.

## Explicit non-goals for the pilot

- a universal theory or ontology of truth;
- general-encyclopedia breadth;
- politics as an early realm;
- public federation or incentive design;
- automatic admission of extracted model output;
- high-volume capture before a reviewed vertical slice;
- activating hosted API or MCP merely because endpoints exist;
- presenting application-level dossier fields as a stable protocol standard;
- replacing the append-only governance, disclosure, and no-self-authorization spine.

## Later documentation

After the first dossier proves the mechanism:

- write a short founding paper centered on page-versus-history, evidence independence, disclosure ordering, contradiction, and no self-authorization;
- add `RELATED.md` covering nanopublications, micropublications, the Underlay, discourse graphs, truth discovery and copying detection, controlled query evaluation, formal argumentation, event sourcing, and agent governance;
- document why earlier systems stalled and which cost or governance assumptions Epistemedia changes;
- register capture, consolidation, extractor benchmarking, and scaled-corpus tasks using measured pilot costs rather than estimates.
