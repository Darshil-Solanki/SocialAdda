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
  first_name: z.string().trim().max(150),
  last_name: z.string().trim().max(150),
  username: z.string().trim().min(1, "Choose a username.").max(150),
  email: z.email("Enter a valid email address."),
  password: z.string().min(8, "Use at least 8 characters."),
  confirm_password: z.string(),
}).refine((values) => values.password === values.confirm_password, {
  message: "The two passwords do not match.",
  path: ["confirm_password"],
});

type FormValues = z.infer<typeof schema>;

export default function SignupPage() {
  const { register: createAccount } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { first_name: "", last_name: "", username: "", email: "", password: "", confirm_password: "" },
  });

  const onSubmit = form.handleSubmit(async (values) => {
    setError(null);
    setPending(true);
    try {
      // The confirmation is checked here only; the API never receives it.
      const { confirm_password: _confirm, ...account } = values;
      void _confirm;
      await createAccount(account);
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
      <h1 className="text-center text-2xl font-bold">Create your account</h1>
      <form method="post" onSubmit={onSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
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
          <span className="mb-1 block font-medium">Username</span>
          <input autoComplete="username" className={inputClass} {...form.register("username")} />
        </label>
        {form.formState.errors.username && <ErrorText>{form.formState.errors.username.message}</ErrorText>}
        <label className="block text-sm">
          <span className="mb-1 block font-medium">Email</span>
          <input type="email" autoComplete="email" className={inputClass} {...form.register("email")} />
        </label>
        {form.formState.errors.email && <ErrorText>{form.formState.errors.email.message}</ErrorText>}
        <label className="block text-sm">
          <span className="mb-1 block font-medium">Password</span>
          <input type="password" autoComplete="new-password" className={inputClass} {...form.register("password")} />
        </label>
        {form.formState.errors.password && <ErrorText>{form.formState.errors.password.message}</ErrorText>}
        <label className="block text-sm">
          <span className="mb-1 block font-medium">Confirm password</span>
          <input
            type="password"
            autoComplete="new-password"
            className={inputClass}
            {...form.register("confirm_password")}
          />
        </label>
        {form.formState.errors.confirm_password && (
          <ErrorText>{form.formState.errors.confirm_password.message}</ErrorText>
        )}
        {error && <ErrorText>{error}</ErrorText>}
        <button className={`${buttonClass} w-full`} disabled={pending}>
          {pending ? "Creating account…" : "Sign up"}
        </button>
      </form>
      <p className="text-center text-sm">
        Already have an account?{" "}
        <Link href="/login" className="text-sky-600 hover:underline">
          Log in
        </Link>
      </p>
    </main>
  );
}
