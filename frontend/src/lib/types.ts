export type UserSummary = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  profile_pic: string | null;
};

// Search results also say whether the viewer already follows that person.
export type UserSearchResult = UserSummary & { is_following: boolean };

export type UserProfile = UserSummary & {
  bio: string | null;
  cover: string | null;
  follower_count: number;
  following_count: number;
  is_following: boolean;
};

export type CurrentUser = UserSummary & {
  email: string;
  bio: string | null;
  cover: string | null;
};

export type Post = {
  id: number;
  author: UserSummary;
  content_text: string;
  content_image: string | null;
  content_thumbnail: string | null;
  like_count: number;
  comment_count: number;
  is_liked: boolean;
  is_saved: boolean;
  date_created: string;
};

export type Comment = {
  id: number;
  author: UserSummary;
  body: string;
  comment_time: string;
  // Replies point at their top-level comment; only one level of replies exists.
  parent_id: number | null;
  reply_count: number;
};

export type Message = {
  id: number;
  sender: UserSummary;
  body: string;
  created_at: string;
};

export type Conversation = {
  id: number;
  other_user: UserSummary | null;
  unread_count: number;
  other_last_read_at: string | null;
};

export type Notification = {
  id: number;
  verb: "like" | "comment" | "follow";
  actor: UserSummary;
  post_id: number | null;
  created_at: string;
  read_at: string | null;
};

// Both pagination styles the API uses (cursor for posts and messages, limit/offset for lists) share this shape:
// `next` is the link to the following page, and `results` holds the items.
export type Paginated<T> = {
  next: string | null;
  previous: string | null;
  results: T[];
};

export type OffsetPage<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type Tokens = { access: string; refresh: string };
