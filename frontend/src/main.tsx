import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ContentProvider } from "./context/ContentContext";
import "./i18n";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ContentProvider>
      <App />
    </ContentProvider>
  </StrictMode>
);
