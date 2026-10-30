// Media paths are served by Django under /media/ and proxied through Next.js.
export function mediaUrl(path: string | null | undefined): string {
  if (!path) return "";
  if (/^https?:\/\//.test(path)) {
    // Django builds absolute URLs from the host it sees (an internal name inside Docker, which a browser cannot
    // reach). Local uploads are therefore served from this origin; files on an external bucket keep their URL.
    const url = new URL(path);
    return url.pathname.startsWith("/media/") ? `${url.pathname}${url.search}` : path;
  }
  return path.startsWith("/") ? path : `/media/${path}`;
}
