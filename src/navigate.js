import { useEffect, useState } from "react";

const listeners = new Set();

export function currentPath() {
  const path = window.location.pathname.replace(/\/$/, "");
  return path || "/";
}

function notify() {
  const path = currentPath();
  listeners.forEach((listener) => listener(path));
}

function scrollToTarget(hash) {
  if (!hash) {
    window.scrollTo(0, 0);
    return;
  }
  const target = document.querySelector(hash);
  if (target) target.scrollIntoView();
}

export function navigate(href) {
  const url = new URL(href, window.location.origin);
  window.history.pushState({}, "", `${url.pathname}${url.search}${url.hash}`);
  notify();
  window.requestAnimationFrame(() => scrollToTarget(url.hash));
}

/** Same as navigate but replaceState (product deep-links / share sync). */
export function replaceUrl(href) {
  const url = new URL(href, window.location.origin);
  window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
  notify();
}

export function usePathname() {
  const [path, setPath] = useState(currentPath);

  useEffect(() => {
    listeners.add(setPath);
    const onPop = () => {
      setPath(currentPath());
      window.requestAnimationFrame(() => scrollToTarget(window.location.hash));
    };
    window.addEventListener("popstate", onPop);
    return () => {
      listeners.delete(setPath);
      window.removeEventListener("popstate", onPop);
    };
  }, []);

  return path;
}

export function onNavClick(event, link, { goToCategory, closeMenu } = {}) {
  event.preventDefault();
  if (link?.category || link?.href?.includes("#collection")) {
    goToCategory?.(link.category || "הכל");
  }
  closeMenu?.();
  navigate(link?.href || "/");
}
