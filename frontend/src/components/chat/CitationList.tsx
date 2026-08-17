import type { Source } from "../../types/query";

interface CitationListProps {
  sources: Source[];
}

export default function CitationList({ sources }: CitationListProps) {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <section aria-label="Sources">
      <h2>Sources</h2>

      <div>
        {sources.map((source, index) => (
          <article key={`${source.filename}-${source.chunk_index ?? index}`}>
            <div>
              <strong>{source.filename}</strong>

              {source.page_label && <span> · Page {source.page_label}</span>}
            </div>

            {source.page !== undefined && <small>Page {source.page + 1}</small>}
          </article>
        ))}
      </div>
    </section>
  );
}
