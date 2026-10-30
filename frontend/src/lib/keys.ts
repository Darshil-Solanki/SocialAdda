// Query keys shared by client components and server pages. Kept out of "use client" modules on purpose.
export const postKeys = {
  all: ["posts"] as const,
  feed: () => ["posts", "all"] as const,
  following: () => ["posts", "following"] as const,
  saved: () => ["posts", "saved"] as const,
  author: (username: string) => ["posts", "author", username] as const,
  detail: (id: number) => ["posts", "detail", id] as const,
};
