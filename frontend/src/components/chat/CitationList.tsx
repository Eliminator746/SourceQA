import { useState } from "react";

import type { Source } from "../../types/query";

interface CitationListProps {
  sources: Source[];
}

export default function CitationList({ sources }: CitationListProps) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-2" aria-label="Sources">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
        Sources
      </p>
      <div className="flex flex-col gap-1.5">
        {sources.map((source, index) => (
          <CitationItem
            key={`${source.document_id}-${source.chunk_index ?? index}`}
            source={source}
            index={index}
          />
        ))}
      </div>
    </div>
  );
}

interface CitationItemProps {
  source: Source;
  index: number;
}

function CitationItem({ source, index }: CitationItemProps) {
  const [showEvidence, setShowEvidence] = useState(false);

  // Backend already normalizes pages to 1-based; display directly.
  const displayPage =
    source.page !== undefined && source.page !== null ? source.page : null;

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-xs">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="shrink-0 w-5 h-5 rounded-full bg-indigo-100 text-indigo-600 font-bold flex items-center justify-center text-[10px]">
            {index + 1}
          </span>
          <div className="min-w-0">
            <span className="font-medium text-gray-700 truncate block">
              {source.filename}
            </span>
            <span className="text-gray-400">
              {displayPage !== null && `Page ${displayPage}`}
              {source.chunk_index !== undefined &&
                ` · Chunk ${source.chunk_index}`}
            </span>
          </div>
        </div>

        {source.content && (
          <button
            type="button"
            onClick={() => setShowEvidence((prev) => !prev)}
            aria-expanded={showEvidence}
            className="shrink-0 text-indigo-500 hover:text-indigo-700 font-medium transition"
          >
            {showEvidence ? "Hide" : "Show"}
          </button>
        )}
      </div>

      {showEvidence && source.content && (
        <p className="mt-2 pt-2 border-t border-gray-200 text-gray-600 leading-relaxed">
          {source.content}
        </p>
      )}
    </div>
  );
}
