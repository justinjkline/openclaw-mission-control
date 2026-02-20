"use client";

import { cn } from "@/lib/utils";

interface MarkdownProps {
  children?: string;
  content?: string;
  className?: string;
  variant?: "default" | "prose";
}

/**
 * Simple markdown renderer for basic formatting.
 * Renders markdown text with basic styling.
 */
export function Markdown({ children, content, className, variant = "default" }: MarkdownProps) {
  const text = content ?? children ?? "";

  return (
    <div
      className={cn(
        variant === "prose"
          ? "prose prose-slate max-w-none"
          : "prose prose-sm dark:prose-invert max-w-none",
        "prose-headings:font-semibold prose-headings:tracking-tight",
        "prose-p:leading-relaxed",
        "prose-code:rounded prose-code:bg-muted prose-code:px-1 prose-code:py-0.5",
        "prose-pre:bg-muted prose-pre:p-4 prose-pre:rounded-lg",
        className
      )}
      dangerouslySetInnerHTML={{
        __html: renderMarkdown(text),
      }}
    />
  );
}

/**
 * Basic markdown to HTML converter.
 * Handles common patterns: headers, bold, italic, code, links, lists.
 */
function renderMarkdown(text: string): string {
  if (!text) return "";

  let html = text
    // Escape HTML
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    // Headers
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    // Bold
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    // Italic
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    // Inline code
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    // Links
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    // Unordered lists
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    // Line breaks
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br>");

  // Wrap list items
  html = html.replace(/(<li>.*<\/li>)+/g, "<ul>$&</ul>");

  // Wrap in paragraph
  if (!html.startsWith("<h") && !html.startsWith("<ul")) {
    html = `<p>${html}</p>`;
  }

  return html;
}
