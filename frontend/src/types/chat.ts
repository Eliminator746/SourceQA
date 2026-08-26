import type { Source } from "./query";

export type ChatMessageRole = "user" | "assistant";

export type AssistantMessageStatus = "searching" | "generating" | "complete";

export interface ChatMessage {
  id: string;
  role: ChatMessageRole;
  content: string;
  sources?: Source[];
  status?: AssistantMessageStatus;
}
