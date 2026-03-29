import { AppProvider } from "./context/AppContext";
import { HelloButton } from "./components/HelloButton";

function App() {
  return (
    <AppProvider>
      <div style={{ maxWidth: 600, margin: "40px auto", fontFamily: "system-ui" }}>
        <h1>Aalumvej26</h1>
        <HelloButton />
      </div>
    </AppProvider>
  );
}

export default App;
