"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ErrorText, buttonClass, inputClass } from "@/components/ui";
import { describeError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Logo } from "@/components/logo";

const schema = z.object({
  username: z.string().trim().min(1, "Enter your username."),
  password: z.string().min(1, "Enter your password."),
});

type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { username: "", password: "" } });

  const onSubmit = form.handleSubmit(async (values) => {
    setError(null);
    setPending(true);
    try {
      await login(values.username, values.password);
      router.replace("/");
    } catch (caught) {
      setError(describeError(caught));
    } finally {
      setPending(false);
    }
  });

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-6 px-4">
      <Logo variant="badge" />
      <h1 className="text-center text-2xl font-bold">Log in to SocialAdda</h1>
      <form method="post" onSubmit={onSubmit} className="space-y-4">
        <label className="block text-sm">
          <span className="mb-1 block font-medium">Username</span>
          <input autoComplete="username" className={inputClass} {...form.register("username")} />
        </label>
        {form.formState.errors.username && <ErrorText>{form.formState.errors.username.message}</ErrorText>}
        <label className="block text-sm">
          <span className="mb-1 block font-medium">Password</span>
          <input type="password" autoComplete="current-password" className={inputClass} {...form.register("password")} />
        </label>
        {form.formState.errors.password && <ErrorText>{form.formState.errors.password.message}</ErrorText>}
        {error && <ErrorText>{error}</ErrorText>}
        <button className={`${buttonClass} w-full`} disabled={pending}>
          {pending ? "Logging in…" : "Log in"}
        </button>
      </form>
      <p className="text-center text-sm">
        <Link href="/forgot-password" className="text-sky-600 hover:underline">
          Forgot your password?
        </Link>
      </p>
      <p className="text-center text-sm">
        New here?{" "}
        <Link href="/signup" className="text-sky-600 hover:underline">
          Create an account
        </Link>
      </p>
    </main>
  );
}
