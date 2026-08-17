from langsmith import Client, evaluate

from evaluation.config import DATASET_NAME
from evaluation.target import target
from evaluation.evaluators import evaluate_rag


def run_one_example():
    client = Client()

    # --------------------------------------------------------
    # Fetch exactly ONE example from the existing dataset
    # --------------------------------------------------------

    examples = client.list_examples(
        dataset_name=DATASET_NAME,
    )

    first_example = next(examples, None)

    if first_example is None:
        raise RuntimeError(
            f"No examples found in dataset: {DATASET_NAME}"
        )

    print("=" * 70)
    print("DRY RUN — ONE LANGSMITH EXAMPLE")
    print("=" * 70)

    print("\nExample ID:")
    print(first_example.id)

    print("\nQuestion:")
    print(first_example.inputs["question"])

    print("\nReference answer:")
    print(
        first_example.outputs.get("answer")
        if first_example.outputs
        else None
    )

    # --------------------------------------------------------
    # Evaluate ONLY this example
    # --------------------------------------------------------

    results = evaluate(
        target,
        data=[first_example],
        evaluators=[
            evaluate_rag,
        ],
        experiment_prefix="rag-qna-dry-run",
        max_concurrency=1,
    )

    print("\n" + "=" * 70)
    print("DRY RUN COMPLETED")
    print("=" * 70)

    print(results)

    return results


if __name__ == "__main__":
    run_one_example()