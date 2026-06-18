const streamUrl = process.env.SSE_IDLE_URL ?? "http://127.0.0.1:8000/__dev/sse-idle";
const requiredDurationMs = Number(process.env.SSE_IDLE_DURATION_MS ?? "30000");
const maxGapMs = Number(process.env.SSE_MAX_GAP_MS ?? "10000");

async function main() {
  const controller = new AbortController();
  const startedAt = Date.now();
  let lastMessageAt = startedAt;

  const timeout = setTimeout(() => controller.abort(), requiredDurationMs + 1_000);
  try {
    const response = await fetch(streamUrl, {
      headers: { Accept: "text/event-stream" },
      signal: controller.signal,
    });
    if (!response.ok || !response.body) {
      throw new Error(`Unable to open SSE stream: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (Date.now() - startedAt < requiredDurationMs) {
      const result = await Promise.race([
        reader.read(),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error("Heartbeat gap exceeded.")), maxGapMs),
        ),
      ]);
      if (!result || typeof result !== "object" || !("done" in result)) {
        continue;
      }
      if (result.done) {
        throw new Error("SSE stream ended before idle duration completed.");
      }
      buffer += decoder.decode(result.value, { stream: true });
      if (buffer.includes("\n\n")) {
        lastMessageAt = Date.now();
        buffer = "";
      }
    }

    console.log(
      `SSE stream stayed alive for ${requiredDurationMs} ms; last frame gap was ${
        Date.now() - lastMessageAt
      } ms.`,
    );
  } finally {
    clearTimeout(timeout);
    controller.abort();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
