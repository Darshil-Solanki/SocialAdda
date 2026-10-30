"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState, type FormEvent } from "react";

import { ErrorText, buttonClass, inputClass, Spinner } from "@/components/ui";
import { apiFetch, describeError } from "@/lib/api";
import { Logo } from "@/components/logo";

function ResetPasswordForm() {
  const params = useSearchParams();
  const uid = params.get("uid") ?? "";
  const token = params.get("token") ?? "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [pending, setPending] = useState(false);

  if (!uid || !token) {
    return <ErrorText>This reset link is incomplete. Request a new one from the reset page.</ErrorText>;
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError("The two passwords do not match.");
      return;
    }
    setPending(true);
    try {
      await apiFetch("/auth/password-reset/confirm/", {
        method: "POST",
        body: { uid, token, new_password: password },
      });
      setDone(true);
    } catch (caught) {
      setError(describeError(caught));
    } finally {
      setPending(false);
    }
  }

  if (done) {
    return (
      <p role="status" className="text-center text-sm">
        Your password has been changed.{" "}
        <Link href="/login" className="text-sky-600 hover:underline">
          Log in with your new password
        </Link>
        .
      </p>
    );
  }

  return (
    <form method="post" onSubmit={submit} className="space-y-4">
      <label className="block text-sm">
        <span className="mb-1 block font-medium">New password</span>
        <input
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          className={inputClass}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
      </label>
      <label className="block text-sm">
        <span className="mb-1 block font-medium">Confirm new password</span>
        <input
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          className={inputClass}
          value={confirm}
          onChange={(event) => setConfirm(event.target.value)}
        />
      </label>
      {error && <ErrorText>{error}</ErrorText>}
      <button className={`${buttonClass} w-full`} disabled={pending || password.length < 8 || confirm.length < 8}>
        {pending ? "Saving…" : "Set new password"}
      </button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-6 px-4">
      <Logo variant="badge" />
      <h1 className="text-center text-2xl font-bold">Choose a new password</h1>
      {/* useSearchParams needs a Suspense boundary for static prerendering. */}
      <Suspense fallback={<Spinner />}>
        <ResetPasswordForm />
      </Suspense>
    </main>
  );
}
