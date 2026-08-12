from pathlib import Path

from app.rag.loaders import load_document
from app.rag.ingestion import ingest_documents
from app.rag.agent import ask_agent


PDF_PATH = Path(r"C:\Users\anish\Downloads\Stock_Market_Performance_2024.pdf")

DOCUMENT_ID = "test-document-001"
USER_ID = "test-user-001"


# --------------------------------
# Read PDF
# --------------------------------

with open(PDF_PATH, "rb") as file:
    contents = file.read()


# --------------------------------
# Load document
# --------------------------------

documents = load_document(
    contents=contents,
    file_type="pdf",
    document_id=DOCUMENT_ID,
    user_id=USER_ID,
    filename=PDF_PATH.name
)

print(f"Loaded documents: {len(documents)}")


# --------------------------------
# Chunk + Embed + Chroma
# --------------------------------

chunks = ingest_documents(
    documents
)

print(f"Created chunks: {len(chunks)}")


# --------------------------------
# Ask Agent
# --------------------------------

question = "Which companies in the report experienced strong stock-price growth despite relatively weak or declining fundamentals, and what does the report say about the risks of this situation?"


answer = ask_agent(
    question=question,
    documents=chunks,
    user_id=USER_ID
)


print("\nQuestion:")
print(question)

print("\nAnswer:")
print(answer)