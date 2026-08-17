# This is where we execute our evaluation
from langsmith import evaluate

from evaluation.config import DATASET_NAME
from evaluation.target import target
from evaluation.evaluators import evaluate_rag


def run_evaluation():
    """
    Run the RAG evaluation against the LangSmith dataset.
    """

    print("=" * 60)
    print("Starting RAG evaluation")
    print("=" * 60)

    print(f"Dataset: {DATASET_NAME}")
    print()

    results = evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[
            evaluate_rag,
        ],
        experiment_prefix="rag-qna-evaluation",
        metadata={
            "evaluation_type": "offline",
            "project": "RAG Q&A",
        },
    )

    print()
    print("=" * 60)
    print("Evaluation completed")
    print("=" * 60)

    return results


if __name__ == "__main__":
    run_evaluation()