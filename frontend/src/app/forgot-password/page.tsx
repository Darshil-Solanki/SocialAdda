"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { ErrorText, buttonClass, inputClass } from "@/components/ui";
import { apiFetch, describeError } from "@/lib/api";
import { Logo } from "@/components/logo";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      await apiFetch("/auth/password-reset/", { method: "POST", body: { email: email.trim() } });
      setSent(true);
    } catch (caught) {
      setError(describeError(caught));
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-6 px-4">
      <Logo variant="badge" />
      <h1 className="text-center text-2xl font-bold">Reset your password</h1>
      {sent ? (
        <p role="status" className="text-center text-sm">
          If an account uses that email, we have sent a link to choose a new password. The link expires after a short time.
        </p>
      ) : (
        <form method="post" onSubmit={submit} className="space-y-4">
          <label className="block text-sm">
            <span className="mb-1 block font-medium">Email</span>
            <input
              type="email"
              autoComplete="email"
              required
              className={inputClass}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          {error && <ErrorText>{error}</ErrorText>}
          <button className={`${buttonClass} w-full`} disabled={pending || !email.trim()}>
            {pending ? "Sending…" : "Send reset link"}
          </button>
        </form>
      )}
      <p className="text-center text-sm">
        <Link href="/login" className="text-sky-600 hover:underline">
          Back to log in
        </Link>
      </p>
    </main>
  );
}
