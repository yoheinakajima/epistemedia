# Forensic-editorial design system

Status: implemented public shell and two reviewed dossier interactions.

This system gives Epistemedia the feel of a readable publication joined to an inspectable evidence
docket. The public shell remains useful for the repository corpus; accepted How We Know cases add
source-span, lineage-count, and policy interactions compiled from reviewed dossier data.

## Design principles

1. **Substance enters the first viewport.** Navigation, title, scope, and the first index or source section should appear without a manifesto-sized pause.
2. **Editorial first, forensic on demand.** Serif display type supports reading; monospace labels distinguish paths, identities, policies, and build facts.
3. **A receipt is not the article.** Full catalog, frontier, commit, policy, and compiler identities remain visible in a bounded receipt component rather than dominating the narrative surface.
4. **State is written, not implied.** Live, reserved, experimental, and reproducible states always have text labels. Forest and amber reinforce those labels but never replace them.
5. **Native interaction wins.** Experimental-manifest disclosure uses `details` and `summary`, skip navigation is a real anchor, and focus indicators remain visible without JavaScript.
6. **No decorative epistemology.** Network wallpaper, truth traffic lights, invented source counts, and fabricated findings are out of scope.

## Tokens

The shared shell defines tokens once in `SITE_CSS`:

| Family | Convention |
| --- | --- |
| Paper | warm page, raised sheet, and deeper docket-shadow surfaces |
| Ink | near-black reading text with a quieter muted register |
| Forest | brand, links, accepted structure, and primary rules |
| Amber | qualification, experimental status, focus, and attention |
| Typography | system serif for editorial hierarchy, system sans for prose, monospace for receipts |
| Space | six named increments from compact inline gaps to section separation |
| Rule | one neutral rule color plus stronger ink or forest boundaries |

Display type is deliberately compact: a case title may carry editorial weight, but it must not
delay the finding, controls, or evidence tally below a manifesto-sized first screen. Narrow
viewports reduce both display size and section spacing rather than merely wrapping the desktop
composition.

No external font, image, or tracking dependency is required.

## Components

### Publication shell

The shell supplies a skip link, compact wordmark, named primary navigation, bounded reading width, and source-repository footer. A forest-to-amber top rule is the smallest persistent brand signature.

### Docket card

Bootstrap topic and document cards use an ordinal label, editorial title, short description, and a ruled metadata footer. The ordinal describes position in the compiled index; it is not a dossier or evidentiary identity.

### Topic index and object card

A topic route is a compact catalog index, not a rendered dump of repository Markdown. Its header
states the exact public-object count and number of object kinds; entries are grouped by actual
catalog kind and rendered as responsive cards with one title, a cleaned human summary, and direct
actions for the canonical object, Markdown twin, and exact accepted-commit source file.

Machine identity remains available through a native `details` disclosure. Kind, source path, media
type, object ID, and content digest use the smaller monospace receipt register so they remain
auditable without competing with the title and summary.

Topic cards expose only two compiled navigation relations:

- **Also filed under** means the same exact object is selected by another accepted topic manifest.
- **References in source** means a repository-relative Markdown link resolves to another exact
  disclosure-safe catalog object.

Relation clusters use native `details` disclosures with derived counts. This keeps dense cards
scannable while leaving every compiled interlink available without JavaScript and by keyboard.

These links never imply semantic similarity, evidentiary support, agreement, relevance, or source
independence. External links, fragment-only targets, unsafe traversal, missing paths, non-public
targets, duplicates, and self-links do not become catalog relations. The same relation set is
present in static JSON and the local API, MCP, and CLI topic projections.

### Qualification panel

Experimental lens manifests use an amber rule plus explicit text explaining what is and is not implemented. The native disclosure control works by keyboard and without JavaScript.

### Object sheet

Object pages separate page identity from embedded source content. The compact utility header uses the
same cleaned human summary as its topic card; it never promotes raw Markdown navigation syntax.
The object title is the sole page-level heading, source metadata appears in a smaller monospace
definition list, and headings inside the source are demoted beneath the `Source content` section.

### Projection receipt

The receipt carries the complete reproducibility identity in a compact definition list. Long identifiers wrap without being truncated. Topic receipts add projection and policy IDs; home and status receipts show catalog, frontier, accepted commit, and compiler.

### Evidence tally

Each dossier profile names its own count units. Case 001 separates raw assertions,
participant-data roots, target-comparable roots, unresolved roots, and counterevidence. Case 002
separates captured reports, URL strings, source works, candidate warrants, and unresolved citation
occurrences. Counts are derived from dossier relations and typed ledgers; no displayed total is
maintained as independent marketing copy, and visual similarity never implies interchangeable
units.

### Purpose bridge

The homepage places one short explanatory bridge immediately after the featured dossier. It names
the product move from repeated information to warranted knowledge, illustrates that move with the
accepted case counts, and routes readers to the brief, skeptical view, and evidence docket. It is
not a second hero, marketing manifesto, or generalized philosophical claim. A compact library cue
then routes to Case 002 without displacing Case 001 or advertising unreviewed future work.

### Catalog count language

The substrate summary distinguishes unique catalog objects from topic memberships. An object may
appear in more than one topic, so the compiler derives and labels both totals explicitly; topic
cards describe membership in that topic rather than implying a disjoint partition.

### Evidence-policy switch

Encyclopedia and skeptical views use ordinary links and an accessible named navigation region.
They share the exact dossier and source works while selecting different evaluations and relations.
The current view is stated in text and with `aria-current`, not color alone.

### Exact source x-ray

Each material featured relation opens through native `details` and `summary` controls. The expanded
record exposes the accepted edition, locator, exact span, source-work identity, license treatment,
and content-addressed IDs without JavaScript.

## Responsive and accessibility contract

- representative widths: desktop at `1440 × 900` and mobile at `390 × 844`;
- no horizontal page scrolling, including long content-addressed identities;
- one `h1` per generated HTML page, with embedded source headings below the page hierarchy;
- visible keyboard focus, a first-focus skip link, and an accessible primary-navigation name;
- no status conveyed by color alone;
- useful HTML when JavaScript is absent;
- no unlicensed external typeface or asset.

Automated tests cover structure, identities, tokens, focus and responsive rules, and overflow-sensitive markup. Browser inspection remains required because passing string and DOM assertions is not evidence of good visual hierarchy.

## Implemented dossier interaction

EM-0018 defines the reversible application model, EM-0019 supplies the first independently reviewed
evidence file, and EM-0020 compiles the first real interaction. EM-0029 and EM-0030 add a second,
separately reviewed profile and a deterministic multi-case registry. The implementation deliberately
stops short of client-side text selection, animated dependence graphs, or a universal scoring
system. The distinctive behavior remains the reviewable path from a policy-relative sentence to an
exact span and its lineage.
