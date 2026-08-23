import { useEffect, useState } from "react";

// Animates text character by character to simulate streaming output.
export function useTypewriter(text: string, speed = 12): string {
  const [displayed, setDisplayed] = useState("");

  useEffect(() => {
    setDisplayed("");
    if (!text) return;

    let index = 0;

    const id = setInterval(() => {
      index++;
      setDisplayed(text.slice(0, index));
      if (index >= text.length) clearInterval(id);
    }, speed);

    return () => clearInterval(id);
  }, [text]);

  return displayed;
}
