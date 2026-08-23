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

  const {
    messages,
    conversationId,
    addUserMessage,
    addAssistantMessage,
    clearConversation,
  } = useConversation();

  const { user, logout } = useAuth();

  const hasReadyDocuments = documents.some((doc) => doc.status === "ready");
  const hasProcessingDocuments = documents.some(
    (doc) => doc.status === "processing",
  );

  const handleQuestion = async (question: string): Promise<boolean> => {
    clearError();
    addUserMessage(question);
    const response = await ask(question, conversationId);
    if (!response) return false;
    addAssistantMessage(response);
    return true;
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50 overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 bg-white border-b border-gray-200 shadow-sm shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <span className="text-white text-sm font-bold">R</span>
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900 leading-tight">
              RAG Q&amp;A
            </h1>
            <p className="text-xs text-gray-500 leading-tight">
              Ask questions about your documents
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600 hidden sm:block">
            {user?.email}
          </span>
          <button
            type="button"
            onClick={logout}
            className="text-sm text-gray-500 hover:text-red-500 font-medium transition"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main */}
      <main className="flex flex-1 overflow-hidden">
        {/* Chat area */}
        <section className="flex flex-col flex-1 overflow-hidden">
          <ChatPanel messages={messages} />

          {queryError && (
            <div
              role="alert"
              className="mx-4 mb-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2 shrink-0"
            >
              {queryError}
            </div>
          )}

          {hasProcessingDocuments && !hasReadyDocuments && (
            <div
              role="status"
              className="mx-4 mb-2 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 shrink-0"
            >
              ⏳ Your document is being indexed. The question input will unlock
              once it is ready.
            </div>
          )}

          <QuestionInput
            onAsk={handleQuestion}
            disabled={!hasReadyDocuments}
            isLoading={queryLoading}
          />

          {messages.length > 0 && (
            <div className="px-4 pb-2 shrink-0 text-center">
              <button
                type="button"
                onClick={clearConversation}
                className="text-xs text-gray-400 hover:text-red-500 transition"
              >
                Clear conversation
              </button>
            </div>
          )}
        </section>

        {/* Document panel */}
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
