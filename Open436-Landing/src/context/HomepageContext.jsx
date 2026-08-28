import React, { createContext, useContext, useEffect, useState } from "react";

// 首页内容上下文：启动时拉取后台配置，逐模块 fallback 到 constants 默认值
// 后端不可用/模块未配置时首页展示默认内容，永不空白
const HomepageContext = createContext(null);

export const HomepageProvider = ({ children }) => {
  // null=加载中, {}=已加载（可能为空，空则全走默认值）
  const [data, setData] = useState(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/users/homepage/public")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error("http " + r.status))))
      .then((res) => {
        if (!cancelled) setData(res?.data ?? {});
      })
      .catch(() => {
        if (!cancelled) setData({});
      });
    return () => {
      cancelled = true;
    };
  }, []);

  /** 取模块数据；DB 无该模块或后端异常时返回 fallback（constants 默认值） */
  const get = (module, fallback) =>
    data?.[module] === undefined || data?.[module] === null ? fallback : data[module];

  return (
    <HomepageContext.Provider value={{ get, loaded: data !== null }}>
      {children}
    </HomepageContext.Provider>
  );
};

export const useHomepage = () => useContext(HomepageContext);
