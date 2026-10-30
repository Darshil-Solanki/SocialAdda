"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";

import { describeError } from "@/lib/api";
import { useCreatePost } from "@/lib/queries";

import { Card, ErrorText, buttonClass, inputClass } from "./ui";

const schema = z.object({
  text: z.string().trim().max(140, "Posts are limited to 140 characters."),
});

type FormValues = z.infer<typeof schema>;

export function PostComposer() {
  const [image, setImage] = useState<File | null>(null);
  // Changing the key remounts the file input, so the chosen file name is cleared after posting.
  const [fileInputKey, setFileInputKey] = useState(0);
  const [imageError, setImageError] = useState<string | null>(null);
  const createPost = useCreatePost();
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { text: "" } });
  const text = useWatch({ control: form.control, name: "text" }) ?? "";

  const onSubmit = form.handleSubmit((values) => {
    if (!values.text && !image) {
      setImageError("Write something or attach an image.");
      return;
    }
    setImageError(null);
    const body = new FormData();
    body.append("content_text", values.text);
    if (image) body.append("content_image", image);
    createPost.mutate(body, {
      onSuccess: () => {
        form.reset();
        setImage(null);
        setFileInputKey((key) => key + 1);
      },
    });
  });

  return (
    <Card className="p-4">
      <form onSubmit={onSubmit} className="space-y-3">
        <label htmlFor="post-text" className="sr-only">
          What is happening?
        </label>
        <textarea
          id="post-text"
          rows={3}
          placeholder="What is happening?"
          className={inputClass}
          {...form.register("text")}
        />
        <div className="flex items-center justify-between gap-3">
          <div className="flex flex-col text-sm">
            <input
              key={fileInputKey}
              type="file"
              accept="image/*"
              aria-label="Attach image"
              onChange={(event) => setImage(event.target.files?.[0] ?? null)}
            />
            <span className={text.length > 140 ? "text-red-600" : "text-zinc-500"}>{text.length}/140</span>
          </div>
          <button className={buttonClass} disabled={createPost.isPending}>
            Post
          </button>
        </div>
        {form.formState.errors.text && <ErrorText>{form.formState.errors.text.message}</ErrorText>}
        {imageError && <ErrorText>{imageError}</ErrorText>}
        {createPost.isError && <ErrorText>{describeError(createPost.error)}</ErrorText>}
      </form>
    </Card>
  );
}
