interface AnswerCardProps {
  answer: string;
}

export default function AnswerCard({ answer }: AnswerCardProps) {
  if (!answer.trim()) {
    return null;
  }

  return (
    <section aria-label="Answer">
      <h2>Answer</h2>

      <div>
        <p>{answer}</p>
      </div>
    </section>
  );
}
