import type { Source } from "../../types/query";
import { useTypewriter } from "../../hooks/useTypewriter";

interface AnswerCardProps {
  answer: string;
  sources?: Source[];
}

export default function AnswerCard({ answer, sources }: AnswerCardProps) {
  const displayed = useTypewriter(answer);
  const isTyping = displayed.length < answer.length;

  if (!answer.trim()) return null;

  return (
    <div className="text-sm text-gray-800 leading-relaxed">
      <span className="whitespace-pre-wrap">
        {displayed}
        {isTyping && (
          <span className="inline-block w-0.5 h-4 bg-indigo-500 ml-0.5 animate-pulse align-middle" />
        )}
      </span>
      {!isTyping && sources && sources.length > 0 && (
        <span className="ml-1">
          {sources.map((source, index) => (
            <span
              key={`${source.document_id}-${index}`}
              className="relative group/cite inline-block mx-0.5"
            >
              <span className="text-indigo-500 font-semibold text-xs cursor-help select-none">
                [{index + 1}]
              </span>
              {/* Tooltip: filename + page only, no chunk */}
              <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2.5 py-1.5 bg-gray-900 text-white text-xs rounded-lg whitespace-nowrap shadow-xl opacity-0 group-hover/cite:opacity-100 transition-opacity duration-150 pointer-events-none z-20">
                {source.filename}
                {source.page !== undefined && source.page !== null
                  ? ` — Page ${source.page}`
                  : ""}
              </span>
            </span>
          ))}
        </span>
      )}
    </div>
  );
}
