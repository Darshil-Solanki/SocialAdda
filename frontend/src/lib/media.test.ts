import { describe, expect, it } from "vitest";

import { mediaUrl } from "./media";

describe("mediaUrl", () => {
  it("returns an empty string for a missing file", () => {
    expect(mediaUrl(null)).toBe("");
    expect(mediaUrl("")).toBe("");
  });

  it("serves a relative upload under /media/", () => {
    expect(mediaUrl("profile_pic/a.png")).toBe("/media/profile_pic/a.png");
  });

  it("uses the same origin for an absolute backend upload URL", () => {
    // Django may return http://api:8000/media/...; the browser must use this origin instead.
    expect(mediaUrl("http://api:8000/media/posts/thumbs/x.webp")).toBe("/media/posts/thumbs/x.webp");
  });

  it("keeps an absolute URL on an external bucket or CDN", () => {
    const url = "https://cdn.example.test/posts/a.png";
    expect(mediaUrl(url)).toBe(url);
  });
});
