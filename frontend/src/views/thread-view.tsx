"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";

import { Card, EmptyState, ErrorText, Spinner, buttonClass, inputClass, formatTime } from "@/components/ui";
import { describeError, socketToken } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { WS_URL } from "@/lib/config";
import { flatten, useConversations, useMarkRead, useMessages, useProfile, useSendMessage } from "@/lib/queries";
import type { Message } from "@/lib/types";

const TYPING_HOLD_MS = 3000;
const TYPING_SEND_INTERVAL_MS = 2000;

type ChatEvent =
  | { event: "typing"; username: string }
  | { event: "read"; username: string; read_at: string }
  | { message: string; username: string };

export function ThreadView({ username }: { username: string }) {
  const { user: me } = useAuth();
  const queryClient = useQueryClient();
  const profile = useProfile(username);
  const messages = useMessages(username);
  const conversations = useConversations();
  const send = useSendMessage(username);
  const markRead = useMarkRead(username);
  const [draft, setDraft] = useState("");
  const [otherIsTyping, setOtherIsTyping] = useState(false);
  const [liveReadAt, setLiveReadAt] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const typingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastTypingSent = useRef(0);
  const otherId = profile.data?.id;

  // Mark the thread read once it has been opened.
  useEffect(() => {
    markRead.mutate();
    // Only on open: markRead is recreated every render and must not re-trigger.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [username]);

  // Live channel: new messages, typing and read receipts all arrive on one socket.
  useEffect(() => {
    if (!otherId) return;
    let socket: WebSocket | null = null;
    let cancelled = false;
    socketToken().then((token) => {
      if (cancelled || !token) return;
      // The token goes in the subprotocol list, so it never appears in a URL.
      socket = new WebSocket(`${WS_URL}/ws/${otherId}/`, ["socialadda", token]);
      socketRef.current = socket;
      socket.onopen = () => socket?.send(JSON.stringify({ type: "read" }));
      socket.onmessage = (event) => {
        let data: ChatEvent;
        try {
          data = JSON.parse(event.data) as ChatEvent;
        } catch {
          return; // a malformed frame must not break the open thread
        }
        if (!("event" in data)) {
          queryClient.invalidateQueries({ queryKey: ["messages", username] });
          // A message from the other person arrived while this thread is open, so it has been seen.
          if (data.username === username) socket?.send(JSON.stringify({ type: "read" }));
          return;
        }
        if (data.username !== username) return; // our own echoes are ignored
        if (data.event === "typing") {
          setOtherIsTyping(true);
          if (typingTimer.current) clearTimeout(typingTimer.current);
          typingTimer.current = setTimeout(() => setOtherIsTyping(false), TYPING_HOLD_MS);
        } else if (data.event === "read") {
          setLiveReadAt(data.read_at);
        }
      };
    });
    return () => {
      cancelled = true;
      if (typingTimer.current) clearTimeout(typingTimer.current);
      socketRef.current = null;
      socket?.close();
    };
  }, [otherId, username, queryClient]);

  function onDraftChange(event: ChangeEvent<HTMLInputElement>) {
    setDraft(event.target.value);
    // Throttle typing pings so the other side gets a signal without a flood of events.
    const now = Date.now();
    if (now - lastTypingSent.current > TYPING_SEND_INTERVAL_MS && socketRef.current?.readyState === WebSocket.OPEN) {
      lastTypingSent.current = now;
      socketRef.current.send(JSON.stringify({ type: "typing" }));
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    const body = draft.trim();
    if (!body) return;
    send.mutate(body, { onSuccess: () => setDraft("") });
  }

  if (profile.isError) return <ErrorText>{describeError(profile.error)}</ErrorText>;
  if (messages.isError) return <ErrorText>{describeError(messages.error)}</ErrorText>;
  if (messages.isPending) return <Spinner label="Loading messages" />;

  // The API returns newest first; show oldest first.
  const items: Message[] = [...flatten(messages.data)].reverse();

  // The other person's last-read time: live receipts win over the value from the conversation list.
  const listed = flatten(conversations.data).find((item) => item.other_user?.username === username);
  const otherReadAt = liveReadAt ?? listed?.other_last_read_at ?? null;
  const isSeen = (message: Message) =>
    message.sender.username === me?.username &&
    otherReadAt !== null &&
    Date.parse(otherReadAt) >= Date.parse(message.created_at);

  return (
    <Card className="flex h-[70vh] flex-col">
      <header className="border-b border-zinc-200 p-4 dark:border-zinc-800">
        <h1 className="font-semibold">{profile.data ? `@${profile.data.username}` : "Conversation"}</h1>
        {otherIsTyping && <p className="text-xs text-zinc-500">typing…</p>}
      </header>

      <div className="flex-1 space-y-2 overflow-y-auto p-4">
        {messages.hasNextPage && (
          <button className="w-full text-sm text-sky-600 hover:underline" onClick={() => messages.fetchNextPage()}>
            Load earlier messages
          </button>
        )}
        {items.length === 0 && <EmptyState>Say hello 👋</EmptyState>}
        {items.map((message) => {
          const mine = message.sender.username === me?.username;
          return (
            <div key={message.id} className={`flex flex-col ${mine ? "items-end" : "items-start"}`}>
              <div
                className={`max-w-[75%] rounded-2xl px-3 py-2 text-sm ${
                  mine ? "bg-sky-600 text-white" : "bg-zinc-200 dark:bg-zinc-800"
                }`}
              >
                <p className="whitespace-pre-wrap break-words">{message.body}</p>
                <time className="mt-1 block text-[10px] opacity-70" dateTime={message.created_at}>
                  {formatTime(message.created_at)}
                </time>
              </div>
              {isSeen(message) && <span className="mt-1 text-xs text-zinc-500">Seen</span>}
            </div>
          );
        })}
      </div>

      <form onSubmit={submit} className="flex gap-2 border-t border-zinc-200 p-3 dark:border-zinc-800">
        <label htmlFor="message-input" className="sr-only">
          Message
        </label>
        <input
          id="message-input"
          className={inputClass}
          maxLength={1000}
          placeholder="Write a message"
          value={draft}
          onChange={onDraftChange}
        />
        <button className={buttonClass} disabled={send.isPending || !draft.trim()}>
          Send
        </button>
      </form>
      {send.isError && <div className="px-3 pb-3"><ErrorText>{describeError(send.error)}</ErrorText></div>}
    </Card>
  );
}
