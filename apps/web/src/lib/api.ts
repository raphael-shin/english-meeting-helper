const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface TranslateRequest {
  text: string;
}

export interface TranslateResponse {
  translatedText: string;
}

export async function translateKoToEn(
  text: string
): Promise<TranslateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/translate/ko-en`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text } as TranslateRequest),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: "Unknown error",
    }));
    throw new Error(error.detail || `Translation failed: ${response.status}`);
  }

  return response.json();
}

export async function getHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json();
}
