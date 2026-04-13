import { useEffect, useRef, useState } from "react";

/**
 * Animate a number from 0 to `end` over `duration` ms.
 * Returns the current animated value as a number.
 */
export function useCountUp(end: number, duration = 1200): number {
  const [value, setValue] = useState(0);
  const startTime = useRef<number | null>(null);
  const rafId = useRef<number>(0);

  useEffect(() => {
    startTime.current = null;

    const step = (timestamp: number) => {
      if (startTime.current === null) startTime.current = timestamp;
      const progress = Math.min((timestamp - startTime.current) / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(eased * end);

      if (progress < 1) {
        rafId.current = requestAnimationFrame(step);
      }
    };

    rafId.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(rafId.current);
  }, [end, duration]);

  return value;
}
