"use client";

/**
 * Source with real file line numbers beside it.
 *
 * The numbers are the point, not decoration. Every claim this product makes
 * cites a `file:line`, and code shown without them leaves the reader counting
 * rows to check that the citation is honest — which is the one thing the
 * product exists to make easy.
 */
export function SourceView({ content, startLine }: { content: string; startLine: number }) {
  // A chunk ends with a newline more often than not, and rendering that as a
  // final empty numbered row makes the span look one line longer than it is.
  const lines = content.replace(/\n$/, "").split("\n");

  return (
    <pre className="source-view">
      <code>
        {lines.map((line, index) => (
          <span className="source-line" key={`${startLine + index}-${index}`}>
            <span className="source-line-number" aria-hidden="true">
              {startLine + index}
            </span>
            {/* A blank line still needs height, or the numbers stop lining up
                with the code beside them. */}
            <span className="source-line-content">{line || " "}</span>
          </span>
        ))}
      </code>
    </pre>
  );
}
