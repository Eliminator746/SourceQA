import { useState } from "react";

interface QuestionInputProps {
  onAsk: (question: string) => Promise<unknown>;
  disabled?: boolean;
  isLoading?: boolean;
}

export default function QuestionInput({
  onAsk,
  disabled = false,
  isLoading = false,
}: QuestionInputProps) {
  const [question, setQuestion] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = async (event: React.SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedQuestion = question.trim();

    setValidationError(null);

    if (!trimmedQuestion) {
      setValidationError("Please enter a question.");
      return;
    }

    if (disabled || isLoading) {
      return;
    }

    try {
      await onAsk(trimmedQuestion);

      // Clear the input only after the request
      // succeeds.
      setQuestion("");
    } catch {
      // useQuery handles the API error.
    }
  };

  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuestion(event.target.value);

    if (validationError) {
      setValidationError(null);
    }
  };

  const isDisabled = disabled || isLoading;

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="question">Ask a question</label>

      <textarea
        id="question"
        value={question}
        onChange={handleChange}
        placeholder={"Ask something about your documents..."}
        rows={4}
        disabled={isDisabled}
        maxLength={2000}
      />

      <div>
        <span>{question.length}/2000</span>

        <button type="submit" disabled={isDisabled || !question.trim()}>
          {isLoading ? "Thinking..." : "Ask"}
        </button>
      </div>

      {validationError && <p role="alert">{validationError}</p>}
    </form>
  );
}
