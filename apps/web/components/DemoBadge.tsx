export function DemoBadge({ label = "DEMO DATA" }: { label?: string }) {
  return (
    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
      bg-amber-100 text-amber-700 border border-amber-300">
      {label}
    </span>
  );
}