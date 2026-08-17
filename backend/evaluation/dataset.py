"""
Create the LangSmith evaluation dataset for the RAG Q&A project.

Evaluation corpus:
    Stock_Market_Performance_2024.pdf

The dataset intentionally contains:
    - 3 answerable questions
    - 2 unanswerable questions
    - 2 multi-hop questions
    - 2 paraphrased questions
    - 1 citation-sensitive question

Important:
    These examples are evaluation data, not training data.
    The reference answers are grounded only in the supplied PDF.
"""

from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)


DATASET_NAME = "RAG Q&A - Stock Market Performance 2024 Evaluation"

DATASET_DESCRIPTION = (
    "10-example evaluation dataset for the RAG Q&A application. "
    "Questions are grounded in Stock_Market_Performance_2024.pdf "
    "and cover answerable, unanswerable, multi-hop, paraphrased, "
    "and citation-sensitive cases."
)


EXAMPLES = [
    # =========================================================
    # 1. Answerable — direct factual retrieval
    # =========================================================
    {
        "inputs": {
            "question": (
                "What was the S&P 500's total return in 2024, "
                "and how did the Nasdaq Composite perform?"
            )
        },
        "outputs": {
            "answer": (
                "The S&P 500 delivered roughly a 25% total return "
                "in 2024, while the Nasdaq Composite rose nearly 29%."
            )
        },
        "metadata": {
            "type": "answerable",
            "difficulty": "easy",
            "expected_sources": ["page_1"],
        },
    },

    # =========================================================
    # 2. Answerable — company-specific retrieval
    # =========================================================
    {
        "inputs": {
            "question": (
                "Why did Amazon's stock rise roughly 48% in 2024?"
            )
        },
        "outputs": {
            "answer": (
                "Amazon benefited from solid online shopping demand "
                "and Prime membership growth, continued strength and "
                "profitability in AWS, and sharply improved earnings "
                "from cost cutting, efficiency measures, and revenue growth."
            )
        },
        "metadata": {
            "type": "answerable",
            "difficulty": "medium",
            "expected_sources": ["page_3", "page_4"],
        },
    },

    # =========================================================
    # 3. Answerable — risk/fundamentals
    # =========================================================
    {
        "inputs": {
            "question": (
                "Why did the report describe Tesla's 2024 stock "
                "performance as a disconnect from its fundamentals?"
            )
        },
        "outputs": {
            "answer": (
                "Tesla's stock gained about 63% even though full-year "
                "EPS fell by more than 50%, while profit margins and "
                "net income also declined. By year-end, the stock was "
                "trading at well over 100 times trailing earnings, "
                "highlighting the gap between the soaring share price "
                "and shrinking earnings."
            )
        },
        "metadata": {
            "type": "answerable",
            "difficulty": "medium",
            "expected_sources": ["page_5", "page_6"],
        },
    },

    # =========================================================
    # 4. Unanswerable — deliberately absent exact metric
    # =========================================================
    {
        "inputs": {
            "question": (
                "What was Microsoft's exact revenue growth percentage "
                "in 2024?"
            )
        },
        "outputs": {
            "answer": (
                "I don't have the answer based on the provided documents."
            )
        },
        "metadata": {
            "type": "unanswerable",
            "difficulty": "medium",
            "reason": (
                "Microsoft is listed as a Magnificent 7 company, "
                "but the report does not provide an exact Microsoft "
                "revenue-growth percentage."
            ),
        },
    },

    # =========================================================
    # 5. Unanswerable — related topic, unsupported exact fact
    # =========================================================
    {
        "inputs": {
            "question": (
                "What was Nvidia's exact revenue growth percentage "
                "in 2024?"
            )
        },
        "outputs": {
            "answer": (
                "I don't have the answer based on the provided documents."
            )
        },
        "metadata": {
            "type": "unanswerable",
            "difficulty": "medium",
            "reason": (
                "The report states that Nvidia's stock rose about 170% "
                "and discusses demand for AI-focused chips, but it does "
                "not provide an exact 2024 revenue-growth percentage."
            ),
        },
    },

    # =========================================================
    # 6. Multi-hop — combine market overview + Tesla section
    # =========================================================
    {
        "inputs": {
            "question": (
                "How did Tesla contribute to the broader 2024 market "
                "rally, and what made its performance risky compared "
                "with the fundamentals described in the report?"
            )
        },
        "outputs": {
            "answer": (
                "Tesla's stock gained approximately 63% and was a "
                "significant contributor to the S&P 500's performance. "
                "At the same time, its EPS fell by more than 50%, profit "
                "margins and net income declined, and the stock traded "
                "at well over 100 times trailing earnings, making the "
                "disconnect between price and fundamentals a risk."
            )
        },
        "metadata": {
            "type": "multi_hop",
            "difficulty": "hard",
            "expected_sources": ["page_1", "page_5", "page_6"],
        },
    },

    # =========================================================
    # 7. Multi-hop — compare Meta and Tesla
    # =========================================================
    {
        "inputs": {
            "question": (
                "Compare Meta and Tesla's 2024 stock gains and explain "
                "how their earnings trends affected the market's view "
                "of their valuations."
            )
        },
        "outputs": {
            "answer": (
                "Meta gained about 72% and had earnings growth of roughly "
                "60%, while its trailing P/E remained in the mid-20s, "
                "so its stock rise was supported by improving fundamentals. "
                "Tesla gained about 63%, but its EPS fell by more than 50% "
                "and its valuation rose to well over 100 times trailing "
                "earnings, creating a much larger disconnect between price "
                "and fundamentals."
            )
        },
        "metadata": {
            "type": "multi_hop",
            "difficulty": "hard",
            "expected_sources": ["page_4", "page_5", "page_6"],
        },
    },

    # =========================================================
    # 8. Paraphrased — same fact, different wording
    # =========================================================
    {
        "inputs": {
            "question": (
                "Which large technology company saw its share price "
                "increase by around 36% in 2024 while its valuation "
                "expanded to about 40 times trailing earnings?"
            )
        },
        "outputs": {
            "answer": (
                "Apple. Its stock climbed approximately 36% in 2024, "
                "and by year-end it was trading at about 40 times "
                "trailing earnings."
            )
        },
        "metadata": {
            "type": "paraphrased",
            "difficulty": "medium",
            "expected_sources": ["page_2"],
        },
    },

    # =========================================================
    # 9. Paraphrased — indirect wording / retrieval robustness
    # =========================================================
    {
        "inputs": {
            "question": (
                "Which high-growth AI/data company was the S&P 500's "
                "top performer, gaining roughly three-and-a-half times "
                "its starting value during 2024?"
            )
        },
        "outputs": {
            "answer": (
                "Palantir Technologies. Its stock rose about 340% in "
                "2024, making it the single best-performing stock in "
                "the S&P 500 for the year."
            )
        },
        "metadata": {
            "type": "paraphrased",
            "difficulty": "medium",
            "expected_sources": ["page_6"],
        },
    },

    # =========================================================
    # 10. Citation-sensitive — answer requires multiple sources
    # =========================================================
    {
        "inputs": {
            "question": (
                "What percentage did the Magnificent 7 contribute to the "
                "S&P 500's 2024 performance, which seven companies made up "
                "the group, and which page of the report contains these facts?"
            )
        },
        "outputs": {
            "answer": (
                "The Magnificent 7 accounted for about 54% of the S&P 500's "
                "2024 performance. The seven companies were Apple, Microsoft, "
                "Alphabet (Google), Amazon, Meta, Nvidia, and Tesla. These facts "
                "appear on page 1 of the report."
            )
        },
        "metadata": {
            "type": "citation_sensitive",
            "difficulty": "medium",
            "expected_sources": ["page_1"],
            "citation_requirement": (
                "The answer should cite the document section containing "
                "the Magnificent 7 composition and their contribution "
                "to S&P 500 performance."
            ),
        },
    },
]


def create_dataset() -> None:
    """Create the dataset and add all evaluation examples."""

    client = Client()

    # Check whether the dataset already exists.
    existing = list(
        client.list_datasets(
            dataset_name=DATASET_NAME,
        )
    )

    if existing:
        dataset = existing[0]
        print(
            f"Dataset already exists: "
            f"{DATASET_NAME} ({dataset.id})"
        )

        # Avoid accidentally duplicating the 10 examples
        # when this script is executed more than once.
        existing_examples = list(
            client.list_examples(
                dataset_id=dataset.id,
            )
        )

        if existing_examples:
            print(
                f"Dataset already contains "
                f"{len(existing_examples)} example(s). "
                "No new examples were added."
            )
            return

    else:
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description=DATASET_DESCRIPTION,
        )

        print(
            f"Created dataset: "
            f"{DATASET_NAME} ({dataset.id})"
        )

    client.create_examples(
        dataset_id=dataset.id,
        examples=EXAMPLES,
    )

    print(
        f"Created {len(EXAMPLES)} evaluation examples."
    )


if __name__ == "__main__":
    create_dataset()
