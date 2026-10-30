"use client";

import {
  InfiniteData,
  keepPreviousData,
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { apiFetch, toApiPath } from "./api";
import { postKeys } from "./keys";
import type {
  Comment,
  Conversation,
  CurrentUser,
  Message,
  Notification,
  OffsetPage,
  Paginated,
  Post,
  UserProfile,
  UserSearchResult,
  UserSummary,
} from "./types";

type CursorPage<T> = Paginated<T>;

// Infinite list of a cursor-paginated endpoint. `path` is the first page, relative to /api/v1.
export function useCursorList<T>(queryKey: readonly unknown[], path: string, enabled = true) {
  return useInfiniteQuery({
    queryKey,
    queryFn: ({ pageParam }) => apiFetch<CursorPage<T>>(pageParam),
    initialPageParam: path,
    getNextPageParam: (last) => (last.next ? toApiPath(last.next) : undefined),
    enabled,
  });
}

export function flatten<T>(data: InfiniteData<CursorPage<T>> | undefined): T[] {
  return data?.pages.flatMap((page) => page.results) ?? [];
}


// Applies a change to a post wherever it is cached: in a list, or as a single post (optimistic updates).
function updatePostInLists(
  queryClient: ReturnType<typeof useQueryClient>,
  postId: number,
  change: (post: Post) => Post,
) {
  queryClient.setQueriesData<unknown>({ queryKey: postKeys.all }, (data: unknown) => {
    if (!data || typeof data !== "object") return data;
    if ("pages" in data) {
      const infinite = data as InfiniteData<CursorPage<Post>>;
      return {
        ...infinite,
        pages: infinite.pages.map((page) => ({
          ...page,
          results: page.results.map((post) => (post.id === postId ? change(post) : post)),
        })),
      };
    }
    const single = data as Post;
    return single.id === postId ? change(single) : data;
  });
}

export function usePost(id: number) {
  return useQuery({
    queryKey: postKeys.detail(id),
    queryFn: () => apiFetch<Post>(`/posts/${id}/`),
  });
}

export function usePostList(source: "feed" | "following" | "saved" | { author: string }) {
  const key =
    source === "feed"
      ? postKeys.feed()
      : source === "following"
        ? postKeys.following()
        : source === "saved"
          ? postKeys.saved()
          : postKeys.author(source.author);
  const path =
    source === "following"
      ? "/feed/following/"
      : source === "saved"
        ? "/saved/"
        : source === "feed"
          ? "/posts/"
          : `/posts/?author=${encodeURIComponent(source.author)}`;
  return useCursorList<Post>(key, path);
}

export function useCreatePost() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: FormData | { content_text: string }) =>
      apiFetch<Post>("/posts/", { method: "POST", body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: postKeys.all }),
  });
}

export type PostEdit = FormData | { content_text: string; remove_image?: boolean };

export function useUpdatePost() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: PostEdit }) =>
      apiFetch<Post>(`/posts/${id}/`, { method: "PATCH", body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: postKeys.all }),
  });
}

export function useDeletePost() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiFetch<void>(`/posts/${id}/`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: postKeys.all }),
  });
}

export function useToggleLike() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (post: Post) =>
      apiFetch<void>(`/posts/${post.id}/like/`, { method: post.is_liked ? "DELETE" : "POST" }),
    onMutate: async (post) => {
      await queryClient.cancelQueries({ queryKey: postKeys.all });
      updatePostInLists(queryClient, post.id, (current) => ({
        ...current,
        is_liked: !current.is_liked,
        like_count: current.like_count + (current.is_liked ? -1 : 1),
      }));
    },
    onError: (_error, post) => updatePostInLists(queryClient, post.id, () => post),
    onSettled: () => queryClient.invalidateQueries({ queryKey: postKeys.all }),
  });
}

