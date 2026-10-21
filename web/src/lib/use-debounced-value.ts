"use client";

import { useEffect, useState } from "react";

/** Devuelve `value` cuando deja de cambiar por `ms` (el `fiado/quote` en vivo usa 300 ms, 09). */
export function useDebouncedValue<T>(value: T, ms = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return debounced;
}
