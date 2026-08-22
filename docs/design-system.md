# Forensic-editorial design system

Status: implemented public-shell and first reviewed dossier interaction.

This system gives Epistemedia the feel of a readable publication joined to an inspectable evidence
docket. The public shell remains useful for the repository corpus; the accepted How We Know case
adds real source-span, lineage-count, and policy interactions compiled from reviewed dossier data.

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

No external font, image, or tracking dependency is required.

## Components

### Publication shell

The shell supplies a skip link, compact wordmark, named primary navigation, bounded reading width, and source-repository footer. A forest-to-amber top rule is the smallest persistent brand signature.

### Docket card

Bootstrap topic and document cards use an ordinal label, editorial title, short description, and a ruled metadata footer. The ordinal describes position in the compiled index; it is not a dossier or evidentiary identity.

### Qualification panel

Experimental lens manifests use an amber rule plus explicit text explaining what is and is not implemented. The native disclosure control works by keyboard and without JavaScript.

### Object sheet

Object pages separate page identity from embedded source content. The object title is the sole page-level heading, source metadata appears in a definition list, and headings inside the source are demoted beneath the `Source content` section.

### Projection receipt

The receipt carries the complete reproducibility identity in a compact definition list. Long identifiers wrap without being truncated. Topic receipts add projection and policy IDs; home and status receipts show catalog, frontier, accepted commit, and compiler.

### Evidence tally

The featured case separates raw assertions, participant-data roots, target-comparable roots,
unresolved roots, and counterevidence. Counts are derived from dossier relations and lineage
records; no displayed total is maintained as independent marketing copy.

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

EM-0018 defines the reversible application model, EM-0019 supplies independently reviewed evidence,
and EM-0020 compiles the first real interaction. It deliberately stops short of client-side text
selection, animated dependence graphs, or a universal scoring system. The distinctive behavior is
the reviewable path from a policy-relative sentence to an exact span and its lineage.
