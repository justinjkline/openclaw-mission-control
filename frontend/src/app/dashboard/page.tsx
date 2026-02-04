"use client";

import { useRouter } from "next/navigation";

import { SignInButton, SignedIn, SignedOut } from "@clerk/nextjs";

import { DashboardSidebar } from "@/components/organisms/DashboardSidebar";
import { DashboardShell } from "@/components/templates/DashboardShell";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  const router = useRouter();

  return (
    <DashboardShell>
      <SignedOut>
        <div className="flex h-full flex-col items-center justify-center gap-4 rounded-2xl surface-panel p-10 text-center">
          <p className="text-sm text-muted">
            Sign in to access your dashboard.
          </p>
          <SignInButton
            mode="modal"
            forceRedirectUrl="/onboarding"
            signUpForceRedirectUrl="/onboarding"
          >
            <Button>Sign in</Button>
          </SignInButton>
        </div>
      </SignedOut>
      <SignedIn>
        <DashboardSidebar />
        <div className="flex h-full flex-col items-center justify-center gap-4 rounded-2xl surface-panel p-10 text-center">
          <p className="text-sm text-muted">
            Your work lives in boards. Jump in to manage tasks.
          </p>
          <Button onClick={() => router.push("/boards")}>
            Go to boards
          </Button>
        </div>
      </SignedIn>
    </DashboardShell>
  );
}
