// Each path segment must be a plain name (usernames, ids, endpoint names). Encoded slashes and dot segments could
// otherwise climb out of /api/v1 to other Django paths, such as /admin/ or the token endpoints.
const SAFE_SEGMENT = /^[A-Za-z0-9_.@+-]+$/;

export function isSafePath(segments: string[]): boolean {
  return segments.every((segment) => SAFE_SEGMENT.test(segment) && segment !== "." && segment !== "..");
}
