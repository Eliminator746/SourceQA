import CitationList from "./CitationList";

import type { Source } from "../../types/query";

interface AnswerCardProps {
  answer: string;
  sources?: Source[];
}

export default function AnswerCard({ answer, sources = [] }: AnswerCardProps) {
  if (!answer.trim()) return null;

  return (
    <div className="text-sm text-gray-800 leading-relaxed">
      <span className="whitespace-pre-wrap">{answer}</span>
      <CitationList sources={sources} />
    </div>
  );
}
