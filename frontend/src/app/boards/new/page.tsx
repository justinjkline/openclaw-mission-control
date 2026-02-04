"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { SignInButton, SignedIn, SignedOut, useAuth } from "@clerk/nextjs";

import { DashboardSidebar } from "@/components/organisms/DashboardSidebar";
import { DashboardShell } from "@/components/templates/DashboardShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { getApiBaseUrl } from "@/lib/api-base";

type Board = {
  id: string;
  name: string;
  slug: string;
  gateway_url?: string | null;
  gateway_token?: string | null;
  gateway_main_session_key?: string | null;
  gateway_workspace_root?: string | null;
  identity_template?: string | null;
  soul_template?: string | null;
};

const apiBase = getApiBaseUrl();

const slugify = (value: string) =>
  value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "") || "board";

export default function NewBoardPage() {
  const router = useRouter();
  const { getToken, isSignedIn } = useAuth();
  const [name, setName] = useState("");
  const [gatewayUrl, setGatewayUrl] = useState("");
  const [gatewayToken, setGatewayToken] = useState("");
  const [gatewayMainSessionKey, setGatewayMainSessionKey] = useState("");
  const [gatewayWorkspaceRoot, setGatewayWorkspaceRoot] = useState("");
  const [identityTemplate, setIdentityTemplate] = useState("");
  const [soulTemplate, setSoulTemplate] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!isSignedIn) return;
    const trimmed = name.trim();
    if (!trimmed) return;
    setIsLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const payload: Partial<Board> = {
        name: trimmed,
        slug: slugify(trimmed),
      };
      if (gatewayUrl.trim()) payload.gateway_url = gatewayUrl.trim();
      if (gatewayToken.trim()) payload.gateway_token = gatewayToken.trim();
      if (gatewayMainSessionKey.trim()) {
        payload.gateway_main_session_key = gatewayMainSessionKey.trim();
      }
      if (gatewayWorkspaceRoot.trim()) {
        payload.gateway_workspace_root = gatewayWorkspaceRoot.trim();
      }
      if (identityTemplate.trim()) {
        payload.identity_template = identityTemplate.trim();
      }
      if (soulTemplate.trim()) {
        payload.soul_template = soulTemplate.trim();
      }
      const response = await fetch(`${apiBase}/api/v1/boards`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error("Unable to create board.");
      }
      const created = (await response.json()) as Board;
      router.push(`/boards/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <DashboardShell>
      <SignedOut>
        <div className="flex h-full flex-col items-center justify-center gap-4 rounded-2xl surface-panel p-10 text-center lg:col-span-2">
          <p className="text-sm text-muted">Sign in to create a board.</p>
          <SignInButton
            mode="modal"
            forceRedirectUrl="/boards/new"
            signUpForceRedirectUrl="/boards/new"
          >
            <Button>Sign in</Button>
          </SignInButton>
        </div>
      </SignedOut>
      <SignedIn>
        <DashboardSidebar />
        <div className="flex h-full flex-col justify-center rounded-2xl surface-panel p-8">
          <div className="mb-6 space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-quiet">
              New board
            </p>
            <h1 className="text-2xl font-semibold text-strong">
              Spin up a board.
            </h1>
            <p className="text-sm text-muted">
              Boards are where tasks live and move through your workflow.
            </p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-strong">
                Board name
              </label>
              <Input
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="e.g. Product ops"
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-strong">
                Gateway URL
              </label>
              <Input
                value={gatewayUrl}
                onChange={(event) => setGatewayUrl(event.target.value)}
                placeholder="ws://gateway:18789"
                disabled={isLoading}
              />
              <p className="text-xs text-quiet">
                Required to provision agents for this board.
              </p>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-strong">
                Gateway token
              </label>
              <Input
                value={gatewayToken}
                onChange={(event) => setGatewayToken(event.target.value)}
                placeholder="Optional bearer token"
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-strong">
                Main session key
              </label>
              <Input
                value={gatewayMainSessionKey}
                onChange={(event) => setGatewayMainSessionKey(event.target.value)}
                placeholder="agent:main:main"
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-strong">
                Workspace root
              </label>
              <Input
                value={gatewayWorkspaceRoot}
                onChange={(event) => setGatewayWorkspaceRoot(event.target.value)}
                placeholder="~/.openclaw"
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-strong">
                Identity template (optional)
              </label>
              <Textarea
                value={identityTemplate}
                onChange={(event) => setIdentityTemplate(event.target.value)}
                placeholder="Override IDENTITY.md for agents in this board."
                className="min-h-[140px]"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-strong">
                Soul template (optional)
              </label>
              <Textarea
                value={soulTemplate}
                onChange={(event) => setSoulTemplate(event.target.value)}
                placeholder="Override SOUL.md for agents in this board."
                className="min-h-[160px]"
              />
            </div>
            {error ? (
              <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-3 text-xs text-muted">
                {error}
              </div>
            ) : null}
            <Button
              type="submit"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? "Creating…" : "Create board"}
            </Button>
          </form>
          <Button
            variant="outline"
            className="mt-4"
            onClick={() => router.push("/boards")}
          >
            Back to boards
          </Button>
        </div>
      </SignedIn>
    </DashboardShell>
  );
}
