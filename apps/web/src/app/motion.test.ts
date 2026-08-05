import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";

// Comments would otherwise be captured as part of the selector they precede.
const css = readFileSync(path.join(import.meta.dirname, "globals.css"), "utf8").replace(
  /\/\*[\s\S]*?\*\//g,
  "",
);

const REDUCED_MOTION_AT = "@media (prefers-reduced-motion: reduce)";

function splitSelectors(selectorList: string): string[] {
  return selectorList
    .split(",")
    .map((s) => s.trim())
    .filter((s) => s !== "" && !s.startsWith("@") && !/^(from|to|\d+%)$/.test(s));
}

/**
 * The reduced-motion block's own text, and the rest of the stylesheet with
 * that block cut out. Everything outside it has to be checked — including the
 * rules that come after it, which a naive "slice up to the block" would miss.
 */
function splitOnReducedMotion(source: string): { block: string; rest: string } {
  const start = source.indexOf(REDUCED_MOTION_AT);
  assert.notEqual(start, -1, "reduced-motion block is missing entirely");
  let depth = 0;
  let end = -1;
  for (let i = source.indexOf("{", start); i < source.length; i++) {
    if (source[i] === "{") depth++;
    else if (source[i] === "}" && --depth === 0) {
      end = i + 1;
      break;
    }
  }
  assert.notEqual(end, -1, "reduced-motion block is unterminated");
  return { block: source.slice(start, end), rest: source.slice(0, start) + source.slice(end) };
}

function selectorsDeclaring(source: string, value: RegExp): Set<string> {
  const found = new Set<string>();
  for (const [, selectorList, body] of source.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    if (!value.test(body)) continue;
    for (const selector of splitSelectors(selectorList)) found.add(selector);
  }
  return found;
}

test("every animation is neutralised under prefers-reduced-motion", () => {
  const { block, rest } = splitOnReducedMotion(css);
  const animated = selectorsDeclaring(rest, /animation:\s*[\w-]/);
  const overridden = selectorsDeclaring(block, /animation:\s*(fade-in|none)/);

  assert.ok(animated.size > 0, "expected to find animations to check");

  const unhandled = [...animated].filter((selector) => !overridden.has(selector));
  assert.deepEqual(
    unhandled,
    [],
    `these animate but are not reduced to a crossfade: ${unhandled.join(", ")}`,
  );
});

test("spring durations match the sampled settle times", () => {
  // The linear() ramps encode a whole spring; playing one over the wrong
  // duration silently changes the curve it was generated for.
  for (const [token, expected] of [
    ["--spring-duration", "580ms"],
    ["--spring-bounce-duration", "540ms"],
  ]) {
    const found = new RegExp(`${token}:\\s*([^;]+);`).exec(css);
    assert.ok(found, `${token} is gone`);
    assert.equal(found[1].trim(), expected);
  }

  // The bounce curve must actually overshoot, and the damped one must not.
  const ramp = (name: string): number[] => {
    const found = new RegExp(`--${name}:\\s*linear\\(([^)]+)\\)`).exec(css);
    assert.ok(found, `--${name} is no longer a linear() ramp`);
    return found[1].split(",").map((n) => Number(n.trim()));
  };
  assert.ok(Math.max(...ramp("spring-bounce")) > 1, "bounce spring stopped overshooting");
  assert.ok(Math.max(...ramp("spring")) <= 1, "damped spring should never overshoot");
});
