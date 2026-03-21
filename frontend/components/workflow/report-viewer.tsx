import ReactMarkdown from "react-markdown";

type ReportViewerProps = {
  markdown: string;
};

/**
 * Render workflow markdown output with basic GitHub-flavored formatting.
 */
export function ReportViewer({ markdown }: ReportViewerProps) {
  return (
    <article className="space-y-3 text-sm leading-relaxed">
      <ReactMarkdown>{markdown}</ReactMarkdown>
    </article>
  );
}
