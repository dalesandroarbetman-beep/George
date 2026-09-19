# Archive adaptation notes

## Adopt

- `geo-architect-direct-upload-fixed.zip`: strategy center, five-door diagnosis, question matrix, entity model, stage gates, and handoff contracts.
- `geo-content-production-suite.zip`: fact gate, answer-first structure, source discipline, platform-native rewriting, scoring, and self-test. Its included scorer tests passed on Python 3.11.
- `geo-content-publisher.zip`: queue/state model, human approval, manual execution pack, URL logging, and metrics schema.
- `mingjingmen.zip`: one independent critic pass for complex or high-stakes drafts; it is a soft gate, not a hard enforcement mechanism.
- `geo-scanner-final.zip`: scan/offsite evidence concepts and reproducibility checks.
- `text to pdf.zip`: optional visual report renderer only.

## Site-specific source

The first knowledge source is `https://www.yohodiy.com/`. It is a JavaScript-rendered storefront. Use the site-crawl profile in `geo-knowledge-base` and preserve the crawl date, final URL, page text, and source type for every fact card.

The current environment can render the site through the browser CLI but does not have the Python `playwright` module. The crawler writes a blocked report instead of pretending that page extraction succeeded; use the browser fallback or install the approved Python dependency before a full crawl.

The current environment now has Python Playwright and Chromium. A public-API capture was added for allowlisted storefront display data, and a fact-card builder produced a review package. API evidence is still source evidence, not business approval.

## Adapt before use

- Existing platform reference text is China-centric; use the foreign-platform reference in this skill for the initial target set.
- Replace references to automatic or authenticated publishing with manual execution packs.
- Treat engine/platform visibility as an observation to be measured, never as a guaranteed ranking or citation rule.

## Blocked scripts

Static compilation on Python 3.11 found f-string syntax errors in the archived `geo-scanner-final/scripts/geo_scan.py` and `geo-content-publisher/scripts/pipeline.py`. Those archive copies remain historical evidence and are not execution paths. The maintained replacements are `skills/geo-scanner/scripts/scan_public_site.py` and `skills/geo-content-publisher/scripts/build_execution_pack.py`; both compile on Python 3.11 and have regression and smoke-test coverage.
