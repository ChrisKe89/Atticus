export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  status?: "pending" | "complete" | "error";
  response?: import("@/lib/ask-contract").AskResponse;
  error?: string;
  question?: string;
}

export interface ChatSession {
  id: string;
  title?: string;
  createdAt: number;
  updatedAt: number;
  messages: ChatMessage[];
}
