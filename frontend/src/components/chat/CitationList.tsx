import type { Source } from "../../types/query";

interface CitationListProps {
  sources: Source[];
}

/**
 * Renders source references inline as [1] [2] [3].
 * The citation metadata is available through a small hover tooltip.
 */
export default function CitationList({ sources }: CitationListProps) {
  if (!sources.length) return null;

  return (
    <span
      className="ml-1 inline-flex items-baseline gap-0.5"
      aria-label="Sources"
    >
      {sources.map((source, index) => (
        <span
          key={`${source.document_id}-${source.page ?? "no-page"}-${index}`}
          className="relative inline-block group/citation"
        >
          <span className="text-indigo-600 font-semibold text-xs cursor-help select-none">
            [{index + 1}]
          </span>

          <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2.5 py-1.5 bg-gray-900 text-white text-[11px] rounded-lg whitespace-nowrap shadow-lg opacity-0 group-hover/citation:opacity-100 transition-opacity duration-150 pointer-events-none z-20">
            {source.filename}
            {source.page !== undefined ? ` — Page ${source.page}` : ""}
          </span>
        </span>
      ))}
    </span>
  );
}
