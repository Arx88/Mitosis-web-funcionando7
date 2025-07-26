import './index.css';
import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { AppContextProvider } from "./context/AppContext";

// Debugging para producción
console.log("🚀 Starting React application mounting...");
console.log("📊 Environment variables:", {
  VITE_BACKEND_URL: import.meta.env.VITE_BACKEND_URL,
  REACT_APP_BACKEND_URL: import.meta.env.REACT_APP_BACKEND_URL,
  MODE: import.meta.env.MODE,
  PROD: import.meta.env.PROD
});

try {
  const container = document.getElementById("root");
  console.log("📍 Root element found:", !!container, container);
  
  if (!container) {
    throw new Error("Root element not found");
  }

  console.log("🏗️ Creating React root...");
  const root = createRoot(container);
  
  console.log("🎨 Rendering React app...");
  root.render(
    <React.StrictMode>
      <AppContextProvider>
        <App />
      </AppContextProvider>
    </React.StrictMode>
  );
  
  console.log("✅ React app mounted successfully!");
} catch (error) {
  console.error("❌ React mounting failed:", error);
  
  // Fallback: mostrar error en el DOM
  const container = document.getElementById("root");
  if (container) {
    container.innerHTML = `
      <div style="padding: 20px; color: red; font-family: monospace;">
        <h2>React Mounting Error</h2>
        <p>Error: ${error.message}</p>
        <p>Check browser console for more details.</p>
      </div>
    `;
  }
}