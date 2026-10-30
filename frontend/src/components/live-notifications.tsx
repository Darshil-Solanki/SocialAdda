"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { socketToken } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { WS_URL } from "@/lib/config";

const RECONNECT_DELAY_MS = 3000;

// Keeps one socket open for the signed-in user and refreshes notification queries on each push.
export function LiveNotifications() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!user) return;
    let socket: WebSocket | null = null;
    let reconnect: ReturnType<typeof setTimeout> | null = null;
    let closed = false;

    async function connect() {
      const token = await socketToken();
      if (closed || !token) return;
      // The token goes in the subprotocol list, so it never appears in a URL.
      socket = new WebSocket(`${WS_URL}/ws/notifications/`, ["socialadda", token]);
      // Refresh on every push, and on (re)connect so anything sent while the socket was down is picked up.
      const refresh = () => queryClient.invalidateQueries({ queryKey: ["notifications"] });
      socket.onopen = refresh;
      socket.onmessage = refresh;
      socket.onclose = () => {
        if (!closed) reconnect = setTimeout(connect, RECONNECT_DELAY_MS);
      };
    }

    connect();
    return () => {
      closed = true;
      if (reconnect) clearTimeout(reconnect);
      socket?.close();
    };
  }, [user, queryClient]);

  return null;
}
