import type { ResearchReport } from "../lib/types";

function ListSection({ title, items }: { title: string; items: string[] }) {
  if (!items?.length) return null;
  return (
    <section>
      <h3 className="mb-2 text-sm font-semibold text-slate-800">{title}</h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

export function ReportView({ report }: { report: ResearchReport }) {
  return (
    <div className="space-y-6 rounded-xl border border-slate-200 bg-white p-6">
      <section>
        <h3 className="mb-2 text-sm font-semibold text-slate-800">
          Company Overview
        </h3>
        <p className="text-sm leading-relaxed text-slate-600">
          {report.company_overview || "—"}
        </p>
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        <ListSection title="Products & Services" items={report.products_and_services} />
        <ListSection title="Target Customers" items={report.target_customers} />
        <ListSection title="Business Signals" items={report.business_signals} />
        <ListSection
          title="Risks & Challenges"
          items={report.risks_and_challenges}
        />
      </div>

      <ListSection
        title="Suggested Discovery Questions"
        items={report.discovery_questions}
      />

      <section>
        <h3 className="mb-2 text-sm font-semibold text-slate-800">
          Suggested Outreach Strategy
        </h3>
        <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-600">
          {report.outreach_strategy.map((step, i) => (
            <li key={i}>{step}</li>
          ))}
        </ol>
      </section>

      {report.unknowns.length > 0 && (
        <section className="rounded-lg bg-amber-50 p-4">
          <h3 className="mb-2 text-sm font-semibold text-amber-800">
            Unknowns — verify before the meeting
          </h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-amber-700">
            {report.unknowns.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </section>
      )}

      {report.sources.length > 0 && (
        <section>
          <h3 className="mb-2 text-sm font-semibold text-slate-800">
            Sources ({report.sources.length})
          </h3>
          <ul className="space-y-1 text-sm">
            {report.sources.map((s, i) => (
              <li key={i}>
                <a
                  href={s.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  {s.title || s.url}
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
