"use client";

import Image from "next/image";
import { SignOutButton, useUser } from "@clerk/nextjs";
import { LogOut } from "lucide-react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";

export function UserMenu({ className }: { className?: string }) {
  const { user } = useUser();
  if (!user) return null;

  const avatarUrl = user.imageUrl ?? null;
  const avatarLabelSource = user.firstName ?? user.username ?? user.id ?? "U";
  const avatarLabel = avatarLabelSource.slice(0, 1).toUpperCase();
  const displayName =
    user.fullName ?? user.firstName ?? user.username ?? "Account";
  const displayEmail = user.primaryEmailAddress?.emailAddress ?? "";

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={cn(
            "flex h-12 items-center gap-2 rounded-lg px-2.5 text-gray-900 transition hover:bg-gray-100",
            className,
          )}
          aria-label="Open user menu"
        >
          <span className="flex h-10 w-10 items-center justify-center overflow-hidden rounded-full bg-gray-100 text-sm font-semibold text-gray-900">
            {avatarUrl ? (
              <Image
                src={avatarUrl}
                alt="User avatar"
                width={40}
                height={40}
                className="h-10 w-10 object-cover"
              />
            ) : (
              avatarLabel
            )}
          </span>
        </button>
      </PopoverTrigger>
      <PopoverContent
        align="end"
        sideOffset={8}
        className="w-64 rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface)] p-0 shadow-lg"
      >
        <div className="border-b border-[color:var(--border)] px-4 py-3">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center overflow-hidden rounded-full bg-[color:var(--surface-muted)] text-sm font-semibold text-strong">
              {avatarUrl ? (
                <Image
                  src={avatarUrl}
                  alt="User avatar"
                  width={40}
                  height={40}
                  className="h-10 w-10 object-cover"
                />
              ) : (
                avatarLabel
              )}
            </span>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-strong">
                {displayName}
              </div>
              {displayEmail ? (
                <div className="truncate text-xs text-muted">{displayEmail}</div>
              ) : null}
            </div>
          </div>
        </div>
        <div className="p-2">
          <SignOutButton>
            <button
              type="button"
              className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-strong transition hover:bg-[color:var(--surface-strong)]"
            >
              <LogOut className="h-4 w-4 text-[color:var(--text-quiet)]" />
              Sign out
            </button>
          </SignOutButton>
        </div>
      </PopoverContent>
    </Popover>
  );
}
