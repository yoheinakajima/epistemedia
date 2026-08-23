from __future__ import annotations

import hashlib
import html
import json
import os
import posixpath
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote, unquote, urlsplit

VERSION = "0.2.0"
PROTOCOL_VERSION = "2026-07-28"
DEFAULT_BASE_URL = "https://epistemedia.org"
DEFAULT_API_URL = "https://api.epistemedia.org/v1"
DEFAULT_MCP_URL = "https://mcp.epistemedia.org/mcp"

LENSES: dict[str, str] = {
    "encyclopedia": "The current default repository-object projection over the shared inventory.",
    "evidence-first": (
        "Experimental identifier reserved for foregrounding primary evidence; currently uses "
        "the shared inventory."
    ),
    "skeptical": (
        "Experimental identifier reserved for stronger support thresholds; currently uses the "
        "shared inventory."
    ),
    "frontier": (
        "Experimental identifier reserved for open questions and disputes; currently uses the "
        "shared inventory."
    ),
    "historical": (
        "Experimental identifier reserved for time-bounded views; currently uses the shared "
        "inventory."
    ),
    "pedagogical": (
        "Experimental identifier reserved for prerequisite-aware explanations; currently uses "
        "the shared inventory."
    ),
    "source-only": (
        "Experimental identifier reserved for exact-source views; currently uses the shared "
        "inventory."
    ),
}

