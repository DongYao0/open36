import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./index.css";

// 提前应用主题，避免刷新闪烁（与 Vue 应用共享 open436_theme）
;(() => {
  try {
    const raw = localStorage.getItem("open436_theme");
    const t = raw ? JSON.parse(raw) : "light";
    document.documentElement.setAttribute("data-theme", t === "dark" ? "dark" : "light");
  } catch {
    document.documentElement.setAttribute("data-theme", "light");
  }
})();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
