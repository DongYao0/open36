import { useState, useEffect } from "react";

const LS_KEY = "open436_theme";

function readTheme() {
  try {
    const v = JSON.parse(localStorage.getItem(LS_KEY));
    return v === "light" || v === "dark" ? v : "light";
  } catch {
    return "dark";
  }
}

function applyTheme(t) {
  document.documentElement.setAttribute("data-theme", t);
  localStorage.setItem(LS_KEY, JSON.stringify(t));
}

export function useTheme() {
  const [theme, setTheme] = useState(readTheme);
  const isDark = theme === "dark";

  const toggle = () => {
    const next = theme === "dark" ? "light" : "dark";
    applyTheme(next);
    setTheme(next);
  };

  // 跨标签页 / 跨应用（Vue）同步
  useEffect(() => {
    const onStorage = (e) => {
      if (e.key !== LS_KEY || !e.newValue) return;
      try {
        const v = JSON.parse(e.newValue);
        if (v === "light" || v === "dark") {
          setTheme(v);
          document.documentElement.setAttribute("data-theme", v);
        }
      } catch { /* ignore */ }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  return { theme, isDark, toggle };
}
