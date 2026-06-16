export interface NodeMeta {
  key: string;
  label: string;
  description: string;
}

// The fixed pipeline shown in the progress stepper. The research/analysis/
// quality_check trio may run more than once via the conditional retry loop.
export const NODES: NodeMeta[] = [
  { key: "planner", label: "Planner", description: "Builds the research plan" },
  { key: "research", label: "Research", description: "Web search + website fetch" },
  { key: "analysis", label: "Analysis", description: "Synthesizes findings" },
  {
    key: "quality_check",
    label: "Quality Check",
    description: "LLM judge — loops back on gaps",
  },
  { key: "report", label: "Report", description: "Final briefing" },
];
