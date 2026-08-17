import { useAuth } from "../context/AuthContext";
import { useDocuments } from "../hooks/useDocuments";

import DocumentPanel from "../components/documents/DocumentPanel";
import ChatPanel from "../components/chat/ChatPanel";

export default function ChatPage() {
  const {
    documents,
    count,
    maxSources,
    isLoading,
    isUploading,
    error,
    upload,
    remove,
  } = useDocuments();

  const { user, logout } = useAuth();

  return (
    <div className="chat-page">
      {/* ------------------------------------------ */}
      {/* Header */}
      {/* ------------------------------------------ */}

      <header className="chat-header">
        <div>
          <h1>RAG Q&A</h1>

          <p>Ask questions about your documents</p>
        </div>

        <div className="chat-header-user">
          <span>{user?.email}</span>

          <button type="button" onClick={logout}>
            Logout
          </button>
        </div>
      </header>

      {/* ------------------------------------------ */}
      {/* Main */}
      {/* ------------------------------------------ */}

      <main className="chat-main">
        <ChatPanel hasDocuments={documents.length > 0} />

        <DocumentPanel
          documents={documents}
          count={count}
          maxSources={maxSources}
          isLoading={isLoading}
          isUploading={isUploading}
          error={error}
          onUpload={upload}
          onDelete={remove}
        />
      </main>
    </div>
  );
}
