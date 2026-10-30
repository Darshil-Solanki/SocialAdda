import { describe, expect, it } from "vitest";

import { isSafePath } from "./paths";

describe("isSafePath", () => {
  it("accepts ordinary API paths, including usernames with dots and plus signs", () => {
    expect(isSafePath(["posts", "12", "comments"])).toBe(true);
    expect(isSafePath(["users", "jane.doe+1"])).toBe(true);
  });

  it("rejects dot segments that would climb out of /api/v1", () => {
    expect(isSafePath(["..", "..", "admin", "login"])).toBe(false);
    expect(isSafePath([".."])).toBe(false);
  });

  it("rejects encoded slashes that arrive as one segment", () => {
    expect(isSafePath(["../../admin/login"])).toBe(false);
    expect(isSafePath(["auth/token"])).toBe(false);
  });
});
