const API_URL = import.meta.env.VITE_API_URL || "http://localhost:4000";

interface RpcResponse<T> {
  success: boolean;
  data: T;
  error: string | null;
}

export async function rpc<T>(action: string, payload: Record<string, unknown> = {}): Promise<T> {
  const response = await fetch(`${API_URL}/rpc`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, payload }),
  });

  const data: RpcResponse<T> = await response.json();
  if (!data.success) {
    throw new Error(data.error || "Unknown error");
  }
  return data.data;
}
