import { useAuth } from "../context/AuthContext";

import { useDocuments } from "../hooks/useDocuments";
import { useQuery } from "../hooks/useQuery";
import { useConversation } from "../hooks/useConversation";

import DocumentPanel from "../components/documents/DocumentPanel";

import ChatPanel from "../components/chat/ChatPanel";
import QuestionInput from "../components/chat/QuestionInput";

export default function ChatPage() {
  const {
    documents,
    count,
    maxSources,
    isLoading: documentsLoading,
    isUploading,
    error: documentError,
    upload,
    remove,
  } = useDocuments();

  const {
    ask,
    isLoading: queryLoading,
    error: queryError,
    clearError,
  } = useQuery();

  const { messages, addUserMessage, addAssistantMessage, clearConversation } =
    useConversation();

  const { user, logout } = useAuth();

  const hasDocuments = documents.length > 0;

  const handleQuestion = async (question: string): Promise<boolean> => {
    clearError();

    // Immediately show the user's question.
    addUserMessage(question);

    const response = await ask(question);

    if (!response) {
      // User message stays in conversation.
      return false;
    }

    addAssistantMessage(response);

    return true;
  };

  return (
    <div className="chat-page">
      {/* -------------------------------------- */}
      {/* Header */}
      {/* -------------------------------------- */}

      <header className="chat-header">
        <div>
          <h1>RAG Q&A</h1>

          <p>Ask questions about your documents</p>
        </div>

        <div>
          <span>{user?.email}</span>

          <button type="button" onClick={logout}>
            Logout
          </button>
        </div>
      </header>

      {/* -------------------------------------- */}
      {/* Main */}
      {/* -------------------------------------- */}

      <main className="chat-main">
        {/* ---------------------------------- */}
        {/* Q&A */}
        {/* ---------------------------------- */}

        <section>
          <ChatPanel messages={messages} />

          {queryError && (
            <div role="alert">
              <p>{queryError}</p>
            </div>
          )}

          <QuestionInput
            onAsk={handleQuestion}
            disabled={!hasDocuments}
            isLoading={queryLoading}
          />

          {messages.length > 0 && (
            <button type="button" onClick={clearConversation}>
              Clear conversation
            </button>
          )}
        </section>

        {/* ---------------------------------- */}
        {/* Documents */}
        {/* ---------------------------------- */}

        <DocumentPanel
          documents={documents}
          count={count}
          maxSources={maxSources}
          isLoading={documentsLoading}
          isUploading={isUploading}
          error={documentError}
          onUpload={upload}
          onDelete={remove}
        />
      </main>
    </div>
  );
}
