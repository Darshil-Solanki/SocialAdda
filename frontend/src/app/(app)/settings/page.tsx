"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useMemo, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Avatar, Card, ErrorText, buttonClass, inputClass } from "@/components/ui";
import { describeError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { mediaUrl } from "@/lib/media";
import { useUpdateProfile } from "@/lib/queries";

const schema = z.object({
  first_name: z.string().trim().max(150),
  last_name: z.string().trim().max(150),
  bio: z.string().trim().max(160, "Bio is limited to 160 characters."),
});

type FormValues = z.infer<typeof schema>;

export default function SettingsPage() {
  const { user } = useAuth();
  const update = useUpdateProfile();
  // Firefox does not open the picker from a <label> around an image, so these buttons call input.click() directly.
  const photoInput = useRef<HTMLInputElement>(null);
  const coverInput = useRef<HTMLInputElement>(null);
  const [avatar, setAvatar] = useState<File | null>(null);
  const [cover, setCover] = useState<File | null>(null);
  const [removeAvatar, setRemoveAvatar] = useState(false);
  const [removeCover, setRemoveCover] = useState(false);
  const coverPreview = useMemo(() => (cover ? URL.createObjectURL(cover) : null), [cover]);

  useEffect(() => {
    return () => {
      if (coverPreview) URL.revokeObjectURL(coverPreview);
    };
  }, [coverPreview]);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    values: {
      first_name: user?.first_name ?? "",
      last_name: user?.last_name ?? "",
      bio: user?.bio ?? "",
    },
  });

  if (!user) return null;

  const onSubmit = form.handleSubmit((values) => {
    const photoChanged = Boolean(avatar || cover || removeAvatar || removeCover);
    const done = () => {
      setAvatar(null);
      setCover(null);
      setRemoveAvatar(false);
      setRemoveCover(false);
    };
    if (photoChanged) {
      // Files need multipart; the text fields and removal flags are sent alongside them.
      const body = new FormData();
      body.append("first_name", values.first_name);
      body.append("last_name", values.last_name);
      body.append("bio", values.bio);
      if (avatar) body.append("profile_pic", avatar);
      else if (removeAvatar) body.append("remove_profile_pic", "true");
      if (cover) body.append("cover", cover);
      else if (removeCover) body.append("remove_cover", "true");
      update.mutate(body, { onSuccess: done });
    } else {
      update.mutate(values);
    }
  });

  // What the photo looks like after the pending changes: a new file, nothing (removed), or the saved photo.
  const avatarPreview = removeAvatar && !avatar ? { ...user, profile_pic: null } : user;
  const coverShown = removeCover && !cover ? null : coverPreview ?? user.cover;

  return (
    <Card className="space-y-4 p-6">
      <h1 className="text-xl font-bold">Edit profile</h1>
      <div className="flex flex-wrap items-center gap-4">
        <button
          type="button"
          onClick={() => photoInput.current?.click()}
          aria-label="Choose profile photo"
          className="cursor-pointer rounded-full"
        >
          {avatarPreview.profile_pic ? (
            <Avatar user={avatarPreview} size={64} />
          ) : (
            // eslint-disable-next-line @next/next/no-img-element -- static placeholder from /public/defaults
            <img src="/defaults/upload_profile.png" alt="Browse profile file to upload" className="size-16 rounded-full object-cover" />
          )}
        </button>
        <div className="space-y-2 text-sm">
          <label className="block">
            <span className="mb-1 block font-medium">Profile photo</span>
            <input
              ref={photoInput}
              id="settings-photo"
              type="file"
              accept="image/*"
              aria-label="Profile photo"
              onChange={(event) => {
                setAvatar(event.target.files?.[0] ?? null);
                setRemoveAvatar(false);
              }}
            />
          </label>
          {(user.profile_pic || avatar) && (
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={removeAvatar}
                disabled={Boolean(avatar)}
                onChange={(event) => setRemoveAvatar(event.target.checked)}
              />
              Remove profile photo
            </label>
          )}
        </div>
      </div>
      <div className="space-y-2 text-sm">
        <span className="block font-medium">Cover photo</span>
        <button
          type="button"
          onClick={() => coverInput.current?.click()}
          aria-label="Choose cover photo"
          className="block h-24 w-full cursor-pointer overflow-hidden rounded-xl bg-zinc-300 dark:bg-zinc-700"
        >
          {coverShown ? (
            // eslint-disable-next-line @next/next/no-img-element -- local preview or user upload
            <img src={coverShown.startsWith("blob:") ? coverShown : mediaUrl(coverShown)} alt="" className="h-full w-full object-cover" />
          ) : (
            // eslint-disable-next-line @next/next/no-img-element -- static placeholder from /public/defaults
            <img src="/defaults/upload_cover.png" alt="Browse cover file to upload" className="h-full w-full object-cover" />
          )}
        </button>
        <input
          ref={coverInput}
          id="settings-cover"
          type="file"
          accept="image/*"
          aria-label="Cover photo"
          onChange={(event) => {
            setCover(event.target.files?.[0] ?? null);
            setRemoveCover(false);
          }}
        />
        {(user.cover || cover) && (
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={removeCover}
              disabled={Boolean(cover)}
              onChange={(event) => setRemoveCover(event.target.checked)}
            />
            Remove cover photo
          </label>
        )}
      </div>
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1 block font-medium">First name</span>
            <input className={inputClass} {...form.register("first_name")} />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block font-medium">Last name</span>
            <input className={inputClass} {...form.register("last_name")} />
          </label>
        </div>
        <label className="block text-sm">
          <span className="mb-1 block font-medium">Bio</span>
          <textarea rows={3} className={inputClass} {...form.register("bio")} />
        </label>
        {form.formState.errors.bio && <ErrorText>{form.formState.errors.bio.message}</ErrorText>}
        {update.isError && <ErrorText>{describeError(update.error)}</ErrorText>}
        {update.isSuccess && <p className="text-sm text-emerald-600">Saved.</p>}
        <button className={buttonClass} disabled={update.isPending}>
          Save changes
        </button>
      </form>
    </Card>
  );
}
