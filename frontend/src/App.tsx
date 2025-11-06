import React from "react";
import { ChatWidget } from "./components/ChatWidget";

function isInIframe() {
  try { 
    return window.self !== window.top; 
  } catch { 
    return true; 
  }
}

const params = new URLSearchParams(window.location.search);
const embedParam = params.get("embed") === "1";
const openParam = params.get("open") === "1";
const isEmbedded = embedParam || isInIframe();
const defaultOpen = openParam || isEmbedded; // auto-open when embedded

export default function App() {
  if (isEmbedded) {
    // For embedded mode, return the widget directly without any wrapper
    return <ChatWidget embedded={true} defaultOpen={defaultOpen} />;
  }

  // Normal site/app shell
  return (
    <>
      {/* your normal site UI here */}
      <ChatWidget />
    </>
  );
}
