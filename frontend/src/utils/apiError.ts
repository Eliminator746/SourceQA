import axios from "axios";

// This is especially useful because our document API has several meaningful backend errors—unsupported file type, 10 MB limit, maximum 5 documents, S3 failure, etc

interface FastAPIErrorResponse {
  detail?: string | Record<string, unknown> | Array<unknown>;
}

export function getApiErrorMessage(
  error: unknown,
  fallback = "Something went wrong. Please try again.",
): string {
  if (!axios.isAxiosError<FastAPIErrorResponse>(error)) {
    return fallback;
  }

  const detail = error.response?.data?.detail;

  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === "object" && item !== null && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }

        return null;
      })
      .filter((message): message is string => Boolean(message));

    if (messages.length > 0) {
      return messages.join(", ");
    }
  }

  if (detail && typeof detail === "object") {
    return JSON.stringify(detail);
  }

  if (error.response?.status === 401) {
    return "Your session has expired. Please log in again.";
  }

  if (error.response?.status === 403) {
    return "You do not have permission to perform this action.";
  }

  if (error.response?.status === 404) {
    return "The requested resource was not found.";
  }

  if (error.response?.status === 409) {
    return "This request conflicts with existing data.";
  }

  if (error.response?.status && error.response.status >= 500) {
    return "The server encountered an error. Please try again later.";
  }

  if (error.message) {
    return error.message;
  }

  return fallback;
}
