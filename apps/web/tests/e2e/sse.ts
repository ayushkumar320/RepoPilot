/** SSE bodies for the streaming ask endpoint, built from an answer payload.
 *
 *  The app asks `/ask/stream` first and only falls back to the buffered
 *  `/ask`, so a route mock that serves JSON to both leaves the streaming path
 *  untested. Splitting the answer into tokens here exercises the frame parser
 *  the way the real endpoint does.
 */
export function askStreamBody(answerJson: string): string {
  const { answer } = JSON.parse(answerJson) as { answer: string };
  const tokens = answer.match(/\S+\s*/g) ?? [answer];
  const frames = tokens.map(
    (text) => `event: answer_token\ndata: ${JSON.stringify({ v: 1, text })}\n\n`,
  );
  frames.push(
    `event: answer_done\ndata: ${JSON.stringify({ v: 1, answer: JSON.parse(answerJson) })}\n\n`,
  );
  return frames.join("");
}

export const sseHeaders = {
  "Cache-Control": "no-cache",
  Connection: "keep-alive",
};
