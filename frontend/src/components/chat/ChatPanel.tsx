import { useQuery } from "../../hooks/useQuery";

import QuestionInput from "./QuestionInput";
import AnswerCard from "./AnswerCard";
import CitationList from "./CitationList";

interface ChatPanelProps {
  hasDocuments: boolean;
}

export default function ChatPanel({ hasDocuments }: ChatPanelProps) {
  const { response, isLoading, error, ask } = useQuery();

  return (
    <section>
      <header>
        <h2>Ask questions</h2>

        <p>Ask questions based on your uploaded documents.</p>
      </header>

      {!hasDocuments && (
        <div>
          <p>Upload at least one document before asking a question.</p>
        </div>
      )}

      <QuestionInput
        onAsk={ask}
        disabled={!hasDocuments}
        isLoading={isLoading}
      />

      {error && (
        <div role="alert">
          <p>{error}</p>
        </div>
      )}

      {response && (
        <div>
          <AnswerCard answer={response.answer} />

          <CitationList sources={response.sources} />
        </div>
      )}
    </section>
  );
}
