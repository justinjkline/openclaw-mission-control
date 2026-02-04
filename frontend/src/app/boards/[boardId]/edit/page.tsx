"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { SignInButton, SignedIn, SignedOut, useAuth } from "@clerk/nextjs";

import { DashboardSidebar } from "@/components/organisms/DashboardSidebar";
import { DashboardShell } from "@/components/templates/DashboardShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { getApiBaseUrl } from "@/lib/api-base";

const apiBase = getApiBaseUrl();

type Board = {
  id: string;
  name: string;
  slug: string;
  gateway_url?: string | null;
  gateway_main_session_key?: string | null;
  gateway_workspace_root?: string | null;
  identity_template?: string | null;
  soul_template?: string | null;
};

const slugify = (value: string) =>
  value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "") || "board";

export default function EditBoardPage() {
  const { getToken, isSignedIn } = useAuth();
  const router = useRouter();
  const params = useParams();
  const boardIdParam = params?.boardId;
  const boardId = Array.isArray(boardIdParam) ? boardIdParam[0] : boardIdParam;

  const [board, setBoard] = useState<Board | null>(null);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [gatewayUrl, setGatewayUrl] = useState("");
  const [gatewayToken, setGatewayToken] = useState("");
  const [gatewayMainSessionKey, setGatewayMainSessionKey] = useState("");
  const [gatewayWorkspaceRoot, setGatewayWorkspaceRoot] = useState("");
  const [identityTemplate, setIdentityTemplate] = useState("");
  const [soulTemplate, setSoulTemplate] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBoard = async () => {
    if (!isSignedIn || !boardId) return;
    setIsLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await fetch(`${apiBase}/api/v1/boards/${boardId}`, {
        headers: { Authorization: token ? `Bearer ${token}` : "" },
      });
      if (!response.ok) {
        throw new Error("Unable to load board.");
      }
      const data = (await response.json()) as Board;
      setBoard(data);
      setName(data.name);
      setSlug(data.slug);
      setGatewayUrl(data.gateway_url ?? "");
      setGatewayMainSessionKey(data.gateway_main_session_key ?? "");
      setGatewayWorkspaceRoot(data.gateway_workspace_root ?? "");
      setIdentityTemplate(data.identity_template ?? "");
      setSoulTemplate(data.soul_template ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadBoard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSignedIn, boardId]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!isSignedIn || !boardId) return;
    const trimmed = name.trim();
    if (!trimmed) {
      setError("Board name is required.");
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const payload: Partial<Board> & { gateway_token?: string | null } = {
        name: trimmed,
        slug: slug.trim() || slugify(trimmed),
        gateway_url: gatewayUrl.trim() || null,
        gateway_main_session_key: gatewayMainSessionKey.trim() || null,
        gateway_workspace_root: gatewayWorkspaceRoot.trim() || null,
        identity_template: identityTemplate.trim() || null,
        soul_template: soulTemplate.trim() || null,
      };
      if (gatewayToken.trim()) {
        payload.gateway_token = gatewayToken.trim();
      }
      const response = await fetch(`${apiBase}/api/v1/boards/${boardId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error("Unable to update board.");
      }
      router.push(`/boards/${boardId}`);
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
          <p className="text-sm text-muted">Sign in to edit boards.</p>
          <SignInButton
            mode="modal"
            forceRedirectUrl={`/boards/${boardId}/edit`}
            signUpForceRedirectUrl={`/boards/${boardId}/edit`}
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
              Edit board
            </p>
            <h1 className="text-2xl font-semibold text-strong">
              {board?.name ?? "Board"}
            </h1>
            <p className="text-sm text-muted">
              Update the board identity and gateway connection.
            </p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-strong">Board name</label>
              <Input
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="e.g. Product ops"
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-strong">Slug</label>
              <Input
                value={slug}
                onChange={(event) => setSlug(event.target.value)}
                placeholder="product-ops"
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
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-strong">
                Gateway token
              </label>
              <Input
                value={gatewayToken}
                onChange={(event) => setGatewayToken(event.target.value)}
                placeholder="Leave blank to keep current token"
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
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "Saving…" : "Save changes"}
            </Button>
          </form>
          <Button
            variant="outline"
            className="mt-4"
            onClick={() => router.push(`/boards/${boardId}`)}
          >
            Back to board
          </Button>
        </div>
      </SignedIn>
    </DashboardShell>
  );
}