SITE_CSS = """
:root{
  color-scheme:light;
  --paper:#f3f0e6;
  --paper-raised:#fffdf6;
  --paper-deep:#e9e4d5;
  --ink:#171a15;
  --muted:#5e6259;
  --forest:#274c3a;
  --forest-deep:#163426;
  --amber:#a96512;
  --amber-wash:#f5e4bd;
  --rule:#c9c4b5;
  --code:#e8e4d8;
  --serif:ui-serif,Georgia,Cambria,"Times New Roman",serif;
  --sans:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --space-1:.35rem;
  --space-2:.65rem;
  --space-3:1rem;
  --space-4:1.5rem;
  --space-5:2.25rem;
  --space-6:3.25rem;
  --measure:72ch;
  --page:1180px;
}
*{box-sizing:border-box}
html{background:var(--paper);scroll-padding-top:1rem}
body{
  margin:0;
  border-top:4px solid;
  border-image:linear-gradient(90deg,var(--forest) 0 78%,var(--amber) 78% 100%) 1;
  background:
    linear-gradient(90deg,rgba(39,76,58,.025) 1px,transparent 1px) 0 0/24px 24px,
    var(--paper);
  color:var(--ink);
  font:16px/1.58 var(--sans);
  text-rendering:optimizeLegibility;
}
a{color:var(--forest-deep);text-decoration-thickness:1px;text-underline-offset:3px}
a:hover{text-decoration-thickness:2px}
a:focus-visible,summary:focus-visible{
  outline:3px solid var(--amber);
  outline-offset:4px;
  border-radius:1px;
}
.skip-link{
  position:fixed;
  z-index:10;
  top:.5rem;
  left:.75rem;
  transform:translateY(-180%);
  background:var(--ink);
  color:var(--paper-raised);
  padding:.55rem .8rem;
}
.skip-link:focus{transform:none}
.site-header,main,.site-footer{
  width:min(100% - 2.5rem,var(--page));
  margin-inline:auto;
}
.site-header{
  min-height:62px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:var(--space-3);
  border-bottom:1px solid var(--rule);
}
.brand{
  display:inline-flex;
  align-items:center;
  min-height:44px;
  gap:.55rem;
  color:var(--ink);
  font-weight:760;
  letter-spacing:-.015em;
  text-decoration:none;
}
.brand-mark{
  display:inline-grid;
  place-items:center;
  width:1.85rem;
  height:1.85rem;
  border:1px solid var(--forest);
  background:var(--forest);
  color:var(--paper-raised);
  font:700 .75rem/1 var(--mono);
  letter-spacing:-.08em;
}
nav{display:flex;align-items:center;gap:1.1rem}
nav a{
  display:inline-flex;
  align-items:center;
  min-height:44px;
  color:var(--ink);
  font-size:.82rem;
  font-weight:720;
  letter-spacing:.055em;
  text-decoration:none;
  text-transform:uppercase;
}
nav a:hover{text-decoration:underline}
main{padding-block:0 var(--space-6)}
.site-footer{
  display:grid;
  grid-template-columns:1fr auto;
  gap:var(--space-4);
  padding-block:var(--space-4);
  border-top:1px solid var(--rule);
  color:var(--muted);
  font-size:.83rem;
}
.site-footer p{margin:0}
p,li,blockquote{max-width:var(--measure)}
h1,h2,h3,h4,h5,h6{
  margin:0 0 .55em;
  color:var(--ink);
  font-family:var(--serif);
  line-height:1.04;
  text-wrap:balance;
}
h1{max-width:18ch;font-size:clamp(2.1rem,3.8vw,3.8rem);letter-spacing:-.04em}
h2{font-size:clamp(1.55rem,2.3vw,2.15rem);letter-spacing:-.025em}
h3{font-size:1.28rem}
h4{font-size:1.08rem}
.hero{padding:var(--space-4) 0 var(--space-3);border-bottom:1px solid var(--rule)}
.hero-home{padding-top:clamp(1.5rem,3.5vw,2.75rem)}
.hero-home h1{max-width:14ch}
.hero-compact{padding-bottom:var(--space-3)}
.dek{margin:.35rem 0 var(--space-3);max-width:760px;color:var(--muted);font-size:1.16rem}
.eyebrow,.meta,.docket-number{
  margin:0 0 .65rem;
  color:var(--muted);
  font:700 .72rem/1.35 var(--mono);
  letter-spacing:.085em;
  text-transform:uppercase;
}
.docket-number{color:var(--forest)}
.scope-note{
  display:grid;
  grid-template-columns:auto 1fr;
  gap:.7rem;
  max-width:900px;
  margin:var(--space-3) 0 0;
  padding:.8rem 0 .8rem var(--space-3);
  border-left:4px solid var(--amber);
  background:linear-gradient(90deg,var(--amber-wash),transparent 88%);
}
.scope-note strong{font:700 .72rem/1.55 var(--mono);letter-spacing:.055em;text-transform:uppercase}
.case-hero{padding:var(--space-4) 0;border-bottom:1px solid var(--ink)}
.case-rule{
  display:flex;
  justify-content:space-between;
  gap:var(--space-2);
  padding:.5rem 0;
  border-top:3px solid var(--forest);
  border-bottom:1px solid var(--rule);
  color:var(--muted);
  font:720 .67rem/1.3 var(--mono);
  letter-spacing:.08em;
  text-transform:uppercase;
}
.case-rule a{min-height:0;color:var(--forest-deep);font:inherit;text-decoration:underline}
.case-grid{
  display:grid;
  grid-template-columns:minmax(0,1.28fr) minmax(290px,.72fr);
  gap:var(--space-4);
  padding-top:var(--space-3);
}
.case-copy{min-width:0}
.case-copy h1,.dossier-lead h1{max-width:20ch;font-size:clamp(2rem,3.6vw,3.4rem)}
.finding{
  max-width:66ch;
  margin:var(--space-3) 0;
  padding:.2rem 0 .2rem var(--space-3);
  border-left:4px solid var(--amber);
  color:var(--forest-deep);
  font:600 clamp(1.05rem,1.6vw,1.3rem)/1.5 var(--serif);
}
.case-docket{align-self:end;padding:var(--space-3);border:1px solid var(--ink);background:var(--paper-raised);box-shadow:6px 6px 0 var(--paper-deep)}
.docket-note{margin:var(--space-3) 0;color:var(--muted);font-size:.9rem}
.docket-meta{margin:0;padding-top:.65rem;border-top:1px solid var(--rule);color:var(--muted);font:680 .67rem/1.45 var(--mono);letter-spacing:.025em;text-transform:uppercase}
.policy-switch{display:inline-flex;gap:0;margin:.2rem 0 var(--space-3);border:1px solid var(--forest);background:var(--paper-raised)}
.policy-switch a{min-height:40px;padding:.55rem .85rem;color:var(--forest-deep);font:720 .72rem/1.3 var(--mono);letter-spacing:.055em;text-decoration:none;text-transform:uppercase}
.policy-switch a+a{border-left:1px solid var(--forest)}
.policy-switch a.current{background:var(--forest);color:var(--paper-raised)}
.case-actions,.representation-links{display:flex;align-items:center;flex-wrap:wrap;gap:.7rem 1rem;margin:.25rem 0 0;font-size:.88rem}
.primary-action{display:inline-flex;align-items:center;min-height:44px;padding:.65rem .85rem;background:var(--forest);color:var(--paper-raised);font-weight:750;text-decoration:none}
.primary-action:hover{background:var(--forest-deep)}
.evidence-tally{display:grid;grid-template-columns:1fr auto 1fr 1fr;gap:.55rem;align-items:stretch}
.tally-cell{display:flex;min-width:0;flex-direction:column;justify-content:center;padding:.7rem;border-top:3px solid var(--rule);background:var(--paper)}
a.tally-cell{color:inherit;text-decoration:none}
a.tally-cell:hover{outline:2px solid var(--amber);outline-offset:-2px}
.tally-cell strong{color:var(--ink);font:750 clamp(1.65rem,3vw,2.4rem)/1 var(--serif)}
.tally-cell span{margin-top:.3rem;color:var(--muted);font:650 .65rem/1.35 var(--mono);letter-spacing:.035em;text-transform:uppercase}
.tally-emphasis{border-color:var(--amber);background:var(--amber-wash)}
.tally-counter{border-color:var(--forest)}
.tally-arrow{align-self:center;color:var(--amber);font:700 1.4rem/1 var(--serif)}
.dossier-lead{padding-top:var(--space-3)}
.purpose-note{
  display:grid;
  grid-template-columns:minmax(170px,.32fr) minmax(0,1fr);
  gap:var(--space-5);
  padding:var(--space-4);
  border-top:5px solid var(--forest);
  background:var(--paper-raised);
  box-shadow:6px 6px 0 var(--paper-deep);
}
.purpose-kicker{
  display:flex;
  flex-direction:column;
  justify-content:space-between;
  gap:var(--space-3);
  padding-right:var(--space-3);
  border-right:1px solid var(--rule);
}
.purpose-kicker strong{
  max-width:9ch;
  color:var(--forest-deep);
  font:750 clamp(1.45rem,3vw,2.15rem)/1.02 var(--serif);
  letter-spacing:-.025em;
}
.purpose-kicker span{
  color:var(--muted);
  font:700 .66rem/1.4 var(--mono);
  letter-spacing:.055em;
  text-transform:uppercase;
}
.purpose-copy h2{max-width:34ch;font-size:clamp(1.4rem,2.3vw,2rem);line-height:1.14}
.purpose-copy>p{max-width:67ch;color:var(--muted)}
.purpose-paths{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:1px;
  margin-top:var(--space-3);
  border:1px solid var(--rule);
  background:var(--rule);
}
.purpose-paths a{
  display:grid;
  grid-template-columns:auto 1fr;
  gap:.2rem .65rem;
  min-height:78px;
  padding:.75rem;
  background:var(--paper);
  color:var(--ink);
  font-size:inherit;
  font-weight:inherit;
  letter-spacing:normal;
  text-decoration:none;
  text-transform:none;
}
.purpose-paths a:hover{background:var(--amber-wash)}
.purpose-paths span{grid-row:1/3;color:var(--amber);font:730 .65rem/1.4 var(--mono)}
.purpose-paths strong{font:720 1.05rem/1.2 var(--serif)}
.purpose-paths small{color:var(--muted);font:.72rem/1.35 var(--sans)}
.practical-reading{display:grid;grid-template-columns:180px minmax(0,1fr);gap:var(--space-5);padding:var(--space-4);border-top:6px solid var(--amber);background:var(--forest-deep);color:var(--paper-raised);box-shadow:8px 8px 0 var(--paper-deep)}
.practical-kicker{display:flex;flex-direction:column;gap:.35rem;color:var(--amber-wash);font:720 .68rem/1.4 var(--mono);letter-spacing:.07em;text-transform:uppercase}
.practical-kicker span:first-child{color:var(--paper-raised);font:760 clamp(1.35rem,3vw,2rem)/1 var(--serif);letter-spacing:-.02em;text-transform:none}
.practical-reading h2{max-width:28ch;color:var(--paper-raised);font-size:clamp(1.6rem,3vw,2.55rem);line-height:1.12}
.practical-reading p{max-width:68ch;color:#e6eadf}
.practical-basis{display:flex;align-items:center;flex-wrap:wrap;gap:.35rem;font:650 .72rem/1.5 var(--mono);letter-spacing:.035em;text-transform:uppercase}
.practical-basis a{display:inline-grid;place-items:center;width:2rem;height:2rem;border:1px solid #d7dcca;color:var(--paper-raised);text-decoration:none}
.practical-basis a:hover{background:var(--paper-raised);color:var(--forest-deep)}
.lineage-ledger{padding-top:var(--space-4)}
.lineage-ledger>.evidence-tally{max-width:960px}
.stranger-definition{max-width:62ch;margin:0 0 var(--space-3);font:600 clamp(1.05rem,2vw,1.28rem)/1.48 var(--serif)}
.ledger-groups{display:grid;grid-template-columns:1fr 1fr 1fr;gap:var(--space-3);align-items:start}
.ledger-group{min-width:0;padding:var(--space-3);scroll-margin-top:var(--space-3);border:1px solid var(--rule);border-top:6px solid var(--rule);background:var(--paper-raised)}
.ledger-support{border-top-color:var(--amber);background:linear-gradient(180deg,var(--amber-wash),var(--paper-raised) 13rem)}
.ledger-counter{border-top-color:var(--forest)}
.ledger-number{margin:0;color:var(--forest-deep);font:750 clamp(2.4rem,5vw,4.4rem)/.9 var(--serif);letter-spacing:-.045em}
.ledger-group h3{margin-top:.45rem;font-size:1.35rem}
.ledger-intro{min-height:4.5em;margin:.2rem 0 var(--space-3);color:var(--muted);font-size:.86rem}
.ledger-group ol{margin:0;padding:0;list-style:none;counter-reset:ledger}
.ledger-group li{position:relative;padding:.85rem 0 .85rem 2.1rem;border-top:1px solid var(--rule);counter-increment:ledger}
.ledger-group li:before{position:absolute;left:0;top:.88rem;content:counter(ledger,decimal-leading-zero);color:var(--muted);font:700 .64rem/1.4 var(--mono)}
.ledger-entry-head{display:flex;align-items:start;justify-content:space-between;gap:.5rem}
.ledger-entry-head strong{font:650 .94rem/1.35 var(--serif)}
.ledger-status{flex:0 0 auto;padding:.18rem .28rem;background:var(--amber);color:var(--paper-raised);font:720 .58rem/1.2 var(--mono);letter-spacing:.05em;text-transform:uppercase}
.ledger-group li p{margin:.35rem 0;color:var(--muted);font-size:.79rem;line-height:1.46}
.ledger-group li code{padding:0;background:transparent;color:var(--muted);font-size:.62rem}
.case-lexicon dl{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));margin:0;border-top:1px solid var(--ink);border-bottom:1px solid var(--ink)}
.case-lexicon dl>div{padding:var(--space-3);border-left:1px solid var(--rule)}
.case-lexicon dl>div:first-child{border-left:0}
.case-lexicon dt{color:var(--forest-deep);font:720 .72rem/1.35 var(--mono);letter-spacing:.035em;text-transform:uppercase}
.case-lexicon dd{margin:.55rem 0 0;color:var(--muted);font-size:.82rem;line-height:1.48}
.evidence-record{border-top:1px solid var(--ink)}
.evidence-sentence{display:grid;grid-template-columns:110px minmax(0,1fr);gap:var(--space-4);padding:var(--space-4);scroll-margin-top:var(--space-3);border-bottom:1px solid var(--rule);background:linear-gradient(90deg,rgba(255,253,246,.8),transparent)}
.evidence-sentence:nth-child(even){background:linear-gradient(90deg,var(--paper-deep),transparent 70%)}
.evidence-marker{display:flex;align-items:start;gap:.5rem;flex-direction:column;color:var(--forest-deep);font:720 .66rem/1.35 var(--mono);letter-spacing:.055em;text-transform:uppercase}
.evidence-marker span{display:grid;place-items:center;width:2rem;height:2rem;border:1px solid var(--forest);background:var(--forest);color:var(--paper-raised)}
.material-sentence{margin:0;max-width:64ch;font:600 clamp(1.15rem,2vw,1.48rem)/1.42 var(--serif)}
.relation-note{margin:.65rem 0;color:var(--muted);font-size:.91rem}
.source-xray{margin-top:var(--space-3);border:1px solid var(--rule);background:var(--paper-raised)}
.source-xray summary,.source-register summary{cursor:pointer;padding:.75rem .9rem;color:var(--forest-deep);font:730 .74rem/1.4 var(--mono);letter-spacing:.035em;text-transform:uppercase}
.source-xray[open] summary,.source-register[open] summary{border-bottom:1px solid var(--rule)}
.xray-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:1px;background:var(--rule)}
.xray-source{min-width:0;padding:1rem;background:var(--paper-raised)}
.xray-source h4{font-size:1.05rem;line-height:1.25}
.xray-index,.source-locator{margin:0 0 .45rem;color:var(--muted);font:680 .66rem/1.4 var(--mono);letter-spacing:.04em;text-transform:uppercase}
.xray-source blockquote{color:var(--ink);font-family:var(--serif)}
.xray-meta{display:grid;margin:0}
.xray-meta>div{min-width:0;padding:.45rem 0;border-top:1px solid var(--rule)}
.xray-meta dt{color:var(--muted);font:700 .62rem/1.4 var(--mono);letter-spacing:.05em;text-transform:uppercase}
.xray-meta dd{margin:.12rem 0 0;overflow-wrap:anywhere;word-break:break-word;font-size:.78rem}
.uncertainty-panel{display:grid;grid-template-columns:1.25fr .75fr;gap:var(--space-5);padding:var(--space-4);border-left:5px solid var(--amber);background:var(--amber-wash)}
.uncertainty-panel ul{margin-bottom:0;padding-left:1.1rem}
.source-register{margin-top:var(--space-5);border-top:1px solid var(--ink);border-bottom:1px solid var(--ink)}
.source-register ol{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.35rem var(--space-4);padding:var(--space-3) var(--space-4) var(--space-4);counter-reset:source}
.source-register li{display:grid;grid-template-columns:1fr;min-width:0;padding:.45rem 0;border-bottom:1px solid var(--rule)}
.source-register li span{color:var(--muted);font-size:.76rem}
.realm-intro .dek{max-width:58ch}
.case-index{padding-top:var(--space-4)}
.case-index-row{display:grid;grid-template-columns:95px minmax(0,1fr) auto;gap:var(--space-4);align-items:center;padding:var(--space-4);border:1px solid var(--ink);border-top:5px solid var(--forest);background:var(--paper-raised);box-shadow:6px 6px 0 var(--paper-deep)}
.case-index-number{align-self:start;margin:0;color:var(--forest-deep);font:760 .72rem/1.35 var(--mono);letter-spacing:.07em;text-transform:uppercase}
.case-index-copy h3{margin-bottom:.45rem;font-size:clamp(1.45rem,3vw,2.3rem)}
.case-index-verdict{margin:.2rem 0 .75rem;color:var(--muted);font:600 1.02rem/1.48 var(--serif)}
.case-index-counts{margin:0;font:690 .76rem/1.55 var(--mono);letter-spacing:.02em;text-transform:uppercase}
.case-index-counts strong{color:var(--forest-deep);font-size:1.05rem}
.empty-case-note{margin:var(--space-3) 0 0;padding:.75rem 0 .75rem var(--space-3);border-left:4px solid var(--amber);color:var(--muted)}
.review-decision{display:flex;align-items:center;justify-content:space-between;gap:var(--space-4);padding:var(--space-4);border:1px solid var(--ink);border-left:6px solid var(--forest);background:var(--paper-raised)}
.review-decision h2{font-size:clamp(2rem,4vw,3.4rem);color:var(--forest-deep)}
.review-decision p:last-child{margin-bottom:0}
.review-stamp{flex:0 0 auto;padding:.55rem .7rem;border:2px solid var(--forest);color:var(--forest-deep);font:760 .7rem/1.2 var(--mono);letter-spacing:.08em;text-transform:uppercase}
.review-grid{display:grid;grid-template-columns:1fr 2fr;gap:1px;background:var(--rule);border:1px solid var(--rule)}
.review-grid dl{margin:0;background:var(--paper-raised)}
.review-grid dl>div{padding:.8rem 1rem;border-top:1px solid var(--rule)}
.review-grid dl>div:first-child{border-top:0}
.review-grid dt{color:var(--muted);font:700 .67rem/1.45 var(--mono);letter-spacing:.055em;text-transform:uppercase}
.review-grid dd{margin:.18rem 0 0;overflow-wrap:anywhere;word-break:break-word}
.review-scope{display:grid;grid-template-columns:1fr 1fr;gap:var(--space-5)}
.review-scope>div{padding-top:var(--space-3);border-top:3px solid var(--forest)}
.review-scope>div+div{border-color:var(--amber)}
.review-scope ul{padding-left:1.1rem}
.raw-receipt-link{margin-top:var(--space-4);font-weight:720}
section+section{margin-top:var(--space-5)}
.section-head{
  display:flex;
  align-items:end;
  justify-content:space-between;
  gap:var(--space-3);
  margin-bottom:var(--space-3);
  border-bottom:1px solid var(--ink);
}
.section-head h2{margin-bottom:.45rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,245px),1fr));gap:.75rem}
.card{
  position:relative;
  display:flex;
  min-width:0;
  min-height:190px;
  flex-direction:column;
  padding:1rem;
  border:1px solid var(--rule);
  border-top:3px solid var(--forest);
  border-radius:2px;
  background:rgba(255,253,246,.78);
}
.card h2{font-size:1.28rem;line-height:1.08}
.card>p:not(.card-meta):not(.docket-number){margin:.2rem 0 var(--space-3);color:var(--muted)}
.card-meta{
  display:flex;
  flex-wrap:wrap;
  gap:.35rem .75rem;
  margin:auto 0 0;
  padding-top:.7rem;
  border-top:1px solid var(--rule);
  color:var(--muted);
  font:650 .68rem/1.35 var(--mono);
  letter-spacing:.025em;
}
.card:focus-within{outline:3px solid var(--amber);outline-offset:2px}
.topic-hero{display:grid;grid-template-columns:minmax(0,1fr) auto;column-gap:var(--space-5)}
.topic-hero>.eyebrow,.topic-hero>h1,.topic-hero>.dek{grid-column:1}
.topic-hero h1,.object-page>.hero h1{max-width:24ch;font-size:clamp(1.8rem,2.7vw,2.4rem)}
.topic-count{
  grid-column:2;
  grid-row:1/4;
  align-self:center;
  display:grid;
  min-width:180px;
  margin:0;
  padding:var(--space-3);
  border-left:4px solid var(--forest);
  background:rgba(255,253,246,.7);
  color:var(--muted);
  font:700 .68rem/1.4 var(--mono);
  letter-spacing:.05em;
  text-transform:uppercase;
}
.topic-count strong{color:var(--forest-deep);font:750 2.35rem/.9 var(--serif);letter-spacing:-.04em}
.topic-count span+span{margin-top:.45rem;padding-top:.45rem;border-top:1px solid var(--rule)}
.topic-hero>.representation-links{grid-column:1;margin-top:.15rem}
.topic-index-note{margin:0 0 .45rem;color:var(--muted);font-size:.8rem}
.topic-group+.topic-group{margin-top:var(--space-4)}
.topic-group-head{display:flex;align-items:end;justify-content:space-between;gap:var(--space-3);margin-bottom:.7rem}
.topic-group-head h2{margin:0;font-size:1.45rem}
.topic-group-head p{margin:0;color:var(--muted);font:700 .68rem/1.4 var(--mono);letter-spacing:.05em;text-transform:uppercase}
.topic-object-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr));align-items:start;gap:.75rem}
.topic-object-card{
  display:flex;
  min-width:0;
  flex-direction:column;
  padding:var(--space-3);
  border:1px solid var(--rule);
  border-top:4px solid var(--forest);
  background:rgba(255,253,246,.82);
}
.topic-object-card:focus-within{outline:3px solid var(--amber);outline-offset:2px}
.object-kind{margin:0 0 .45rem;color:var(--forest);font:720 .64rem/1.35 var(--mono);letter-spacing:.075em;text-transform:uppercase}
.topic-object-card h3{margin:0;font-size:1.22rem;line-height:1.16}
.topic-object-card h3 a{text-decoration-thickness:1px}
.object-summary{margin:.65rem 0 var(--space-3);color:var(--muted);font-size:.88rem;line-height:1.5}
.object-actions{display:flex;align-items:center;flex-wrap:wrap;gap:.4rem .8rem;margin:auto 0 0;padding-top:.7rem;border-top:1px solid var(--rule);font-size:.75rem}
.object-actions a{font-weight:680}
.object-actions .object-primary{color:var(--forest-deep);font-weight:780}
.object-relations{margin-top:.75rem;border-top:1px dotted var(--rule)}
.object-relations summary{display:flex;cursor:pointer;justify-content:space-between;gap:.75rem;padding:.55rem 0 .15rem}
.object-relations summary::marker{color:var(--forest)}
.relation-count{color:var(--muted);font:700 .6rem/1.35 var(--mono)}
.relation-label{margin:0;color:var(--muted);font:720 .62rem/1.35 var(--mono);letter-spacing:.065em;text-transform:uppercase}
.relation-links{display:flex;flex-wrap:wrap;gap:.25rem .65rem;margin:.3rem 0 0;padding:0;list-style:none}
.relation-links li{max-width:100%;font-size:.74rem;line-height:1.4}
.object-identity{margin-top:.75rem;border-top:1px solid var(--rule)}
.object-identity summary{cursor:pointer;padding:.65rem 0;color:var(--muted);font:720 .62rem/1.35 var(--mono);letter-spacing:.055em;text-transform:uppercase}
.object-identity dl{display:grid;margin:0;padding:0 0 .35rem}
.object-identity dl>div{display:grid;grid-template-columns:90px minmax(0,1fr);gap:.5rem;padding:.34rem 0;border-top:1px dotted var(--rule)}
.object-identity dt{color:var(--muted);font:700 .57rem/1.4 var(--mono);letter-spacing:.045em;text-transform:uppercase}
.object-identity dd{min-width:0;margin:0;color:var(--muted);font:.64rem/1.45 var(--mono)}
.object-identity code{padding:0;background:transparent;font:inherit;overflow-wrap:anywhere;word-break:break-word}
.object-topic-links{margin-top:var(--space-3);padding:.75rem 0;border-top:1px solid var(--rule)}
.object-topic-links .relation-links{margin-top:.4rem}
.lens-status{
  border:1px solid var(--rule);
  border-left:4px solid var(--amber);
  background:var(--paper-raised);
  padding:.85rem 1rem;
  margin:var(--space-4) 0;
}
.lens-status summary{cursor:pointer;font-weight:760}
.lens-status p:last-child{margin-bottom:0}
.projection-receipt{
  margin-top:var(--space-5);
  border:1px solid var(--ink);
  border-top:5px solid var(--forest);
  background:var(--paper-raised);
  box-shadow:6px 6px 0 var(--paper-deep);
}
.receipt-head{
  display:flex;
  align-items:start;
  justify-content:space-between;
  gap:var(--space-3);
  padding:1rem;
  border-bottom:1px solid var(--rule);
}
.receipt-head h2{margin:0;font-size:1.45rem}
.stamp{
  flex:0 0 auto;
  padding:.35rem .5rem;
  border:2px solid var(--forest);
  color:var(--forest-deep);
  font:750 .65rem/1.2 var(--mono);
  letter-spacing:.08em;
  text-transform:uppercase;
}
.receipt-grid{display:grid;margin:0}
.receipt-grid>div{
  display:grid;
  grid-template-columns:minmax(110px,.22fr) 1fr;
  gap:var(--space-3);
  padding:.7rem 1rem;
  border-top:1px solid var(--rule);
}
.receipt-grid>div:first-child{border-top:0}
.receipt-grid dt{color:var(--muted);font:700 .7rem/1.5 var(--mono);letter-spacing:.06em;text-transform:uppercase}
.receipt-grid dd{min-width:0;margin:0}
.object-facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.5rem 1rem;margin:var(--space-3) 0 0}
.object-facts>div{min-width:0;padding:.55rem 0;border-top:1px solid var(--rule)}
.object-facts dt{color:var(--muted);font:700 .68rem/1.5 var(--mono);letter-spacing:.05em;text-transform:uppercase}
.object-facts dd{margin:.2rem 0 0;color:var(--muted);font:.72rem/1.5 var(--mono);overflow-wrap:anywhere;word-break:break-word}
.object-facts code{padding:0;background:transparent;font:inherit}
.source-document{padding-top:var(--space-4)}
.source-document>h2{padding-bottom:.45rem;border-bottom:1px solid var(--ink)}
.status-list{border-top:1px solid var(--ink)}
.status-row{display:grid;grid-template-columns:150px 1fr auto;gap:var(--space-3);align-items:start;padding:.8rem 0;border-bottom:1px solid var(--rule)}
.status-name{font-weight:750}
.status-value{min-width:0;overflow-wrap:anywhere;word-break:break-word}
.status-label{font:750 .66rem/1.3 var(--mono);letter-spacing:.06em;text-transform:uppercase}
.status-live{color:var(--forest-deep)}
.status-reserved{color:#704406}
code,pre{background:var(--code);font-family:var(--mono)}
code{padding:.1rem .28rem;border-radius:2px;overflow-wrap:anywhere;word-break:break-word}
pre{max-width:100%;padding:1rem;overflow:auto;border:1px solid var(--rule);border-radius:2px}
pre code{padding:0;overflow-wrap:normal;word-break:normal}
blockquote{margin-left:0;padding:.35rem 0 .35rem 1rem;border-left:4px solid var(--amber);color:var(--muted)}
.manifest{border-top:1px solid var(--rule);margin-top:var(--space-5);padding-top:var(--space-3)}
@media (max-width:640px){
  .site-header,main,.site-footer{width:min(100% - 2rem,var(--page))}
  .site-header{min-height:58px;gap:.65rem}
  .brand{font-size:.9rem}
  .brand-mark{width:1.65rem;height:1.65rem}
  nav{gap:.7rem}
  nav a{font-size:.68rem}
  h1{font-size:clamp(1.9rem,8.2vw,2.5rem)}
  .hero{padding:1.25rem 0 .9rem}
  .hero-home{padding-top:1.5rem}
  .case-hero{padding:var(--space-3) 0}
  .case-rule{flex-wrap:wrap;justify-content:flex-start}
  .case-rule span+span:before{content:"/";margin-right:.55rem;color:var(--amber)}
  .case-grid{grid-template-columns:1fr;gap:var(--space-3);padding-top:var(--space-3)}
  .case-copy h1,.dossier-lead h1{font-size:clamp(1.9rem,8.2vw,2.5rem)}
  .case-docket{box-shadow:4px 4px 0 var(--paper-deep)}
  .purpose-note{
    grid-template-columns:1fr;
    gap:var(--space-3);
    padding:var(--space-3);
    box-shadow:4px 4px 0 var(--paper-deep);
  }
  .purpose-kicker{
    align-items:end;
    flex-direction:row;
    padding:0 0 var(--space-2);
    border-right:0;
    border-bottom:1px solid var(--rule);
  }
  .purpose-paths{grid-template-columns:1fr}
  .purpose-paths a{min-height:64px}
  .policy-switch{display:flex;width:100%}
  .policy-switch a{flex:1;justify-content:center}
  .evidence-tally{grid-template-columns:1fr 1fr}
  .tally-arrow{display:none}
  .tally-counter{grid-column:1/-1}
  .practical-reading{grid-template-columns:1fr;gap:var(--space-3);padding:var(--space-3);box-shadow:4px 4px 0 var(--paper-deep)}
  .practical-kicker{flex-direction:row;justify-content:space-between}
  .ledger-groups{grid-template-columns:1fr}
  .ledger-intro{min-height:0}
  .case-lexicon dl{grid-template-columns:1fr}
  .case-lexicon dl>div{border-left:0;border-top:1px solid var(--rule)}
  .case-lexicon dl>div:first-child{border-top:0}
  .evidence-sentence{grid-template-columns:1fr;gap:.75rem}
  .evidence-marker{align-items:center;flex-direction:row}
  .uncertainty-panel{grid-template-columns:1fr;gap:var(--space-3);padding:var(--space-3)}
  .source-register ol{grid-template-columns:1fr;padding-inline:var(--space-3)}
  .case-index-row{grid-template-columns:1fr;gap:var(--space-2);padding:var(--space-3);box-shadow:4px 4px 0 var(--paper-deep)}
  .case-index-row .primary-action{justify-self:start}
  .review-decision{align-items:flex-start;flex-direction:column}
  .review-grid,.review-scope{grid-template-columns:1fr}
  .scope-note{grid-template-columns:1fr;gap:.15rem}
  .section-head{align-items:start;flex-direction:column;gap:0}
  .card{min-height:0}
  .topic-hero{grid-template-columns:1fr}
  .topic-hero>.eyebrow,.topic-hero>h1,.topic-hero>.dek,.topic-count,.topic-hero>.representation-links{grid-column:1;grid-row:auto}
  .topic-hero h1,.object-page>.hero h1{font-size:clamp(1.7rem,7vw,2rem)}
  .topic-count{min-width:0;margin-top:.2rem}
  .topic-object-card{padding:.9rem}
  .object-identity dl>div{grid-template-columns:1fr;gap:.1rem}
  .receipt-head{align-items:stretch;flex-direction:column}
  .stamp{align-self:start}
  .receipt-grid>div{grid-template-columns:1fr;gap:.2rem}
  .object-facts{grid-template-columns:1fr}
  .status-row{grid-template-columns:1fr;gap:.2rem}
  .status-label{justify-self:start}
  .site-footer{grid-template-columns:1fr}
}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
""".strip()

TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".toml",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".css",
    ".html",
    ".xml",
    ".csv",
    ".sql",
    ".sh",
}

IGNORED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "generated",
    "dist",
    "build",
}

PUBLIC_ROOTS = {
    "README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "LICENSE",
    "constitution",
    "policies",
    "schemas",
    "docs",
    "tasks",
    "governance",
    "research",
    "releases",
    "src",
    "tests",
    ".github",
    "catalog",
    "pyproject.toml",
    "Makefile",
    "Dockerfile",
    "compose.yaml",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical_json(value).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def stable_id(kind: str, value: Any) -> str:
    return f"em:{kind}:sha256:{digest(value)}"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def accepted_commit(root: Path) -> str:
    """Return Git HEAD or a validated immutable build-time fallback."""
    value = git_value(root, "rev-parse", "HEAD", default="")
    if value:
        return value
    value = os.environ.get("EPISTEMEDIA_ACCEPTED_COMMIT", "")
    if not value:
        return "unknown"
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise ValueError("accepted commit must be exactly 40 lowercase hexadecimal characters")
    return value


def accepted_timestamp(root: Path) -> str:
    """Return the accepted commit time used by reproducible public projections."""
    value = git_value(root, "show", "-s", "--format=%ct", "HEAD", default="")
    if not value:
        value = os.environ.get("SOURCE_DATE_EPOCH", "0")
    if re.fullmatch(r"0|[1-9][0-9]*", value) is None:
        raise ValueError("accepted source timestamp must be non-negative Unix epoch seconds")
    try:
        accepted = datetime.fromtimestamp(int(value), timezone.utc)
    except (OverflowError, OSError, ValueError) as exc:
        raise ValueError("accepted source timestamp is outside the supported range") from exc
    return accepted.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_value(root: Path, *args: str, default: str = "unknown") -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return default


def title_from_path(path: str) -> str:
    name = Path(path).stem.replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", name).strip().title() or path


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def first_paragraph(text: str, limit: int = 320) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    for paragraph in paragraphs:
        if paragraph and not paragraph.startswith("#") and not paragraph.startswith("|"):
            return paragraph[:limit]
    return ""


def human_summary(obj: PublicObject, limit: int = 240) -> str:
    """Return a compact prose summary without leaking Markdown link destinations."""

    if obj.media_type not in {"text/markdown", "text/plain"}:
        return f"Accepted {obj.kind.replace('-', ' ')} in the public catalog."
    text = re.sub(r"```.*?```", "", obj.text, flags=re.S)
    value = ""
    for paragraph in re.split(r"\n\s*\n", text):
        lines = [line for line in paragraph.splitlines() if line.strip()]
        if not lines or all(re.match(r"^\s*#{1,6}\s", line) for line in lines):
            continue
        linked_list_lines = sum(
            bool(re.match(r"^\s*[-+*]\s+\[[^]]+\]\(", line)) for line in lines
        )
        if linked_list_lines and linked_list_lines == len(lines):
            continue
        if all(line.lstrip().startswith("|") for line in lines):
            continue
        value = paragraph
        break
    value = re.sub(r"(?m)^\s*>\s?", "", value)
    value = re.sub(r"(?m)^\s*#{1,6}\s+", "", value)
    value = re.sub(r"!\[([^]]*)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"<((?:https?|mailto):[^>]+)>", r"\1", value)
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = value.replace("**", "").replace("__", "").replace("*", "")
    value = re.sub(r"^\s*(?:[-+] |\d+[.)] )", "", value)
    value = re.sub(r"\s+", " ", value).strip(" #-\t")
    if not value:
        return f"Accepted {obj.kind.replace('-', ' ')} in the public catalog."
    if len(value) <= limit:
        return value
    shortened = value[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return (shortened or value[: limit - 1]).rstrip() + "…"


MARKDOWN_LINK_RE = re.compile(
    r"(?<!!)\[[^\]]+\]\(\s*(?:<(?P<angled>[^>]+)>|(?P<plain>[^\s)]+))"
)


def repository_markdown_targets(source_path: str, text: str) -> list[str]:
    """Resolve safe repository-relative Markdown links against one source path."""

    without_fences = re.sub(r"```.*?```", "", text, flags=re.S)
    without_code = re.sub(r"`[^`]*`", "", without_fences)
    source_dir = PurePosixPath(source_path).parent.as_posix()
    targets: list[str] = []
    seen: set[str] = set()
    for match in MARKDOWN_LINK_RE.finditer(without_code):
        raw_target = (match.group("angled") or match.group("plain") or "").strip()
        parsed = urlsplit(raw_target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        decoded = unquote(parsed.path)
        if decoded.startswith("/") or "\\" in decoded or "\x00" in decoded:
            continue
        joined = posixpath.normpath(posixpath.join(source_dir, decoded))
        if joined in {"", ".", ".."} or joined.startswith("../"):
            continue
        if joined not in seen:
            seen.add(joined)
            targets.append(joined)
    return targets


def safe_slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "item"


def static_object_file_key(object_id: str) -> str:
    """Return a cross-platform filename for a protocol object ID."""
    return quote(object_id, safe="")


def static_object_route_key(object_id: str) -> str:
    """Encode the filename for one URL-decoding pass by a static host."""
    return quote(static_object_file_key(object_id), safe="")


def is_public_source(root: Path, path: Path) -> bool:
    rel = path.relative_to(root)
    if not rel.parts:
        return False
    if any(part in IGNORED_PARTS or part.startswith(".") and part != ".github" for part in rel.parts):
        return False
    first = rel.parts[0]
    return first in PUBLIC_ROOTS and path.suffix.lower() in TEXT_SUFFIXES or str(rel) in PUBLIC_ROOTS


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


@dataclass(frozen=True)
class PublicObject:
    id: str
    kind: str
    path: str
    title: str
    media_type: str
    content_digest: str
    text: str
    summary: str
    visibility: str = "public"
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self, include_text: bool = True) -> dict[str, Any]:
        value: dict[str, Any] = {
            "id": self.id,
            "kind": self.kind,
            "path": self.path,
            "title": self.title,
            "media_type": self.media_type,
            "content_digest": self.content_digest,
            "summary": self.summary,
            "visibility": self.visibility,
            "metadata": self.metadata,
        }
        if include_text:
            value["text"] = self.text
        return value


@dataclass(frozen=True)
class Topic:
    slug: str
    title: str
    description: str
    include: tuple[str, ...]
    tags: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "include": list(self.include),
            "tags": list(self.tags),
        }


@dataclass
class PublicCatalog:
    root: Path
    commit: str
    frontier: str
    objects: list[PublicObject]
    topics: list[Topic]
    policies: dict[str, Any]
    catalog_id: str
    generated_at: str

    @classmethod
    def build(cls, root: Path) -> "PublicCatalog":
        root = root.resolve()
        objects: list[PublicObject] = []
        for path in sorted(root.rglob("*")):
            if not path.is_file() or not is_public_source(root, path):
                continue
            rel = path.relative_to(root).as_posix()
            text = read_text(path)
            media_type = media_type_for(path)
            content_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            identity = {
                "path": rel,
                "content_digest": content_digest,
                "media_type": media_type,
            }
            kind = object_kind(rel)
            obj = PublicObject(
                id=stable_id(kind, identity),
                kind=kind,
                path=rel,
                title=first_heading(text, title_from_path(rel)),
                media_type=media_type,
                content_digest=content_digest,
                text=text,
                summary=first_paragraph(text),
                metadata={"source": "repository", "path": rel},
            )
            objects.append(obj)

        topics = load_topics(root, objects)
        policies = load_policies(root)
        commit = accepted_commit(root)
        # Frontier is accepted content, not a deploy URL or build timestamp.
        frontier_material = {
            "commit": commit,
            "objects": sorted((o.id, o.content_digest) for o in objects),
            "policies": policies,
            "topics": [topic.as_dict() for topic in topics],
        }
        frontier = stable_id("frontier", frontier_material)
        catalog_material = {
            "frontier": frontier,
            "object_ids": sorted(o.id for o in objects),
            "topic_slugs": sorted(t.slug for t in topics),
            "lens_versions": sorted(LENSES),
            "compiler": VERSION,
        }
        return cls(
            root=root,
            commit=commit,
            frontier=frontier,
            objects=objects,
            topics=topics,
            policies=policies,
            catalog_id=stable_id("catalog", catalog_material),
            generated_at=accepted_timestamp(root),
        )

    def object_map(self) -> dict[str, PublicObject]:
        return {obj.id: obj for obj in self.objects}

    def topic_map(self) -> dict[str, Topic]:
        return {topic.slug: topic for topic in self.topics}

    def selected_objects(self, topic: Topic) -> list[PublicObject]:
        selected: list[PublicObject] = []
        for obj in self.objects:
            if any(path_match(obj.path, pattern) for pattern in topic.include):
                selected.append(obj)
        return selected

    def topic_membership_count(self) -> int:
        """Count object-to-topic memberships without implying object distinctness."""

        return sum(len(self.selected_objects(topic)) for topic in self.topics)

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        terms = [term for term in re.findall(r"[a-z0-9]+", query.lower()) if len(term) > 1]
        if not terms:
            return []
        scored: list[tuple[float, PublicObject]] = []
        for obj in self.objects:
            hay_title = obj.title.lower()
            hay_path = obj.path.lower()
            hay_text = obj.text.lower()
            score = 0.0
            for term in terms:
                score += 8.0 * hay_title.count(term)
                score += 4.0 * hay_path.count(term)
                score += min(10, hay_text.count(term))
            if score:
                scored.append((score, obj))
        scored.sort(key=lambda pair: (-pair[0], pair[1].path))
        return [
            {
                "score": score,
                "id": obj.id,
                "title": obj.title,
                "path": obj.path,
                "kind": obj.kind,
                "summary": obj.summary,
            }
            for score, obj in scored[:limit]
        ]

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": "https://epistemedia.com/schemas/public-catalog-v1.json",
            "catalog_id": self.catalog_id,
            "frontier": self.frontier,
            "commit": self.commit,
            "compiler": f"epistemedia/{VERSION}",
            "generated_at": self.generated_at,
            "object_count": len(self.objects),
            "topic_count": len(self.topics),
            "objects": [obj.as_dict(include_text=False) for obj in self.objects],
            "topics": [topic.as_dict() for topic in self.topics],
            "lenses": LENSES,
            "policies": self.policies,
        }


def media_type_for(path: Path) -> str:
    return {
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".json": "application/json",
        ".jsonl": "application/x-ndjson",
        ".yaml": "application/yaml",
        ".yml": "application/yaml",
        ".toml": "application/toml",
        ".py": "text/x-python",
        ".js": "text/javascript",
        ".ts": "text/typescript",
        ".tsx": "text/tsx",
        ".jsx": "text/jsx",
        ".css": "text/css",
        ".html": "text/html",
        ".xml": "application/xml",
        ".csv": "text/csv",
        ".sql": "text/x-sql",
        ".sh": "text/x-shellscript",
    }.get(path.suffix.lower(), "text/plain")


def object_kind(path: str) -> str:
    first = path.split("/", 1)[0]
    return {
        "constitution": "constitution",
        "policies": "policy",
        "schemas": "schema",
        "tasks": "task",
        "governance": "governance-record",
        "research": "research-note",
        "releases": "release",
        "src": "implementation",
        "tests": "test",
        "docs": "documentation",
        "catalog": "catalog-source",
        ".github": "automation",
    }.get(first, "repository-artifact")


def path_match(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-3])
    if pattern.endswith("/*"):
        prefix = pattern[:-2]
        return path.startswith(prefix + "/") and "/" not in path[len(prefix) + 1 :]
    if "*" in pattern:
        regex = "^" + re.escape(pattern).replace(r"\*\*", ".*").replace(r"\*", "[^/]*") + "$"
        return bool(re.match(regex, path))
    return path == pattern or path.startswith(pattern.rstrip("/") + "/")


