import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import { HomepageProvider } from "./context/HomepageContext";
import "./index.css";

// 固定黑夜模式（无明暗切换），主题由 index.css 的 :root 定义
document.documentElement.setAttribute("data-theme", "dark");

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <HomepageProvider>
      <App />
    </HomepageProvider>
  </React.StrictMode>
);
