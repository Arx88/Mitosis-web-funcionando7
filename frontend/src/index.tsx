import './index.css';
import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { AppContextProvider } from "./context/AppContext";

const container = document.getElementById("root");
const root = createRoot(container!);
root.render(
  <AppContextProvider>
    <App />
  </AppContextProvider>
);