# Product & Business Thinking

## 1. Five weaknesses in the current product design

1. **No grounding guarantees.** The report can still over-claim; "Unknowns" helps
   but there's no per-claim citation or confidence, so a seller can't tell what's
   verified vs. inferred.
2. **One-shot, generic research.** It doesn't tailor depth to deal size, persona,
   or industry, and it can't be steered mid-run ("focus on security posture").
3. **No freshness or re-run.** A report is a snapshot; there's no scheduled
   refresh or "what changed since last week" — value decays fast in sales.
4. **No CRM / workflow integration.** Output lives in the app, not in the tools
   reps actually work in (Salesforce/HubSpot, email, Slack).
5. **Single user, no collaboration or accounts.** No auth, sharing, or team
   library; knowledge isn't reused across the org.
6. **Unmanaged cost/latency.** No budgets, caching, or quality scoring surfaced
   to the user, so runs vary in price and time unpredictably.

## 2. Top 3 improvements to build next

1. **Cited, confidence-scored reports** — every claim links to a source and a
   confidence level. This is the trust unlock; without it, reps double-check
   everything and the time-savings evaporate.
2. **CRM + email integration** — push the briefing into the account record and
   draft outreach in Gmail/Outlook. Meets users where they work; drives adoption.
3. **Saved profiles + scheduled refresh** — re-run on a cadence and surface
   deltas. Turns a one-off tool into recurring, sticky value.

## 3. Who buys, who uses, why they'd pay

- **Buyer:** VP of Sales / RevOps / Sales Enablement (and SDR-team leads).
- **User:** AEs, SDRs/BDRs, founders selling, customer-success and partnerships.
- **Why they pay:** pre-call research is ~30–60 min of manual work per meeting and
  is done inconsistently. A reliable, cited briefing in minutes raises meeting
  quality and rep capacity. The ROI is straightforward — time saved per rep per
  week, and better-prepared first calls — which is easy to justify on a per-seat
  plan or usage-based pricing.

## 4. Success metrics

- **Activation:** % of new users who complete ≥3 reports in week 1.
- **Value/efficiency:** median research time saved per meeting; reports per active
  rep per week.
- **Quality:** % reports rated useful (thumbs up); citation coverage; "Unknowns"
  rate trend.
- **Retention/expansion:** weekly active reps, seat expansion, logo retention.
- **Outcome (north star to chase):** correlation between briefing use and
  meeting→opportunity conversion.

## 5. Four-week AI roadmap

- **Week 1 — Grounding.** Per-claim citations + confidence; stricter "only state
  what's supported" prompting; tighten the quality rubric.
- **Week 2 — Eval harness.** Golden companies + LLM-graded rubric; track
  quality/citation coverage in CI; A/B prompts and models against it.
- **Week 3 — Steering & personas.** Objective/persona-aware planning; mid-run
  steering; depth tiers (quick vs. deep) with token budgets.
- **Week 4 — Cost & freshness.** Cache search/fetch; per-run budgets; scheduled
  re-runs with "what changed" diffs.

## 6. Biggest cost, scaling, and reliability risks

- **Cost:** unbounded LLM + search spend per run (the retry loop and deep
  research multiply calls). Mitigate with budgets, caching, model tiering
  (cheap model for routing/judge), and batch where possible.
- **Scaling:** synchronous, single-process execution and in-process progress
  streaming. Mitigate with a durable job queue + workers and Redis/Postgres
  pub/sub for SSE across replicas.
- **Reliability:** third-party latency/outages and rate limits surfacing
  mid-workflow. Mitigate with retries/backoff, circuit breakers, deterministic
  fallbacks (already present), and checkpoint-based resume.

## 7. A feature I'd remove (and why)

**The free-form follow-up chat — in its current generic form.** It's the lowest
differentiated surface (it's "chat over a doc") and it dilutes focus. I'd replace
it with **targeted, structured actions** ("draft the outreach email", "generate 5
discovery questions for the CFO", "what changed since last run") that are higher
intent and easier to make reliable and measurable.

## 8. A feature I'd add (and why)

**CRM-native delivery + outreach drafting.** Push the briefing into the account
record and draft a first-touch email/sequence. It moves the product from a
"nice tool you visit" to "in the flow of work," which is where sales tools win on
adoption and retention — and it creates a natural usage-based billing surface.

## 9. First 90-day roadmap

- **Days 0–30 — Trust & measurement.** Citations + confidence, eval harness,
  basic auth and per-user sessions. Goal: a briefing reps trust without
  re-checking.
- **Days 31–60 — In the flow of work.** CRM (HubSpot/Salesforce) + email
  integration; saved company profiles; team library/sharing. Goal: daily-active
  usage inside existing tools.
- **Days 61–90 — Stickiness & economics.** Scheduled refresh with change diffs;
  cost controls + caching; usage dashboards and pricing/packaging. Goal: provable
  ROI and a path to seat/usage expansion.

## 10. If I owned this product, what I'd change first

**Make the output trustworthy and measurable before adding surface area.** The
single biggest lever is grounding: cited, confidence-scored claims plus an
evaluation harness that quantifies report quality. Everything else (integrations,
scheduling, pricing) compounds on trust — a fast briefing reps don't believe is
worth nothing, and without evals we'd be tuning prompts blind. So week one is
citations + confidence + an eval rubric, and only then do I expand distribution.
