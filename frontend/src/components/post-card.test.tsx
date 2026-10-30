import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Providers } from "./providers";
import { PostCard } from "./post-card";
import type { Post } from "@/lib/types";

const post: Post = {
  id: 5,
  author: { id: 2, username: "bob", first_name: "Bob", last_name: "B", profile_pic: "profile_pic/no_pic.png" },
  content_text: "Hello world",
  content_image: null,
  content_thumbnail: null,
  like_count: 3,
  comment_count: 1,
  is_liked: false,
  is_saved: false,
  date_created: "2026-10-12T07:00:00Z",
};

describe("PostCard", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("renders the post text and counts", () => {
    render(<Providers><PostCard post={post} /></Providers>);
    expect(screen.getByText("Hello world")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Like" }).textContent).toContain("3");
  });

  it("sends a like request when the like button is pressed", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<Providers><PostCard post={post} /></Providers>);
    fireEvent.click(screen.getByRole("button", { name: "Like" }));

    // The provider also asks for the current user; find the like request by its URL.
    await waitFor(() =>
      expect(fetchMock.mock.calls.some(([url]) => url === "/api/v1/posts/5/like/")).toBe(true),
    );
    const [, init] = fetchMock.mock.calls.find(([url]) => url === "/api/v1/posts/5/like/")!;
    expect(init.method).toBe("POST");
  });
});
