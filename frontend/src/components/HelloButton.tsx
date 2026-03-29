import { useEffect } from "react";
import { useApp } from "../context/AppContext";

export function HelloButton() {
  const { greetings, loading, error, sendHello, loadGreetings } = useApp();

  useEffect(() => {
    loadGreetings();
  }, [loadGreetings]);

  return (
    <div>
      <button
        onClick={() => sendHello("World")}
        disabled={loading}
        style={{ padding: "8px 20px", fontSize: 16, cursor: "pointer" }}
      >
        {loading ? "Sending..." : "Say Hello"}
      </button>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {greetings.length > 0 && (
        <ul style={{ listStyle: "none", padding: 0, marginTop: 20 }}>
          {greetings.map((g) => (
            <li key={g.id} style={{ padding: "6px 0", borderBottom: "1px solid #eee" }}>
              {g.message} — <small>{g.created_at}</small>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