def load_topics(root: Path, objects: list[PublicObject]) -> list[Topic]:
    path = root / "catalog" / "topics.json"
    topics: list[Topic] = []
    if path.exists():
        try:
            raw = json.loads(path.read_text())
            for item in raw.get("topics", raw if isinstance(raw, list) else []):
                topics.append(
                    Topic(
                        slug=safe_slug(item["slug"]),
                        title=item["title"],
                        description=item.get("description", ""),
                        include=tuple(item.get("include", [])),
                        tags=tuple(item.get("tags", [])),
                    )
                )
        except Exception as exc:
            raise ValueError(f"invalid catalog/topics.json: {exc}") from exc
    if not topics:
        defaults = [
            ("project", "Epistemedia", "The public project, implementation, and operating state.", ("README.md", "docs/**", "src/**")),
            ("governance", "Governance", "Constitutional and policy machinery for autonomous contribution.", ("constitution/**", "policies/**", "governance/**")),
            ("protocol", "Epistemic Mesh Protocol", "Event, provenance, federation, and projection contracts.", ("schemas/**", "docs/**")),
            ("agents", "Agent Operations", "How agents orient, select, execute, validate, and hand off work.", ("AGENTS.md", "tasks/**", "docs/agent-ops/**")),
        ]
        topics = [Topic(slug, title, desc, include) for slug, title, desc, include in defaults]
    # Keep topics that resolve to at least one public object; deterministic order.
    result = []
    for topic in sorted(topics, key=lambda t: t.slug):
        if any(any(path_match(obj.path, p) for p in topic.include) for obj in objects):
            result.append(topic)
    return result


def load_policies(root: Path) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "epistemic": "commons-balanced-v0.1",
        "disclosure": "public-v0.1",
        "selection": "repository-public-v0.1",
        "compiler": f"epistemedia/{VERSION}",
    }
    manifest = root / "policies" / "manifest.json"
    if manifest.exists():
        try:
            defaults.update(json.loads(manifest.read_text()))
        except Exception as exc:
            raise ValueError(f"invalid policies/manifest.json: {exc}") from exc
    return defaults


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def html_shell(
    title: str,
    body: str,
    *,
    base_url: str,
    canonical_url: str,
    markdown_url: str | None = None,
    social_image_url: str | None = None,
) -> str:
    alternates = ""
    if markdown_url:
        alternates = f'<link rel="alternate" type="text/markdown" href="{html.escape(markdown_url)}">'
    social_meta = ""
    if social_image_url:
        social_meta = (
            f'<meta property="og:image" content="{html.escape(social_image_url)}">'
            '<meta name="twitter:card" content="summary_large_image">'
        )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · Epistemedia</title>
<meta name="description" content="Knowledge that can show its work.">
<link rel="canonical" href="{html.escape(canonical_url)}">
<link rel="describedby" href="{html.escape(base_url)}/llms.txt">
{alternates}
{social_meta}
<style>{SITE_CSS}</style>
</head>
<body>
<a class="skip-link" href="#content">Skip to content</a>
<header class="site-header">
  <a class="brand" href="{html.escape(base_url)}/" aria-label="Epistemedia home"><span class="brand-mark" aria-hidden="true">E/</span><span>Epistemedia</span></a>
  <nav aria-label="Primary"><a href="{html.escape(base_url)}/how-we-know/">How We Know</a><a href="{html.escape(base_url)}/explore/">Substrate</a><a href="{html.escape(base_url)}/docs/">Docs</a><a href="{html.escape(base_url)}/status/">Status</a></nav>
