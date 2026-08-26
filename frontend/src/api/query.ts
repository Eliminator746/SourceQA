import apiClient from "./client";

import type { QueryRequest, QueryResponse, Source } from "../types/query";

// ============================================================
// Normal non-streaming API
// ============================================================

export const askQuestion = async (
  data: QueryRequest,
): Promise<QueryResponse> => {
  const response = await apiClient.post<QueryResponse>("/api/query", data);

  return response.data;
};

// ============================================================
// Streaming API
// ============================================================

export type StreamStatus = "searching" | "generating";

export interface StreamHandlers {
  onConversationId?: (conversationId: string) => void;

  onStatus?: (status: StreamStatus) => void;

  onToken?: (text: string) => void;

  onSources?: (sources: Source[]) => void;
}

// ============================================================
// SSE event payload
// ============================================================

interface StreamEvent {
  conversation_id?: string;
  status?: StreamStatus;
  text?: string;
  sources?: Source[];
  message?: string;
}

// ============================================================
// Streaming error handling
// ============================================================

function getStreamErrorMessage(status: number, payload: unknown): string {
  if (
    payload &&
    typeof payload === "object" &&
    "detail" in payload &&
    typeof payload.detail === "string"
  ) {
    return payload.detail;
  }

  if (status === 401) {
    localStorage.removeItem("access_token");

    window.location.href = "/login";

    return "Your session has expired. " + "Please log in again.";
  }

  if (status === 429) {
    return (
      "The AI service is temporarily unavailable. " + "Please try again later."
    );
  }

  if (status >= 500) {
    return (
      "Something went wrong while generating " + "the answer. Please try again."
    );
  }

  return "Unable to process the request. " + "Please try again.";
}

// ============================================================
// Parse one SSE block
// ============================================================

function parseSseBlock(block: string): {
  event: string;
  data: StreamEvent;
} | null {
  let event = "message";

  const dataLines: string[] = [];

  for (const line of block.split(/\r?\n/)) {
    if (line.startsWith("event:")) {
      event = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trimStart());
    }
  }

  if (dataLines.length === 0) {
    return null;
  }

  try {
    return {
      event,
      data: JSON.parse(dataLines.join("\n")) as StreamEvent,
    };
  } catch {
    return null;
  }
}

// ============================================================
// Real streaming conversational RAG
// ============================================================

/**
 * Stream a conversational RAG response from:
 *
 *     POST /api/query/stream
 *
 * Fetch is used instead of EventSource because the endpoint:
 *
 * 1. Uses POST
 * 2. Requires a JSON request body
 * 3. Requires a Bearer token
 */
export const streamQuestion = async (
  data: QueryRequest,
  handlers: StreamHandlers = {},
): Promise<QueryResponse> => {
  // ----------------------------------------------------------
  // JWT
  // ----------------------------------------------------------

  const token = localStorage.getItem("access_token");

  // ----------------------------------------------------------
  // API base URL
  // ----------------------------------------------------------

  const baseUrl = apiClient.defaults.baseURL ?? "http://localhost:8000";

  // ----------------------------------------------------------
  // Streaming request
  // ----------------------------------------------------------

  const response = await fetch(`${baseUrl}/api/query/stream`, {
    method: "POST",

    headers: {
      "Content-Type": "application/json",

      Accept: "text/event-stream",

      ...(token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {}),
    },

    body: JSON.stringify(data),
  });

  // ----------------------------------------------------------
  // HTTP error
  // ----------------------------------------------------------

  if (!response.ok) {
    let payload: unknown = null;

    try {
      payload = await response.json();
    } catch {
      // Ignore non-JSON error responses.
    }

    throw new Error(getStreamErrorMessage(response.status, payload));
  }

  // ----------------------------------------------------------
  // Streaming body must exist
  // ----------------------------------------------------------

  if (!response.body) {
    throw new Error("The server did not provide a streaming response.");
  }

  // ----------------------------------------------------------
  // Reader
  // ----------------------------------------------------------

  const reader = response.body.getReader();

  const decoder = new TextDecoder();

  // ----------------------------------------------------------
  // Stream state
  // ----------------------------------------------------------

  let buffer = "";

  let answer = "";

  let conversationId = data.conversation_id ?? "";

  let sources: Source[] = [];

  let streamError: string | null = null;

  // ==========================================================
  // Process one complete SSE block
  // ==========================================================

  const processBlock = (block: string) => {
    const parsed = parseSseBlock(block);

    if (!parsed) {
      return;
    }

    const { event, data: eventData } = parsed;

    switch (event) {
      // ------------------------------------------------------
      // Conversation ID
      // ------------------------------------------------------

      case "conversation":
        if (eventData.conversation_id) {
          conversationId = eventData.conversation_id;

          handlers.onConversationId?.(conversationId);
        }

        break;

      // ------------------------------------------------------
      // Status
      // ------------------------------------------------------

      case "status":
        if (eventData.status) {
          handlers.onStatus?.(eventData.status);
        }

        break;

      // ------------------------------------------------------
      // Token
      // ------------------------------------------------------

      case "token":
        if (eventData.text) {
          answer += eventData.text;

          handlers.onToken?.(eventData.text);
        }

        break;

      // ------------------------------------------------------
      // Sources
      // ------------------------------------------------------

      case "sources":
        if (Array.isArray(eventData.sources)) {
          sources = eventData.sources;

          handlers.onSources?.(sources);
        }

        break;

      // ------------------------------------------------------
      // Error
      // ------------------------------------------------------

      case "error":
        streamError =
          eventData.message ??
          "Something went wrong " + "while generating the answer.";

        break;

      // ------------------------------------------------------
      // Done
      // ------------------------------------------------------

      case "done":
        if (eventData.conversation_id) {
          conversationId = eventData.conversation_id;

          handlers.onConversationId?.(conversationId);
        }

        if (Array.isArray(eventData.sources)) {
          sources = eventData.sources;

          handlers.onSources?.(sources);
        }

        break;

      default:
        break;
    }
  };

  // ==========================================================
  // Read stream
  // ==========================================================

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(value, {
        stream: true,
      });

      // ------------------------------------------------------
      // SSE events are separated by a blank line.
      // ------------------------------------------------------

      const blocks = buffer.split(/\r?\n\r?\n/);

      // Keep incomplete block.
      buffer = blocks.pop() ?? "";

      // Process completed blocks.
      for (const block of blocks) {
        processBlock(block);

        if (streamError) {
          break;
        }
      }

      if (streamError) {
        break;
      }
    }

    // --------------------------------------------------------
    // Flush decoder
    // --------------------------------------------------------

    buffer += decoder.decode();

    if (buffer.trim()) {
      processBlock(buffer);
    }
  } finally {
    reader.releaseLock();
  }

  // ==========================================================
  // Stream error
  // ==========================================================

  if (streamError) {
    throw new Error(streamError);
  }

  // ==========================================================
  // Safety check
  // ==========================================================

  if (!conversationId) {
    throw new Error("The stream completed without " + "a conversation ID.");
  }

  // ==========================================================
  // Final response
  // ==========================================================

  return {
    conversation_id: conversationId,

    answer,

    sources,
  };
};
