/**
 * Keyboard shortcuts for robot control.
 */

import { useEffect, useCallback } from "react";

interface KeyboardConfig {
  onForward: () => void;
  onBackward: () => void;
  onLeft: () => void;
  onRight: () => void;
  onStop: () => void;
  onEStop: () => void;
  enabled: boolean;
}

export function useKeyboardControl({
  onForward,
  onBackward,
  onLeft,
  onRight,
  onStop,
  onEStop,
  enabled,
}: KeyboardConfig) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!enabled) return;

      // Don't intercept when typing in inputs
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      )
        return;

      switch (e.key) {
        case "w":
        case "ArrowUp":
          e.preventDefault();
          onForward();
          break;
        case "s":
        case "ArrowDown":
          e.preventDefault();
          onBackward();
          break;
        case "a":
        case "ArrowLeft":
          e.preventDefault();
          onLeft();
          break;
        case "d":
        case "ArrowRight":
          e.preventDefault();
          onRight();
          break;
        case " ":
          e.preventDefault();
          onStop();
          break;
        case "Escape":
          e.preventDefault();
          onEStop();
          break;
      }
    },
    [enabled, onForward, onBackward, onLeft, onRight, onStop, onEStop]
  );

  const handleKeyUp = useCallback(
    (e: KeyboardEvent) => {
      if (!enabled) return;
      if (["w", "s", "a", "d", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.key)) {
        onStop();
      }
    },
    [enabled, onStop]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [handleKeyDown, handleKeyUp]);
}
