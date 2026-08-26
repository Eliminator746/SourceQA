import { useAuth } from "../context/AuthContext";

import { useDocuments } from "../hooks/useDocuments";
import { useQuery } from "../hooks/useQuery";
import { useConversation } from "../hooks/useConversation";

import DocumentPanel from "../components/documents/DocumentPanel";
import ChatPanel from "../components/chat/ChatPanel";
import QuestionInput from "../components/chat/QuestionInput";

export default function ChatPage() {
  // ==========================================================
  // Documents
  // ==========================================================

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

  // ==========================================================
  // Query / streaming
  // ==========================================================

  const {
    ask,
    isLoading: queryLoading,
    error: queryError,
    clearError,
  } = useQuery();

  // ==========================================================
  // Conversation state
  // ==========================================================

  const {
    messages,
    conversationId,

    addUserMessage,
    updateConversationId,

    startAssistantMessage,
    updateAssistantMessage,
    appendAssistantToken,
    completeAssistantMessage,
    updateAssistantSources,

    removeMessage,
    clearConversation,
  } = useConversation();

  const { user, logout } = useAuth();

  // ==========================================================
  // Document readiness
  // ==========================================================

  const hasReadyDocuments = documents.some((doc) => doc.status === "ready");

  const hasProcessingDocuments = documents.some(
    (doc) => doc.status === "processing",
  );

  // ==========================================================
  // Question handler
  // ==========================================================

  const handleQuestion = async (question: string): Promise<boolean> => {
    // --------------------------------------------------------
    // Clear previous error
    // --------------------------------------------------------

    clearError();

    // --------------------------------------------------------
    // Add user message immediately
    // --------------------------------------------------------

    addUserMessage(question);

    // --------------------------------------------------------
    // Create empty assistant message.
    //
    // This message will receive streamed tokens.
    // --------------------------------------------------------

    const assistantMessageId = startAssistantMessage();

    // --------------------------------------------------------
    // Start streaming request
    // --------------------------------------------------------

    const response = await ask(question, conversationId, {
      // --------------------------------------------------
      // Conversation ID
      // --------------------------------------------------

      onConversationId: (id) => {
        updateConversationId(id);
      },

      // --------------------------------------------------
      // Status
      // --------------------------------------------------

      onStatus: (status) => {
        updateAssistantMessage(assistantMessageId, {
          status,
        });
      },

      // --------------------------------------------------
      // Stream token
      // --------------------------------------------------

      onToken: (text) => {
        appendAssistantToken(assistantMessageId, text);
      },

      // --------------------------------------------------
      // Sources
      // --------------------------------------------------

      onSources: (sources) => {
        updateAssistantSources(assistantMessageId, sources);
      },
    });

    // --------------------------------------------------------
    // Stream failed
    // --------------------------------------------------------

    if (!response) {
      removeMessage(assistantMessageId);

      return false;
    }

    // --------------------------------------------------------
    // Stream completed
    // --------------------------------------------------------

    completeAssistantMessage(assistantMessageId, response);

    return true;
  };

  // ==========================================================
  // Render
  // ==========================================================

  return (
    <div className="h-screen flex flex-col bg-gray-50 overflow-hidden">
      {/* ====================================================
          Header
          ==================================================== */}

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

        <div className="flex items-center gap-3">
          {/* ==================================================
              New Chat
              ================================================== */}

          <button
            type="button"
            onClick={() => {
              clearConversation();
              clearError();
            }}
            disabled={queryLoading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:border-indigo-200 hover:text-indigo-600 hover:bg-indigo-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            <span className="text-sm leading-none">+</span>
            New Chat
          </button>

          {/* ==================================================
              User
              ================================================== */}

          <span className="text-sm text-gray-600 hidden sm:block">
            {user?.email}
          </span>

          {/* ==================================================
              Logout
              ================================================== */}

          <button
            type="button"
            onClick={logout}
            className="text-sm text-gray-500 hover:text-red-500 font-medium transition"
          >
            Logout
          </button>
        </div>
      </header>

      {/* ======================================================
          Main
          ====================================================== */}

      <main className="flex flex-1 overflow-hidden">
        {/* ====================================================
            Chat area
            ==================================================== */}

        <section className="flex flex-col flex-1 overflow-hidden">
          <ChatPanel messages={messages} />

          {/* ==================================================
              Query error
              ================================================== */}

          {queryError && (
            <div
              role="alert"
              className="mx-4 mb-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2 shrink-0"
            >
              {queryError}
            </div>
          )}

          {/* ==================================================
              Document processing
              ================================================== */}

          {hasProcessingDocuments && !hasReadyDocuments && (
            <div
              role="status"
              className="mx-4 mb-2 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 shrink-0"
            >
              ⏳ Your document is being indexed. The question input will unlock
              once it is ready.
            </div>
          )}

          {/* ==================================================
              Question input
              ================================================== */}

          <QuestionInput
            onAsk={handleQuestion}
            disabled={!hasReadyDocuments}
            isLoading={queryLoading}
          />
        </section>

        {/* ====================================================
            Document panel
            ==================================================== */}

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