export function useToggleBookmark() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (post: Post) =>
      apiFetch<void>(`/posts/${post.id}/bookmark/`, { method: post.is_saved ? "DELETE" : "POST" }),
    onMutate: async (post) => {
      await queryClient.cancelQueries({ queryKey: postKeys.all });
      updatePostInLists(queryClient, post.id, (current) => ({ ...current, is_saved: !current.is_saved }));
    },
    onError: (_error, post) => updatePostInLists(queryClient, post.id, () => post),
    onSettled: () => queryClient.invalidateQueries({ queryKey: postKeys.all }),
  });
}

// Top-level comments of a post (the API lists replies separately, by parent).
export function useComments(postId: number, enabled: boolean) {
  return useCursorList<Comment>(["comments", postId], `/posts/${postId}/comments/`, enabled);
}

export function useReplies(postId: number, parentId: number, enabled: boolean) {
  return useCursorList<Comment>(
    ["comments", postId, "replies", parentId],
    `/posts/${postId}/comments/?parent=${parentId}`,
    enabled,
  );
}

export function useAddComment(postId: number, parentId?: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: string) =>
      apiFetch<Comment>(`/posts/${postId}/comments/`, {
        method: "POST",
        body: parentId ? { body, parent: parentId } : { body },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["comments", postId] });
      queryClient.invalidateQueries({ queryKey: postKeys.all });
    },
  });
}

export function useMe(enabled: boolean) {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => apiFetch<CurrentUser>("/me/"),
    enabled,
    retry: false,
  });
}

type ProfileEdit = Partial<Pick<CurrentUser, "first_name" | "last_name" | "bio">> & {
  remove_profile_pic?: boolean;
  remove_cover?: boolean;
};

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: FormData | ProfileEdit) => apiFetch<CurrentUser>("/me/", { method: "PATCH", body }),
    onSuccess: (user) => {
      queryClient.setQueryData(["me"], user);
      // Profile pages, post authors, suggestions and search results all show the same photos and names.
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["users"] });
      queryClient.invalidateQueries({ queryKey: postKeys.all });
    },
  });
}

export function useProfile(username: string) {
  return useQuery({
    queryKey: ["profile", username],
    queryFn: () => apiFetch<UserProfile>(`/users/${encodeURIComponent(username)}/`),
    placeholderData: keepPreviousData,
  });
}

export function useFollow(username: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (follow: boolean) =>
      apiFetch<void>(`/users/${encodeURIComponent(username)}/follow/`, {
        method: follow ? "POST" : "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile", username] });
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["users", "search"] });
      queryClient.invalidateQueries({ queryKey: postKeys.following() });
    },
  });
}

export function useSuggestions() {
  return useQuery({
    queryKey: ["suggestions"],
    queryFn: () => apiFetch<OffsetPage<UserSummary>>("/users/suggestions/"),
  });
}

export function useUserSearch(query: string) {
  return useQuery({
    queryKey: ["users", "search", query],
    queryFn: () => apiFetch<OffsetPage<UserSearchResult>>(`/users/?q=${encodeURIComponent(query)}`),
    enabled: query.trim().length > 0,
    placeholderData: keepPreviousData,
  });
}

export function useConversations() {
  return useCursorList<Conversation>(["conversations"], "/conversations/");
}

export function useMessages(username: string) {
  return useCursorList<Message>(["messages", username], `/conversations/${encodeURIComponent(username)}/messages/`);
}

export function useSendMessage(username: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: string) =>
      apiFetch<Message>(`/conversations/${encodeURIComponent(username)}/messages/`, {
        method: "POST",
        body: { body },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["messages", username] });
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

export function useMarkRead(username: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch<void>(`/conversations/${encodeURIComponent(username)}/read/`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["conversations"] }),
  });
}

export function useNotifications() {
  return useCursorList<Notification>(["notifications"], "/notifications/");
}

export function useUnreadCount(enabled: boolean) {
  return useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: () => apiFetch<{ count: number }>("/notifications/unread-count/"),
    enabled,
    // The live socket refreshes this; polling is a fallback when the socket is down.
    refetchInterval: 60_000,
  });
}

export function useMarkNotificationsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch<void>("/notifications/read/", { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}
