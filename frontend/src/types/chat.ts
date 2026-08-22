import type { Source } from "./query";

export type ChatMessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: ChatMessageRole;
  content: string;
  sources?: Source[];
}
