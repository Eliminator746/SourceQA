import { useState } from "react";

import type { Source } from "../../types/query";

interface CitationListProps {
  sources: Source[];
}

export default function CitationList({ sources }: CitationListProps) {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <section className="citation-list" aria-label="Sources">
      <h3>Sources</h3>

      <div>
        {sources.map((source, index) => (
          <CitationItem
            key={`${source.document_id}-${source.chunk_index ?? index}`}
            source={source}
            index={index}
          />
        ))}
      </div>
    </section>
  );
}

interface CitationItemProps {
  source: Source;
  index: number;
}

function CitationItem({ source, index }: CitationItemProps) {
  const [showEvidence, setShowEvidence] = useState(false);

  const displayPage =
    source.page_label ?? (source.page !== undefined ? source.page + 1 : null);

  return (
    <article className="citation-item">
      {/* ------------------------------------------ */}
      {/* Citation header */}
      {/* ------------------------------------------ */}

      <div>
        <span>[{index + 1}]</span>

        <div>
          <strong>{source.filename}</strong>

          {displayPage !== null && (
            <span>
              {" · "}
              Page {displayPage}
            </span>
          )}

          {source.chunk_index !== undefined && (
            <span>
              {" · "}
              Chunk {source.chunk_index}
            </span>
          )}
        </div>
      </div>

      {/* ------------------------------------------ */}
      {/* Evidence toggle */}
      {/* ------------------------------------------ */}

      {source.content && (
        <button
          type="button"
          onClick={() => setShowEvidence((previous) => !previous)}
          aria-expanded={showEvidence}
        >
          {showEvidence ? "Hide evidence" : "Show evidence"}
        </button>
      )}

      {/* ------------------------------------------ */}
      {/* Evidence */}
      {/* ------------------------------------------ */}

      {showEvidence && source.content && (
        <div>
          <p>{source.content}</p>
        </div>
      )}
    </article>
  );
}
