import { useEffect, useRef, useState } from "react";

const DeferredRender = ({
  children,
  className = "",
  minHeight = "1px",
  rootMargin = "600px 0px",
  idle = false,
  placeholder = null,
}) => {
  const hostRef = useRef(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    if (mounted) return undefined;

    let idleId;
    let timerId;
    const reveal = () => {
      if (idle && "requestIdleCallback" in window) {
        idleId = window.requestIdleCallback(() => setMounted(true), { timeout: 1500 });
      } else if (idle) {
        timerId = window.setTimeout(() => setMounted(true), 350);
      } else {
        setMounted(true);
      }
    };
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        observer.disconnect();
        reveal();
      }
    }, { rootMargin });

    if (hostRef.current) observer.observe(hostRef.current);
    return () => {
      observer.disconnect();
      if (idleId) window.cancelIdleCallback?.(idleId);
      if (timerId) window.clearTimeout(timerId);
    };
  }, [idle, mounted, rootMargin]);

  return (
    <div ref={hostRef} className={className} style={{ minHeight }}>
      {mounted ? children : placeholder}
    </div>
  );
};

export default DeferredRender;
