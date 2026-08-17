import os
from pathlib import Path

from dotenv import load_dotenv


env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)


# ============================================================
# LangSmith
# ============================================================

DATASET_NAME = os.getenv(
    "DATASET_NAME",
    "RAG Q&A Evaluation",
)


# ============================================================
# Evaluation corpus
# ============================================================

# The evaluation dataset contains questions, but the questions
# themselves do not tell our target which documents to search.
#
# Therefore, all evaluation questions must run against the same
# controlled evaluation corpus.
#
# Set this to the user_id whose documents are indexed in Chroma
# for evaluation.
EVAL_USER_ID = os.getenv(
    "EVAL_USER_ID",
    "test-user-001",
)


# ============================================================
# Judge model
# ============================================================

# Used later by evaluation/judge.py
#
# We deliberately use the cheaper/higher-RPD Flash-Lite model
# for offline evaluation instead of the production model.

JUDGE_MODEL = os.getenv(
    "JUDGE_MODEL",
    "gemini-3.5-flash-lite",
)


# ============================================================
# Evaluation switches
# ============================================================

RUN_RETRIEVAL_RELEVANCE = True

RUN_GROUNDEDNESS = True

RUN_ANSWER_RELEVANCE = True

RUN_CORRECTNESS = True


# ============================================================
# Evaluation execution
# ============================================================

# Keep this at 1 because of the Gemini free-tier RPM limit.
MAX_CONCURRENCY = 1

# One evaluation run only.
NUM_REPETITIONS = 1


# ============================================================
# Retrieval configuration
# ============================================================

SEMANTIC_K = 20

BM25_K = 20

RERANK_K = 5


# ============================================================
# Experiment metadata
# ============================================================

EXPERIMENT_PREFIX = os.getenv(
    "LANGSMITH_EXPERIMENT_PREFIX",
    "rag-qna-evaluation",
)