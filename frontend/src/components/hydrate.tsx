"use client";

import { HydrationBoundary, type DehydratedState } from "@tanstack/react-query";
import type { ReactNode } from "react";

// Passes data that the server fetched into the browser's query cache, so the first paint has it.
export function Hydrate({ state, children }: { state: DehydratedState; children: ReactNode }) {
  return <HydrationBoundary state={state}>{children}</HydrationBoundary>;
}
