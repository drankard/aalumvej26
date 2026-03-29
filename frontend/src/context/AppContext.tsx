import { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { rpc } from "../api/client";

interface Greeting {
  id: string;
  name: string;
  message: string;
  created_at: string;
}

interface AppState {
  greetings: Greeting[];
  loading: boolean;
  error: string | null;
  sendHello: (name: string) => Promise<void>;
  loadGreetings: () => Promise<void>;
}

const AppContext = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [greetings, setGreetings] = useState<Greeting[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendHello = useCallback(async (name: string) => {
    setLoading(true);
    setError(null);
    try {
      const greeting = await rpc<Greeting>("hello", { name });
      setGreetings((prev) => [greeting, ...prev]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadGreetings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await rpc<Greeting[]>("list_greetings");
      setGreetings(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <AppContext.Provider value={{ greetings, loading, error, sendHello, loadGreetings }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