</header>
<main id="content" tabindex="-1">{body}</main>
<footer class="site-footer"><p><strong>Knowledge that can show its work.</strong><br>Human and agent interfaces compile from one public projection.</p><p><a href="https://github.com/yoheinakajima/epistemedia">Source repository</a></p></footer>
</body></html>
"""


def md_to_html(text: str, *, heading_offset: int = 0) -> str:
    # Small deterministic renderer. It deliberately supports a conservative Markdown subset.
    lines = text.splitlines()
    out: list[str] = []
    in_code = False
    code: list[str] = []
    in_list = False
    for line in lines:
        if line.startswith("```"):
            if in_code:
                out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
                code = []
                in_code = False
            else:
                if in_list:
                    out.append("</ul>")
                    in_list = False
                in_code = True
            continue
        if in_code:
            code.append(line)
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            level = min(6, len(heading.group(1)) + heading_offset)
            out.append(f"<h{level}>{inline_md(heading.group(2))}</h{level}>")
        elif line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline_md(line[2:])}</li>")
        elif not line.strip():
            if in_list:
                out.append("</ul>")
                in_list = False
        elif line.startswith("> "):
            out.append(f"<blockquote>{inline_md(line[2:])}</blockquote>")
        elif line.startswith("|"):
            out.append(f"<pre>{html.escape(line)}</pre>")
        else:
            out.append(f"<p>{inline_md(line)}</p>")
    if in_list:
        out.append("</ul>")
    if in_code:
        out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
    return "\n".join(out)


def inline_md(value: str) -> str:
    escaped = html.escape(value)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
    return escaped


def accepted_source_url(catalog: PublicCatalog, obj: PublicObject) -> str:
    path = quote(obj.path, safe="/")
    return (
        "https://github.com/yoheinakajima/epistemedia/blob/"
        f"{quote(catalog.commit, safe='')}/{path}"
    )


def object_topic_memberships(
    catalog: PublicCatalog,
    obj: PublicObject,
    base_url: str,
    *,
    exclude_slug: str | None = None,
) -> list[dict[str, str]]:
    memberships = []
    for candidate in catalog.topics:
        if candidate.slug == exclude_slug:
            continue
        if any(path_match(obj.path, pattern) for pattern in candidate.include):
            memberships.append(
                {
                    "slug": candidate.slug,
                    "title": candidate.title,
                    "url": f"{base_url.rstrip('/')}/topics/{candidate.slug}/",
                }
            )
    return memberships


def object_source_references(
    catalog: PublicCatalog, obj: PublicObject, base_url: str
) -> list[dict[str, str]]:
    if obj.media_type != "text/markdown":
        return []
    objects_by_path = {candidate.path: candidate for candidate in catalog.objects}
    references = []
    for target_path in repository_markdown_targets(obj.path, obj.text):
        target = objects_by_path.get(target_path)
        if target is None or target.id == obj.id:
            continue
        route_key = static_object_route_key(target.id)
        references.append(
            {
                "id": target.id,
                "title": target.title,
                "kind": target.kind,
                "path": target.path,
                "html_url": f"{base_url.rstrip('/')}/objects/{route_key}/",
                "markdown_url": f"{base_url.rstrip('/')}/objects/{route_key}.md",
            }
        )
    return references


def topic_object_record(
    catalog: PublicCatalog, obj: PublicObject, topic: Topic, base_url: str
) -> dict[str, Any]:
    value = obj.as_dict(include_text=False)
    route_key = static_object_route_key(obj.id)
    value["summary"] = human_summary(obj)
    value["links"] = {
        "html": f"{base_url.rstrip('/')}/objects/{route_key}/",
        "markdown": f"{base_url.rstrip('/')}/objects/{route_key}.md",
        "accepted_source": accepted_source_url(catalog, obj),
    }
    value["also_filed_under"] = object_topic_memberships(
        catalog, obj, base_url, exclude_slug=topic.slug
    )
    value["references_in_source"] = object_source_references(catalog, obj, base_url)
    return value


def topic_projection(catalog: PublicCatalog, topic: Topic, lens: str, base_url: str) -> dict[str, Any]:
    selected = catalog.selected_objects(topic)
    objects = [topic_object_record(catalog, obj, topic, base_url) for obj in selected]
    relation_material = [
        {
            "id": obj["id"],
            "also_filed_under": [item["slug"] for item in obj["also_filed_under"]],
            "references_in_source": [item["id"] for item in obj["references_in_source"]],
        }
        for obj in objects
    ]
    manifest_material = {
        "catalog_id": catalog.catalog_id,
        "frontier": catalog.frontier,
        "topic": topic.slug,
        "lens": lens,
        "policies": catalog.policies,
        "objects": relation_material,
        "compiler": VERSION,
    }
    projection_id = stable_id("projection", manifest_material)
    kind_counts = [
        {"kind": kind, "count": sum(obj["kind"] == kind for obj in objects)}
        for kind in sorted({obj["kind"] for obj in objects})
    ]
    route = f"topics/{topic.slug}/"
    if lens != "encyclopedia":
        route += f"{lens}/"
    route_url = f"{base_url.rstrip('/')}/{route}"
    return {
        "projection_id": projection_id,
        "catalog_id": catalog.catalog_id,
        "frontier": catalog.frontier,
        "topic": topic.as_dict(),
        "lens": {"id": lens, "description": LENSES[lens]},
        "policies": catalog.policies,
        "compiler": f"epistemedia/{VERSION}",
        "commit": catalog.commit,
        "generated_at": catalog.generated_at,
        "base_url": base_url,
        "object_count": len(objects),
        "kind_counts": kind_counts,
        "relation_counts": {
            "also_filed_under": sum(len(obj["also_filed_under"]) for obj in objects),
            "references_in_source": sum(len(obj["references_in_source"]) for obj in objects),
        },
        "representations": {
            "html": route_url,
            "markdown": f"{route_url}index.md",
            "json": f"{route_url}index.json",
        },
        "objects": objects,
    }


def projection_markdown(
    projection: dict[str, Any], *, include_topic_intro: bool = True, include_manifest: bool = True
) -> str:
    topic = projection["topic"]
    lines = []
    if include_topic_intro:
        lines += [
            f"# {topic['title']}",
            "",
            topic.get("description", ""),
            "",
        ]
    lines += [
        f"**Lens:** `{projection['lens']['id']}` — {projection['lens']['description']}",
        "",
        "**Lens status:** Experimental manifest. Current lens policies preserve the same included-object inventory; the label does not yet indicate a materially differentiated editorial result.",
        "",
        f"**Inventory:** {projection['object_count']} public objects across {len(projection['kind_counts'])} object kinds.",
        "",
        (
            f"[HTML]({projection['representations']['html']}) · "
            f"[Markdown]({projection['representations']['markdown']}) · "
            f"[JSON]({projection['representations']['json']})"
        ),
        "",
        "## Objects",
        "",
    ]
    for group in projection["kind_counts"]:
        lines += [
            f"### {group['kind'].replace('-', ' ').title()} ({group['count']})",
            "",
        ]
        for obj in (item for item in projection["objects"] if item["kind"] == group["kind"]):
            links = obj["links"]
            lines += [
                f"#### [{obj['title']}]({links['html']})",
                "",
                obj["summary"],
                "",
                (
                    f"[Open object]({links['html']}) · "
                    f"[Markdown twin]({links['markdown']}) · "
                    f"[Accepted source]({links['accepted_source']})"
                ),
                "",
            ]
            if obj["also_filed_under"]:
                labels = ", ".join(
                    f"[{item['title']}]({item['url']})" for item in obj["also_filed_under"]
                )
                lines += [f"**Also filed under:** {labels}", ""]
            if obj["references_in_source"]:
                labels = ", ".join(
                    f"[{item['title']}]({item['html_url']})"
                    for item in obj["references_in_source"]
                )
                lines += [f"**References in source:** {labels}", ""]
            lines += [
                "<details>",
                "<summary>Technical identity</summary>",
                "",
                f"- Kind: `{obj['kind']}`",
                f"- Source path: `{obj['path']}`",
                f"- Media type: `{obj['media_type']}`",
                f"- Object ID: `{obj['id']}`",
                f"- Content digest: `{obj['content_digest']}`",
                "",
                "</details>",
                "",
            ]
    if include_manifest:
        lines += [
            "## Projection manifest",
            "",
            f"- Projection: `{projection['projection_id']}`",
            f"- Catalog: `{projection['catalog_id']}`",
            f"- Evidence frontier: `{projection['frontier']}`",
            f"- Accepted commit: `{projection['commit']}`",
            f"- Epistemic policy: `{projection['policies']['epistemic']}`",
            f"- Disclosure policy: `{projection['policies']['disclosure']}`",
            f"- Compiler: `{projection['compiler']}`",
        ]
    return "\n".join(lines).strip() + "\n"


def topic_projection_html(projection: dict[str, Any], lens_links: str) -> str:
    topic = projection["topic"]
    representations = projection["representations"]
    groups = []
    for group in projection["kind_counts"]:
        cards = []
        objects = [obj for obj in projection["objects"] if obj["kind"] == group["kind"]]
        for obj in objects:
            links = obj["links"]
            relations = []
            if obj["also_filed_under"]:
                relation_links = "".join(
                    f'<li><a href="{html.escape(item["url"])}">'
                    f'{html.escape(item["title"])}</a></li>'
                    for item in obj["also_filed_under"]
                )
                relations.append(
                    '<details class="object-relations"><summary>'
                    '<span class="relation-label">Also filed under</span>'
                    f'<span class="relation-count">{len(obj["also_filed_under"])}</span>'
                    f'</summary><ul class="relation-links">{relation_links}</ul></details>'
                )
            if obj["references_in_source"]:
                reference_links = "".join(
                    f'<li><a href="{html.escape(item["html_url"])}">'
                    f'{html.escape(item["title"])}</a></li>'
                    for item in obj["references_in_source"]
                )
                relations.append(
                    '<details class="object-relations"><summary>'
                    '<span class="relation-label">References in source</span>'
                    f'<span class="relation-count">{len(obj["references_in_source"])}</span>'
                    f'</summary><ul class="relation-links">{reference_links}</ul></details>'
                )
            identity_rows = "".join(
                f"<div><dt>{label}</dt><dd><code>{html.escape(str(value))}</code></dd></div>"
                for label, value in (
                    ("Kind", obj["kind"]),
                    ("Source path", obj["path"]),
                    ("Media type", obj["media_type"]),
                    ("Object ID", obj["id"]),
                    ("Content digest", obj["content_digest"]),
                )
            )
            cards.append(
                '<article class="topic-object-card">'
                f'<p class="object-kind">{html.escape(obj["kind"].replace("-", " "))}</p>'
                f'<h3><a href="{html.escape(links["html"])}">{html.escape(obj["title"])}</a></h3>'
                f'<p class="object-summary">{html.escape(obj["summary"])}</p>'
                '<p class="object-actions">'
                f'<a class="object-primary" href="{html.escape(links["html"])}">Open object</a>'
                f'<a href="{html.escape(links["markdown"])}">Markdown twin</a>'
                f'<a href="{html.escape(links["accepted_source"])}">Accepted source</a></p>'
                + "".join(relations)
                + '<details class="object-identity"><summary>Technical identity</summary>'
                f'<dl>{identity_rows}</dl></details></article>'
            )
        group_title = group["kind"].replace("-", " ").title()
        groups.append(
            '<section class="topic-group">'
            '<div class="topic-group-head">'
            f'<h2>{html.escape(group_title)}</h2><p>{group["count"]} '
            f'{"object" if group["count"] == 1 else "objects"}</p></div>'
            f'<div class="topic-object-grid">{"".join(cards)}</div></section>'
        )
    count = projection["object_count"]
    return (
        '<section class="hero hero-compact topic-hero">'
        f'<p class="eyebrow">Topic projection · {html.escape(projection["lens"]["id"])}</p>'
        f'<h1>{html.escape(topic["title"])}</h1>'
        f'<p class="dek">{html.escape(topic.get("description", ""))}</p>'
        '<p class="topic-count">'
        f'<strong>{count}</strong><span>{"public object" if count == 1 else "public objects"}</span>'
        f'<span>{len(projection["kind_counts"])} object kinds</span></p>'
        '<p class="representation-links">'
        f'<a href="{html.escape(representations["markdown"])}">Read as Markdown</a>'
        f'<a href="{html.escape(representations["json"])}">Read as JSON</a></p></section>'
        '<details class="lens-status"><summary>Experimental lens manifests (shared inventory)</summary>'
        '<p><strong>Experimental lens manifest.</strong> These routes currently preserve the same '
        'included-object inventory. Their labels and '
        'manifest identities differ; they are not yet materially different editorial products. '
        'This remains a manifest, not a differentiated editorial result.</p>'
        f'<p>{lens_links}</p></details>'
        '<section class="topic-index" aria-labelledby="topic-objects-title">'
        '<div class="section-head"><div><p class="eyebrow">Public catalog</p>'
        '<h2 id="topic-objects-title">Browse the objects</h2></div>'
        '<p class="topic-index-note">Grouped by object kind. Catalog links are navigation, not '
        'evidence of similarity or support.</p></div>'
        + "".join(groups)
        + "</section>"
    )


def projection_receipt_html(
    *,
    catalog_id: str,
    frontier: str,
    commit: str,
    compiler: str,
    projection_id: str | None = None,
    dossier_id: str | None = None,
    view_policy: str | None = None,
    content_digest: str | None = None,
    epistemic_policy: str | None = None,
    disclosure_policy: str | None = None,
) -> str:
    rows = []
    if projection_id:
        rows.append(("Projection", projection_id))
    if dossier_id:
        rows.append(("Dossier", dossier_id))
    if view_policy:
        rows.append(("View policy", view_policy))
    rows.extend(
        [
            ("Catalog", catalog_id),
            ("Frontier", frontier),
            ("Accepted commit", commit),
        ]
    )
    if epistemic_policy:
        rows.append(("Epistemic policy", epistemic_policy))
    if disclosure_policy:
        rows.append(("Disclosure policy", disclosure_policy))
    rows.append(("Compiler", compiler))
    if content_digest:
        rows.append(("Content digest", content_digest))
    rendered_rows = "".join(
        f"<div><dt>{html.escape(label)}</dt><dd><code>{html.escape(value)}</code></dd></div>"
        for label, value in rows
    )
    return (
        '<section class="projection-receipt" aria-labelledby="projection-receipt-title">'
        '<div class="receipt-head"><div><p class="eyebrow">Build receipt</p>'
        '<h2 id="projection-receipt-title">Reproduce this projection</h2></div>'
        '<span class="stamp">Reproducible projection</span></div>'
        f'<dl class="receipt-grid">{rendered_rows}</dl></section>'
    )


def build_public(
    root: Path,
    output: Path,
    *,
    base_url: str = DEFAULT_BASE_URL,
    api_url: str = DEFAULT_API_URL,
    mcp_url: str = DEFAULT_MCP_URL,
) -> dict[str, Any]:
    from .featured import (
        FEATURE_VIEWS,
        feature_home_html,
        feature_index_html,
        feature_page_html,
        feature_purpose_html,
        load_featured_dossier,
        review_receipt_html,
        review_receipt_markdown,
        share_card_svg,
    )
    from .featured import projection_markdown as dossier_markdown

    catalog = PublicCatalog.build(root)
    featured = load_featured_dossier(root)
    featured_default = (
        featured.envelope(catalog, featured.default_view) if featured is not None else None
    )
    output = output.resolve()
    tmp = output.parent / (output.name + ".tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)

    write_json(tmp / "catalog.json", catalog.public_dict())
    write_json(tmp / "status.json", {
        "project": "Epistemedia",
        "version": VERSION,
        "catalog_id": catalog.catalog_id,
        "frontier": catalog.frontier,
        "commit": catalog.commit,
        "generated_at": catalog.generated_at,
        "object_count": len(catalog.objects),
        "topic_count": len(catalog.topics),
        "dossier_count": 1 if featured is not None else 0,
        "featured_dossier": featured.slug if featured is not None else None,
        "protocol_version": PROTOCOL_VERSION,
    })
    write_json(tmp / "search.json", {
        "catalog_id": catalog.catalog_id,
        "frontier": catalog.frontier,
        "documents": [obj.as_dict(include_text=False) for obj in catalog.objects],
    })

    for obj in catalog.objects:
        file_key = static_object_file_key(obj.id)
        route_key = static_object_route_key(obj.id)
        write_json(tmp / "objects" / f"{file_key}.json", obj.as_dict())
        source_url = accepted_source_url(catalog, obj)
        memberships = object_topic_memberships(catalog, obj, base_url)
        membership_markdown = ", ".join(
            f"[{item['title']}]({item['url']})" for item in memberships
        ) or "None"
        markdown = (
            f"# {obj.title}\n\n"
            f"- Object ID: `{obj.id}`\n"
            f"- Kind: `{obj.kind}`\n"
            f"- Repository path: [`{obj.path}`]({source_url})\n"
            f"- Content digest: `{obj.content_digest}`\n\n"
            f"**Also filed under:** {membership_markdown}\n\n"
            f"## Source content\n\n{obj.text.rstrip()}\n"
        )
        write_text(tmp / "objects" / f"{file_key}.md", markdown)
        object_summary = human_summary(obj)
        summary = f'<p class="dek">{html.escape(object_summary)}</p>'
        membership_items = "".join(
            f'<li><a href="{html.escape(item["url"])}">{html.escape(item["title"])}</a></li>'
            for item in memberships
        )
        membership_html = (
            '<div class="object-topic-links"><p class="relation-label">Also filed under</p>'
            f'<ul class="relation-links">{membership_items}</ul></div>'
            if membership_items
            else ""
        )
        body = (
            '<article class="object-page">'
            f'<section class="hero hero-compact"><p class="eyebrow">Repository object · {html.escape(obj.kind)}</p>'
            f'<h1>{html.escape(obj.title)}</h1>{summary}'
            '<dl class="object-facts">'
            f'<div><dt>Source path</dt><dd><a href="{html.escape(source_url)}"><code>{html.escape(obj.path)}</code></a></dd></div>'
            f'<div><dt>Media type</dt><dd><code>{html.escape(obj.media_type)}</code></dd></div>'
            f'<div><dt>Object ID</dt><dd><code>{html.escape(obj.id)}</code></dd></div>'
            f'<div><dt>Content digest</dt><dd><code>{html.escape(obj.content_digest)}</code></dd></div>'
            f'</dl>{membership_html}</section><section class="source-document" aria-labelledby="source-content-title">'
            '<h2 id="source-content-title">Source content</h2>'
            + md_to_html(obj.text, heading_offset=2)
            + "</section>"
            + projection_receipt_html(
                catalog_id=catalog.catalog_id,
                frontier=catalog.frontier,
                commit=catalog.commit,
                epistemic_policy=catalog.policies["epistemic"],
                disclosure_policy=catalog.policies["disclosure"],
                compiler=f"epistemedia/{VERSION}",
            )
            + "</article>"
        )
        write_text(
            tmp / "objects" / file_key / "index.html",
            html_shell(
                obj.title,
                body,
                base_url=base_url,
                canonical_url=f"{base_url}/objects/{route_key}/",
                markdown_url=f"{base_url}/objects/{route_key}.md",
            ),
        )

    projection_count = 0
    topic_cards = []
    for topic_index, topic in enumerate(catalog.topics, start=1):
        selected = catalog.selected_objects(topic)
        topic_cards.append(
            f'<article class="card docket-card"><p class="docket-number">Topic {topic_index:02d}</p>'
            f'<h2><a href="{base_url}/topics/{topic.slug}/">{html.escape(topic.title)}</a></h2>'
            f'<p>{html.escape(topic.description)}</p><p class="card-meta"><span>'
            f'{len(selected)} objects in this topic</span>'
            '<span>Encyclopedia projection</span></p></article>'
        )
        for lens in LENSES:
            projection = topic_projection(catalog, topic, lens, base_url)
            projection_count += 1
            md = projection_markdown(projection)
            base = tmp / "topics" / topic.slug / lens
            write_json(base / "manifest.json", projection)
            write_json(base / "index.json", projection)
            write_text(base / "index.md", md)
            lens_links = " ".join(
                f'<a href="{base_url}/topics/{topic.slug}/{candidate}/">'
                f'{html.escape(candidate)}</a>'
                for candidate in LENSES
                if candidate != lens and candidate != "encyclopedia"
            )
            if lens != "encyclopedia":
                lens_links = (
                    f'<a href="{base_url}/topics/{topic.slug}/">encyclopedia</a> '
                    + lens_links
                ).strip()
            write_text(
                base / "index.html",
                html_shell(
                    f"{topic.title} — {lens}",
                    topic_projection_html(projection, lens_links)
                    + projection_receipt_html(
                        projection_id=projection["projection_id"],
                        catalog_id=projection["catalog_id"],
                        frontier=projection["frontier"],
                        commit=projection["commit"],
                        epistemic_policy=projection["policies"]["epistemic"],
                        disclosure_policy=projection["policies"]["disclosure"],
                        compiler=projection["compiler"],
                    ),
                    base_url=base_url,
                    canonical_url=f"{base_url}/topics/{topic.slug}/{lens}/",
                    markdown_url=f"{base_url}/topics/{topic.slug}/{lens}/index.md",
                ),
            )
        default_projection = topic_projection(catalog, topic, "encyclopedia", base_url)
        md = projection_markdown(default_projection)
        write_json(tmp / "topics" / topic.slug / "index.json", default_projection)
        lens_links = " ".join(
            f'<a href="{base_url}/topics/{topic.slug}/{lens}/">{html.escape(lens)}</a>'
            for lens in LENSES
            if lens != "encyclopedia"
        )
        body = (
            topic_projection_html(default_projection, lens_links)
            + projection_receipt_html(
                projection_id=default_projection["projection_id"],
                catalog_id=default_projection["catalog_id"],
                frontier=default_projection["frontier"],
                commit=default_projection["commit"],
                epistemic_policy=default_projection["policies"]["epistemic"],
                disclosure_policy=default_projection["policies"]["disclosure"],
                compiler=default_projection["compiler"],
            )
        )
        write_text(
            tmp / "topics" / topic.slug / "index.html",
            html_shell(
                topic.title,
                body,
                base_url=base_url,
                canonical_url=f"{base_url}/topics/{topic.slug}/",
                markdown_url=f"{base_url}/topics/{topic.slug}/index.md",
            ),
        )
        write_text(tmp / "topics" / topic.slug / "index.md", md)

    if featured is not None and featured_default is not None:
        case_root = tmp / "how-we-know" / featured.slug
        for view in FEATURE_VIEWS:
            projection_count += 1
            case_envelope = featured.envelope(catalog, view)
            case_data = case_envelope["data"]
            view_root = case_root / view
            write_json(view_root / "index.json", case_envelope)
            write_text(view_root / "index.md", dossier_markdown(case_envelope))
            write_text(
                view_root / "share-card.svg",
                share_card_svg(case_envelope, base_url),
            )
            case_body = feature_page_html(case_envelope, base_url) + projection_receipt_html(
                dossier_id=case_data["dossier_id"],
                view_policy=case_data["view"]["policy_id"],
                catalog_id=case_envelope["catalog_id"],
                frontier=case_envelope["frontier"],
                commit=case_envelope["commit"],
                epistemic_policy=case_envelope["policies"]["epistemic"],
                disclosure_policy=case_envelope["policies"]["disclosure"],
                compiler=case_envelope["compiler"],
                content_digest=case_envelope["content_digest"],
            )
            write_text(
                view_root / "index.html",
                html_shell(
                    f"{case_data['title']} — {view}",
                    case_body,
                    base_url=base_url,
                    canonical_url=f"{base_url}/how-we-know/{featured.slug}/{view}/",
                    markdown_url=(
                        f"{base_url}/how-we-know/{featured.slug}/{view}/index.md"
                    ),
                    social_image_url=(
                        f"{base_url}/how-we-know/{featured.slug}/{view}/share-card.svg"
                    ),
                ),
            )

        default_data = featured_default["data"]
        write_json(case_root / "index.json", featured_default)
        write_text(case_root / "index.md", dossier_markdown(featured_default))
        write_text(
            case_root / "share-card.svg",
            share_card_svg(featured_default, base_url),
        )
        write_text(
            case_root / "index.html",
            html_shell(
                default_data["title"],
                feature_page_html(featured_default, base_url)
                + projection_receipt_html(
                    dossier_id=default_data["dossier_id"],
                    view_policy=default_data["view"]["policy_id"],
                    catalog_id=featured_default["catalog_id"],
                    frontier=featured_default["frontier"],
                    commit=featured_default["commit"],
                    epistemic_policy=featured_default["policies"]["epistemic"],
                    disclosure_policy=featured_default["policies"]["disclosure"],
                    compiler=featured_default["compiler"],
                    content_digest=featured_default["content_digest"],
                ),
                base_url=base_url,
                canonical_url=f"{base_url}/how-we-know/{featured.slug}/",
                markdown_url=f"{base_url}/how-we-know/{featured.slug}/index.md",
                social_image_url=f"{base_url}/how-we-know/{featured.slug}/share-card.svg",
            ),
        )
        review_envelope = featured.review_envelope(catalog)
        review_root = case_root / "review"
        write_json(review_root / "index.json", review_envelope)
        write_text(review_root / "index.md", review_receipt_markdown(review_envelope))
        write_text(
            review_root / "index.html",
            html_shell(
                f"Review receipt — {default_data['title']}",
                review_receipt_html(review_envelope, base_url)
                + projection_receipt_html(
                    dossier_id=default_data["dossier_id"],
                    catalog_id=review_envelope["catalog_id"],
                    frontier=review_envelope["frontier"],
                    commit=review_envelope["commit"],
                    epistemic_policy=review_envelope["policies"]["epistemic"],
                    disclosure_policy=review_envelope["policies"]["disclosure"],
                    compiler=review_envelope["compiler"],
                    content_digest=review_envelope["content_digest"],
                ),
                base_url=base_url,
                canonical_url=f"{base_url}/how-we-know/{featured.slug}/review/",
                markdown_url=f"{base_url}/how-we-know/{featured.slug}/review/index.md",
            ),
        )
        how_we_know_data = {
            "realm": "How We Know",
            "scope": (
                "Truth, evidence, knowledge, and information—where they agree, where they "
                "differ, and how we can tell."
            ),
            "featured": featured.summary(catalog),
        }
        how_we_know_envelope = envelope(catalog, how_we_know_data)
        write_json(tmp / "how-we-know" / "index.json", how_we_know_envelope)
        write_text(
            tmp / "how-we-know" / "index.md",
            "# How We Know\n\n"
            "Truth, evidence, knowledge, and information—where they agree, where they differ, "
            "and how we can tell.\n\n"
            f"## Case {default_data['number']}\n\n"
            f"[{default_data['title']}]({base_url}/how-we-know/{featured.slug}/)\n\n"
            f"> {default_data['view']['label']}\n\n"
            f"- Dossier: `{default_data['dossier_id']}`\n"
            f"- Content digest: `{featured_default['content_digest']}`\n",
        )
        how_we_know_body = (
            feature_index_html(how_we_know_envelope, base_url)
            + projection_receipt_html(
                dossier_id=default_data["dossier_id"],
                view_policy=default_data["view"]["policy_id"],
                catalog_id=how_we_know_envelope["catalog_id"],
                frontier=how_we_know_envelope["frontier"],
                commit=how_we_know_envelope["commit"],
                epistemic_policy=how_we_know_envelope["policies"]["epistemic"],
                disclosure_policy=how_we_know_envelope["policies"]["disclosure"],
                compiler=how_we_know_envelope["compiler"],
                content_digest=how_we_know_envelope["content_digest"],
            )
        )
        write_text(
            tmp / "how-we-know" / "index.html",
            html_shell(
                "How We Know",
                how_we_know_body,
                base_url=base_url,
                canonical_url=f"{base_url}/how-we-know/",
                markdown_url=f"{base_url}/how-we-know/index.md",
                social_image_url=f"{base_url}/how-we-know/{featured.slug}/share-card.svg",
            ),
        )

        home_body = (
            feature_home_html(featured_default, base_url)
            + feature_purpose_html(featured_default, base_url)
            + '<section><div class="section-head"><div><p class="eyebrow">'
            'Operating substrate</p><h2>Explore how the record is built</h2></div>'
            f'<p class="meta">{len(catalog.objects)} distinct public objects · '
            f'{catalog.topic_membership_count()} topic memberships across '
            f'{len(catalog.topics)} topics</p></div><div class="grid">'
            + "".join(topic_cards)
            + '</div></section>'
            + projection_receipt_html(
                dossier_id=default_data["dossier_id"],
                view_policy=default_data["view"]["policy_id"],
                catalog_id=featured_default["catalog_id"],
                frontier=featured_default["frontier"],
                commit=featured_default["commit"],
                epistemic_policy=featured_default["policies"]["epistemic"],
                disclosure_policy=featured_default["policies"]["disclosure"],
                compiler=featured_default["compiler"],
                content_digest=featured_default["content_digest"],
            )
        )
        home_markdown = (
            "# Epistemedia\n\nKnowledge that can show its work.\n\n"
            f"## How We Know · Case {default_data['number']}\n\n"
            f"[{default_data['title']}]({base_url}/how-we-know/{featured.slug}/)\n\n"
            f"> {default_data['view']['label']}\n\n"
            f"- Apparent support assertions: "
            f"**{default_data['counts']['apparent_support_assertion_count']}**\n"
            f"- Target-comparable support roots: "
            f"**{default_data['counts']['target_comparable_support_data_root_count']} known + "
            f"{default_data['counts']['target_comparable_unresolved_data_root_count']} "
            "unresolved**\n"
            f"- Counterevidence data roots: "
            f"**{default_data['counts']['counter_data_root_count']}**\n\n"
            f"Dossier: `{default_data['dossier_id']}`  \n"
            f"Content digest: `{featured_default['content_digest']}`\n\n"
            "## Why this exists\n\n"
            "Information tells you what was said. Epistemedia shows what the evidence "
            "earns—and where it stops.\n\n"
            "Case 001 shows why: a claim can sound supported ten times while resting on "
            "four target-comparable data roots, with one 2007 lineage unresolved. The "
            "counts follow evidence lineage, not paper titles.\n\n"
            f"[Brief]({base_url}/how-we-know/{featured.slug}/) · "
            f"[Skeptical]({base_url}/how-we-know/{featured.slug}/skeptical/) · "
            f"[Evidence docket]({base_url}/how-we-know/{featured.slug}/#evidence-record-title)\n\n"
            "## Operating substrate\n\n"
            f"{len(catalog.objects)} distinct public objects · "
            f"{catalog.topic_membership_count()} topic memberships across "
            f"{len(catalog.topics)} topics.\n\n"
            f"[Explore the project substrate]({base_url}/explore/)\n"
        )
    else:
        home_body = (
            '<section class="hero hero-home"><p class="eyebrow">Open knowledge · Public alpha</p>'
            '<h1>Knowledge that can show its work.</h1>'
            '<p class="dek">No accepted featured dossier is configured in this realm.</p></section>'
            '<section><div class="grid">'
            + "".join(topic_cards)
            + "</div></section>"
            + projection_receipt_html(
                catalog_id=catalog.catalog_id,
                frontier=catalog.frontier,
                commit=catalog.commit,
                epistemic_policy=catalog.policies["epistemic"],
                disclosure_policy=catalog.policies["disclosure"],
                compiler=f"epistemedia/{VERSION}",
            )
        )
        home_markdown = "# Epistemedia\n\nKnowledge that can show its work.\n"
    write_text(
        tmp / "index.html",
        html_shell(
            "Knowledge that can show its work",
            home_body,
            base_url=base_url,
            canonical_url=f"{base_url}/",
            markdown_url=f"{base_url}/index.md",
            social_image_url=(
                f"{base_url}/how-we-know/{featured.slug}/share-card.svg"
                if featured is not None
                else None
            ),
        ),
    )
    write_text(tmp / "index.md", home_markdown)

    explore_body = (
        '<section class="hero hero-compact"><p class="eyebrow">Repository index</p><h1>Substrate</h1>'
        '<p class="dek">Browse topics and the exact public objects used to compile them.</p></section>'
        '<section aria-label="Bootstrap topics"><div class="grid">'
        + "".join(topic_cards)
        + "</div></section>"
        + projection_receipt_html(
            catalog_id=catalog.catalog_id,
            frontier=catalog.frontier,
            commit=catalog.commit,
            epistemic_policy=catalog.policies["epistemic"],
            disclosure_policy=catalog.policies["disclosure"],
            compiler=f"epistemedia/{VERSION}",
        )
    )
    write_text(
        tmp / "explore" / "index.html",
        html_shell(
            "Substrate",
            explore_body,
            base_url=base_url,
            canonical_url=f"{base_url}/explore/",
            markdown_url=f"{base_url}/explore/index.md",
        ),
    )
    write_text(tmp / "explore" / "index.md", "# Substrate\n\n" + "\n".join(f"- [{t.title}]({base_url}/topics/{t.slug}/)" for t in catalog.topics) + "\n")

    docs = [
        obj
        for obj in catalog.objects
        if obj.kind == "documentation" or obj.path in ("README.md", "AGENTS.md")
    ]
    docs_cards = "".join(
        f'<article class="card docket-card"><p class="docket-number">Document {index:02d}</p>'
        f'<h2><a href="{base_url}/objects/{static_object_route_key(obj.id)}/">{html.escape(obj.title)}</a></h2>'
        f'<p>{html.escape(obj.summary)}</p><p class="card-meta"><span>{html.escape(obj.path)}</span></p></article>'
        for index, obj in enumerate(docs, start=1)
    )
    docs_body = (
        '<section class="hero hero-compact"><p class="eyebrow">Operating library</p><h1>Documentation</h1>'
        '<p class="dek">Human guidance and machine-operable project contracts, compiled from accepted repository content.</p></section>'
        f'<section aria-label="Project documentation"><div class="grid">{docs_cards}</div></section>'
        + projection_receipt_html(
            catalog_id=catalog.catalog_id,
            frontier=catalog.frontier,
            commit=catalog.commit,
            epistemic_policy=catalog.policies["epistemic"],
            disclosure_policy=catalog.policies["disclosure"],
            compiler=f"epistemedia/{VERSION}",
        )
    )
    write_text(
        tmp / "docs" / "index.html",
        html_shell(
            "Documentation",
            docs_body,
            base_url=base_url,
            canonical_url=f"{base_url}/docs/",
            markdown_url=f"{base_url}/docs/index.md",
        ),
    )
    write_text(tmp / "docs" / "index.md", "# Documentation\n\n" + "\n".join(f"- [{o.title}]({base_url}/objects/{static_object_route_key(o.id)}/) — `{o.path}`" for o in docs) + "\n")

    corpus_scope = (
        "one independently reviewed How We Know dossier plus the self-describing repository corpus"
        if featured is not None
        else "self-describing repository bootstrap"
    )
    status_md = (
        "# Epistemedia status\n\n"
        "- Canonical human site: `https://epistemedia.org` — verified live with HTTPS\n"
        "- Sharing redirect: `https://episte.media` — reserved, not verified live\n"
        "- Hosted API: `https://api.epistemedia.org/v1` — reserved, not verified live\n"
        "- Hosted MCP: `https://mcp.epistemedia.org/mcp` — reserved, not verified live\n"
        f"- Corpus scope: {corpus_scope}\n"
        f"- Version: `{VERSION}`\n"
        f"- Catalog: `{catalog.catalog_id}`\n"
        f"- Frontier: `{catalog.frontier}`\n"
        f"- Commit: `{catalog.commit}`\n"
        f"- Public objects: `{len(catalog.objects)}`\n"
        f"- Topics: `{len(catalog.topics)}`\n"
        f"- Featured dossiers: `{1 if featured is not None else 0}`\n"
        f"- Projections: `{projection_count}`\n"
    )
    write_text(tmp / "status" / "index.md", status_md)
    status_rows = "".join(
        [
            '<div class="status-row"><span class="status-name">Canonical human site</span>'
            '<span class="status-value"><code>https://epistemedia.org</code></span>'
            '<span class="status-label status-live">Verified live · HTTPS</span></div>',
            '<div class="status-row"><span class="status-name">Sharing redirect</span>'
            '<span class="status-value"><code>https://episte.media</code></span>'
            '<span class="status-label status-reserved">Reserved · unverified</span></div>',
            '<div class="status-row"><span class="status-name">Hosted API</span>'
            '<span class="status-value"><code>https://api.epistemedia.org/v1</code></span>'
            '<span class="status-label status-reserved">Reserved · unverified</span></div>',
            '<div class="status-row"><span class="status-name">Hosted MCP</span>'
            '<span class="status-value"><code>https://mcp.epistemedia.org/mcp</code></span>'
            '<span class="status-label status-reserved">Reserved · unverified</span></div>',
        ]
    )
    status_body = (
        '<section class="hero hero-compact"><p class="eyebrow">Provider read-back + build identity</p>'
        '<h1>Status</h1><p class="dek">Live means externally observed. Reserved destinations are not presented as deployed services.</p></section>'
        '<section aria-labelledby="surface-status-title"><div class="section-head"><div>'
        '<p class="eyebrow">Service boundary</p><h2 id="surface-status-title">Public surfaces</h2>'
        f'</div></div><div class="status-list">{status_rows}</div></section>'
        '<section aria-labelledby="build-summary-title"><div class="section-head"><div>'
        '<p class="eyebrow">Current compilation</p><h2 id="build-summary-title">Public corpus</h2>'
        '</div></div><dl class="object-facts">'
        f'<div><dt>Version</dt><dd><code>{VERSION}</code></dd></div>'
        f'<div><dt>Public objects</dt><dd>{len(catalog.objects)}</dd></div>'
        f'<div><dt>Topics</dt><dd>{len(catalog.topics)}</dd></div>'
        f'<div><dt>Featured dossiers</dt><dd>{1 if featured is not None else 0}</dd></div>'
        f'<div><dt>Projections</dt><dd>{projection_count}</dd></div>'
        f'</dl><p class="scope-note"><strong>Current coverage:</strong><span>{html.escape(corpus_scope)}.</span></p></section>'
        + projection_receipt_html(
            catalog_id=catalog.catalog_id,
            frontier=catalog.frontier,
            commit=catalog.commit,
            epistemic_policy=catalog.policies["epistemic"],
            disclosure_policy=catalog.policies["disclosure"],
            compiler=f"epistemedia/{VERSION}",
        )
    )
    write_text(
        tmp / "status" / "index.html",
        html_shell(
            "Status",
            status_body,
            base_url=base_url,
            canonical_url=f"{base_url}/status/",
            markdown_url=f"{base_url}/status/index.md",
        ),
    )

    llms = [
        "# Epistemedia",
        "> Knowledge that can show its work. An open, federated knowledge network for humans and agents.",
        "",
        "## Start here",
        f"- [Project overview]({base_url}/index.md)",
        f"- [How We Know]({base_url}/how-we-know/index.md)",
        *(
            [
                f"- [Featured evidence dossier]({base_url}/how-we-know/{featured.slug}/index.md)",
                f"- [Featured dossier JSON]({base_url}/how-we-know/{featured.slug}/index.json)",
                f"- [Featured scoreboard card]({base_url}/how-we-know/{featured.slug}/share-card.svg)",
                f"- [Independent review receipt]({base_url}/how-we-know/{featured.slug}/review/index.md)",
            ]
            if featured is not None
            else []
        ),
        f"- [Documentation]({base_url}/docs/index.md)",
        f"- [Substrate topics]({base_url}/explore/index.md)",
        f"- [Current status]({base_url}/status/index.md)",
        f"- [Public catalog]({base_url}/catalog.json)",
        f"- [Static OpenAPI contract — hosted API not live]({base_url}/openapi.json)",
        f"- [Static MCP descriptor — remote MCP not live]({base_url}/mcp/server.json)",
        "",
        "## Agent operating rule",
        "Treat pages as reproducible projections, not canonical truth. Preserve repository path, object ID, content digest, catalog, frontier, policy, disclosure boundary, and compiler metadata in downstream work.",
    ]
    write_text(tmp / "llms.txt", "\n".join(llms) + "\n")
    write_text(tmp / "docs" / "llms.txt", "# Epistemedia documentation\n\n" + "\n".join(f"- [{o.title}]({base_url}/objects/{static_object_route_key(o.id)}.md)" for o in docs) + "\n")
    write_text(tmp / "llms-full.txt", "# Epistemedia public project corpus\n\n" + "\n\n---\n\n".join(f"## {o.title}\n\nSource: `{o.path}`\n\n{o.text}" for o in catalog.objects) + "\n")

    openapi = openapi_document(base_url=base_url, api_url=api_url)
    write_json(tmp / "openapi.json", openapi)
    write_json(tmp / "api" / "openapi.json", openapi)
    discovery = {
        "schema": "https://epistemedia.com/schemas/discovery-v1.json",
        "name": "Epistemedia",
        "description": "Knowledge that can show its work.",
        "catalog_id": catalog.catalog_id,
        "frontier": catalog.frontier,
        "commit": catalog.commit,
        "human": base_url,
        "llms": f"{base_url}/llms.txt",
        "api": api_url,
        "openapi": f"{base_url}/openapi.json",
        "mcp": mcp_url,
        "repository": "https://github.com/yoheinakajima/epistemedia",
        "protocol_version": PROTOCOL_VERSION,
        "representations": ["text/html", "text/markdown", "application/json", "application/ld+json"],
        "how_we_know": f"{base_url}/how-we-know/",
    }
    if featured is not None and featured_default is not None:
        discovery["featured_dossier"] = {
            "slug": featured.slug,
            "dossier_id": featured_default["data"]["dossier_id"],
            "human": f"{base_url}/how-we-know/{featured.slug}/",
            "markdown": f"{base_url}/how-we-know/{featured.slug}/index.md",
            "json": f"{base_url}/how-we-know/{featured.slug}/index.json",
            "review": f"{base_url}/how-we-know/{featured.slug}/review/",
            "share_card": f"{base_url}/how-we-know/{featured.slug}/share-card.svg",
            "content_digest": featured_default["content_digest"],
        }
    write_json(tmp / ".well-known" / "epistemedia.json", discovery)
    write_json(tmp / "mcp" / "server.json", mcp_descriptor(mcp_url))
    write_text(tmp / "robots.txt", "User-agent: *\nAllow: /\nSitemap: " + base_url + "/sitemap.xml\n")
    urls = [
        base_url + "/",
        base_url + "/how-we-know/",
        base_url + "/docs/",
        base_url + "/explore/",
        base_url + "/status/",
    ] + [f"{base_url}/topics/{topic.slug}/" for topic in catalog.topics]
    if featured is not None:
        urls += [
            f"{base_url}/how-we-know/{featured.slug}/",
            f"{base_url}/how-we-know/{featured.slug}/review/",
            *[
                f"{base_url}/how-we-know/{featured.slug}/{view}/"
                for view in FEATURE_VIEWS
            ],
        ]
    write_text(tmp / "sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(f"  <url><loc>{html.escape(url)}</loc></url>" for url in urls) + "\n</urlset>\n")
    write_text(tmp / ".well-known" / "security.txt", "Contact: https://github.com/yoheinakajima/epistemedia/security\nCanonical: " + base_url + "/.well-known/security.txt\n")

    inventory = []
    for path in sorted(tmp.rglob("*")):
        if path.is_file():
            rel = path.relative_to(tmp).as_posix()
            inventory.append({"path": rel, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size})
    manifest = {
        "schema": "https://epistemedia.com/schemas/release-manifest-v1.json",
        "catalog_id": catalog.catalog_id,
        "frontier": catalog.frontier,
        "commit": catalog.commit,
        "compiler": f"epistemedia/{VERSION}",
        "generated_at": catalog.generated_at,
        "base_url": base_url,
        "api_url": api_url,
        "mcp_url": mcp_url,
        "file_count": len(inventory) + 1,
        "files": inventory,
    }
    # Manifest ID intentionally excludes deployment URLs and generation time.
    manifest["manifest_id"] = stable_id("release-manifest", {
        "catalog_id": catalog.catalog_id,
        "frontier": catalog.frontier,
        "commit": catalog.commit,
        "files": [(item["path"], item["sha256"]) for item in inventory],
    })
    write_json(tmp / "manifest.json", manifest)

    if output.exists():
        shutil.rmtree(output)
    tmp.replace(output)
    return manifest


def openapi_document(*, base_url: str = DEFAULT_BASE_URL, api_url: str = DEFAULT_API_URL) -> dict[str, Any]:
    return {
        "openapi": "3.1.1",
        "info": {
            "title": "Epistemedia Public API",
            "version": VERSION,
            "description": "Free read access to disclosure-safe Epistemedia public projections.",
            "license": {"name": "Apache-2.0 and object-specific content licenses"},
        },
        "servers": [{"url": api_url}],
        "paths": {
            "/status": {"get": operation("Current public catalog status", "getStatus")},
            "/search": {"get": {**operation("Search public objects", "searchKnowledge"), "parameters": [{"name": "q", "in": "query", "required": True, "schema": {"type": "string"}}, {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20, "maximum": 100}}]}},
            "/dossiers": {
                "get": operation("List accepted public dossiers", "listDossiers")
            },
            "/dossiers/{slug}": {
                "get": {
                    **operation("Get an accepted dossier policy view", "getDossier"),
                    "parameters": [
                        {
                            "name": "slug",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "policy",
                            "in": "query",
                            "schema": {
                                "type": "string",
                                "enum": ["encyclopedia", "skeptical"],
                                "default": "encyclopedia",
                            },
                        },
                    ],
                }
            },
            "/topics": {"get": operation("List public topics", "listTopics")},
            "/topics/{slug}": {"get": {**operation("Get a topic projection", "getTopic"), "parameters": [{"name": "slug", "in": "path", "required": True, "schema": {"type": "string"}}, {"name": "lens", "in": "query", "schema": {"type": "string", "enum": sorted(LENSES), "default": "encyclopedia"}}]}},
            "/objects/{id}": {"get": {**operation("Get an exact public object", "getObject"), "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}]}},
            "/claims/{id}/trace": {"get": {**operation("Trace a claim or object to accepted sources and manifest data", "traceClaim"), "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}]}},
        },
        "components": {
            "schemas": {
                "Envelope": {
                    "type": "object",
                    "required": [
                        "catalog_id",
                        "frontier",
                        "commit",
                        "policies",
                        "compiler",
                        "content_digest",
                        "data",
                    ],
                    "properties": {
                        "catalog_id": {"type": "string"},
                        "frontier": {"type": "string"},
                        "commit": {"type": "string"},
                        "policies": {"type": "object"},
                        "compiler": {"type": "string"},
                        "content_digest": {"type": "string"},
                        "data": {},
                    },
                },
                "Error": {"type": "object", "required": ["error"], "properties": {"error": {"type": "string"}, "detail": {"type": "string"}}},
            }
        },
        "externalDocs": {"url": f"{base_url}/docs/"},
    }


def operation(summary: str, operation_id: str) -> dict[str, Any]:
    return {
        "summary": summary,
        "operationId": operation_id,
        "responses": {
            "200": {"description": "Disclosure-safe public response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Envelope"}}}},
            "404": {"description": "Not found", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
        },
    }


def mcp_descriptor(mcp_url: str = DEFAULT_MCP_URL) -> dict[str, Any]:
    return {
        "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
        "name": "com.epistemedia/knowledge",
        "description": "Read and trace disclosure-safe Epistemedia knowledge projections.",
        "version": VERSION,
        "remotes": [{"type": "streamable-http", "url": mcp_url}],
        "repository": {"url": "https://github.com/yoheinakajima/epistemedia", "source": "github"},
    }


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []
    required = ["README.md", "AGENTS.md", "pyproject.toml"]
    for rel in required:
        if not (root / rel).exists():
            errors.append(f"missing required file: {rel}")
    try:
        catalog = PublicCatalog.build(root)
        if not catalog.objects:
            errors.append("public catalog contains no objects")
        if not catalog.topics:
            errors.append("public catalog contains no topics")
        ids = [obj.id for obj in catalog.objects]
        if len(ids) != len(set(ids)):
            errors.append("duplicate public object IDs")
        for obj in catalog.objects:
            if obj.visibility != "public":
                errors.append(f"non-public object entered PublicCatalog: {obj.path}")
            if not obj.content_digest:
                errors.append(f"object lacks content digest: {obj.path}")
        from .featured import load_featured_dossier

        load_featured_dossier(root)
    except Exception as exc:
        errors.append(str(exc))
    # Common secret patterns are hard failures in accepted text files.
    secret_patterns = [
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        re.compile(r"ghp_[A-Za-z0-9]{30,}"),
        re.compile(r"sk-[A-Za-z0-9]{30,}"),
    ]
    for path in root.rglob("*"):
        if not path.is_file() or not is_public_source(root, path):
            continue
        text = read_text(path)
        if any(pattern.search(text) for pattern in secret_patterns):
            errors.append(f"possible secret in {path.relative_to(root)}")
    return errors


def audit_public(root: Path, public: Path) -> list[str]:
    findings: list[str] = []
    catalog = PublicCatalog.build(root)
    catalog_path = public / "catalog.json"
    manifest_path = public / "manifest.json"
    if not catalog_path.exists():
        return ["missing generated catalog.json"]
    if not manifest_path.exists():
        return ["missing generated manifest.json"]
    generated = json.loads(catalog_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    if generated.get("catalog_id") != catalog.catalog_id:
        findings.append("generated catalog ID differs from current accepted inputs")
    if generated.get("frontier") != catalog.frontier:
        findings.append("generated frontier differs from current accepted inputs")
    if manifest.get("catalog_id") != catalog.catalog_id:
        findings.append("release manifest references another catalog")
    required = [
        public / "index.html",
        public / "llms.txt",
        public / "openapi.json",
        public / ".well-known" / "epistemedia.json",
        public / "mcp" / "server.json",
    ]
    from .featured import load_featured_dossier

    featured = load_featured_dossier(root)
    if featured is not None:
        required += [
            public / "how-we-know" / "index.html",
            public / "how-we-know" / featured.slug / "index.html",
            public / "how-we-know" / featured.slug / "index.md",
            public / "how-we-know" / featured.slug / "index.json",
            public / "how-we-know" / featured.slug / "review" / "index.html",
            public / "how-we-know" / featured.slug / "review" / "index.md",
            public / "how-we-know" / featured.slug / "review" / "index.json",
        ]
    for path in required:
        if not path.exists():
            findings.append(f"missing public interface: {path.relative_to(public)}")
    # Static public output must not contain obvious private path or key material.
    forbidden = ["/Users/", "C:\\Users\\", "PRIVATE KEY-----", "ghp_", "sk-"]
    for path in public.rglob("*"):
        if not path.is_file() or path.stat().st_size > 5_000_000:
            continue
        try:
            text = path.read_text(errors="ignore")
        except Exception:
            continue
        for token in forbidden:
            if token in text:
                findings.append(f"public disclosure finding in {path.relative_to(public)}: {token}")
    findings.extend(verify_release_identity(public))
    return sorted(set(findings))


def verify_release_identity(public: Path) -> list[str]:
    """Fail closed when a generated route declares or renders another release identity."""

    findings: list[str] = []
    catalog_path = public / "catalog.json"
    if not catalog_path.exists():
        return ["release identity check lacks catalog.json"]
    try:
        catalog = json.loads(catalog_path.read_text())
    except json.JSONDecodeError:
        return ["release identity check cannot parse catalog.json"]
    catalog_policies = catalog.get("policies")
    compiler = catalog_policies.get("compiler") if isinstance(catalog_policies, dict) else None
    expected = {
        "catalog_id": catalog.get("catalog_id"),
        "frontier": catalog.get("frontier"),
        "commit": catalog.get("commit"),
        "compiler": compiler,
    }
    if any(not isinstance(value, str) or not value for value in expected.values()):
        return ["release identity check found an incomplete catalog identity"]

    manifest_path = public / "manifest.json"
    if not manifest_path.exists():
        findings.append("release identity check lacks manifest.json")
    else:
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError:
            findings.append("release identity check cannot parse manifest.json")
            manifest = {}
        inventory = manifest.get("files")
        if not isinstance(inventory, list):
            findings.append("release manifest files must be a list")
            inventory = []
        expected_manifest_id = stable_id(
            "release-manifest",
            {
                "catalog_id": manifest.get("catalog_id"),
                "frontier": manifest.get("frontier"),
                "commit": manifest.get("commit"),
                "files": [
                    (item.get("path"), item.get("sha256"))
                    for item in inventory
                    if isinstance(item, dict)
                ],
            },
        )
        if manifest.get("manifest_id") != expected_manifest_id:
            findings.append("release manifest identity does not match its declared inventory")
        if manifest.get("file_count") != len(inventory) + 1:
            findings.append("release manifest file count does not match its inventory")

        declared_paths: set[str] = set()
        for item in inventory:
            if not isinstance(item, dict):
                findings.append("release manifest inventory contains a non-object entry")
                continue
            relative = item.get("path")
            if not isinstance(relative, str) or not relative:
                findings.append("release manifest inventory contains an invalid path")
                continue
            candidate = (public / relative).resolve()
            try:
                candidate.relative_to(public.resolve())
            except ValueError:
                findings.append(f"release manifest path escapes public root: {relative}")
                continue
            if relative in declared_paths:
                findings.append(f"release manifest path is duplicated: {relative}")
                continue
            declared_paths.add(relative)
            if not candidate.is_file():
                findings.append(f"release manifest file is missing: {relative}")
                continue
            if item.get("bytes") != candidate.stat().st_size:
                findings.append(f"release manifest byte count differs: {relative}")
            actual_sha256 = hashlib.sha256(candidate.read_bytes()).hexdigest()
            if item.get("sha256") != actual_sha256:
                findings.append(f"release manifest digest differs: {relative}")

        actual_paths = {
            path.relative_to(public).as_posix()
            for path in public.rglob("*")
            if path.is_file() and path != manifest_path
        }
        for relative in sorted(actual_paths - declared_paths):
            findings.append(f"generated file is absent from release manifest: {relative}")
        for relative in sorted(declared_paths - actual_paths):
            findings.append(f"release manifest declares an absent generated file: {relative}")

    for path in sorted(public.rglob("index.html")):
        rendered = path.read_text(errors="ignore")
        for identity_field, value in expected.items():
            if value not in rendered:
                findings.append(
                    "mixed release identity in "
                    f"{path.relative_to(public)}: missing {identity_field}"
                )

    for path in sorted(public.rglob("*.json")):
        try:
            document = json.loads(path.read_text())
        except json.JSONDecodeError:
            findings.append(f"invalid generated JSON: {path.relative_to(public)}")
            continue
        if not isinstance(document, dict):
            continue
        for identity_field, value in expected.items():
            if identity_field in document and document[identity_field] != value:
                findings.append(
                    "mixed release identity in "
                    f"{path.relative_to(public)}: {identity_field} differs"
                )
        policies = document.get("policies")
        if isinstance(policies, dict) and policies.get("compiler") not in {
            None,
            expected["compiler"],
        }:
            findings.append(
                f"mixed release identity in {path.relative_to(public)}: compiler differs"
            )
    return findings


def envelope(catalog: PublicCatalog, data: Any) -> dict[str, Any]:
    return {
        "catalog_id": catalog.catalog_id,
        "frontier": catalog.frontier,
        "commit": catalog.commit,
        "policies": catalog.policies,
        "compiler": f"epistemedia/{VERSION}",
        "content_digest": digest(data),
        "data": data,
    }


def discover_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "AGENTS.md").exists():
            return candidate
    raise FileNotFoundError("not inside an Epistemedia repository; pass --root")
