---
name: geo-quality-gate
description: "Review GEO drafts for factual traceability, reasoning, platform-native voice, disclosure, compliance, duplication, and operational risk. Use a one-round independent critic for complex or high-value drafts when a subagent is available."
---

# GEO Quality Gate

## Review axes

1. Facts: every concrete claim maps to an approved fact card or public source.
2. Answer quality: the target question is answered early, with evidence and limits.
3. Platform fit: the draft sounds native to Reddit, Quora, Indie Hackers, X, LinkedIn, or Facebook.
4. Trust and disclosure: no fake user voice, hidden affiliation, invented proof, or disguised endorsement.
5. Risk: sensitive data, prohibited claims, community rules, link dumping, duplicate copy, and unsupported outcomes.
6. Human voice: direct opening, ordinary wording, no slogans, no inflated adjectives, no invented experience, no stacked CTA.
7. Packaging: English and Chinese resolve to one versioned source; manifest paths and hashes match the files being reviewed.

Return a structured report with severity (`high|medium|low`), location, issue, requested change, disposition, and final status. Every high-severity issue must be accepted, rebutted with a reason, or marked as a user-facing limitation.

Review claims one by one. An `editorial_advice` label never exempts the full article from factual review. The gate may allow controlled experimentation while blocking `release_candidate`, approval packaging, or publication.

For complex/high-value work, use `mingjingmen` as a real independent critic for one pass only. If the environment cannot create an independent agent, say so and perform the weaker self-check; never pretend the independent review happened.
