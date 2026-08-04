import type { IntentProfile } from "./api/generated.ts";

/**
 * Personas — the lens a repository gets answered through.
 *
 * Each preset is a hand-tuned `IntentProfile`. The fields do real work in the
 * answer prompt: `audience_framing` and `raw_text` tell the model who is
 * reading, `focus_keywords` decide which supported claims win scarce space,
 * and `output_shape_preference` picks the ordering directive. Two personas
 * asking one question get the same verified facts, ranked differently.
 *
 * Adding a preset is a data change, not a code change — keep it that way.
 */
export interface Persona {
  id: string;
  label: string;
  blurb: string;
  profile: IntentProfile;
}

export const PERSONAS: Persona[] = [
  {
    id: "contributor",
    label: "Open-source contributor",
    blurb: "Where to make a first change, and what protects it.",
    profile: {
      raw_text:
        "I want to contribute to this project and need to know where a change would go and what tests guard it",
      audience_framing: "a first-time outside contributor preparing a pull request",
      modality_weights: { change: 1, understand: 0.6 },
      focus_keywords: ["entry points", "tests", "contributing", "extension points"],
      output_shape_preference: "ranked_list",
      success_criterion: "identify a concrete file to edit and the test that covers it",
    },
  },
  {
    id: "competitor",
    label: "Competitive analyst",
    blurb: "Capabilities, limits, and where the seams are.",
    profile: {
      raw_text:
        "I am evaluating this project against a competing product and need its real capabilities, constraints, and weak seams",
      audience_framing: "a product strategist at a competing company",
      modality_weights: { evaluate: 1, compare: 0.8, understand: 0.5 },
      focus_keywords: ["features", "limits", "dependencies", "integrations", "performance"],
      output_shape_preference: "ranked_list",
      success_criterion: "a defensible read on what this codebase does and does not support",
    },
  },
  {
    id: "security",
    label: "Security reviewer",
    blurb: "Trust boundaries, inputs, secrets, and authz.",
    profile: {
      raw_text:
        "I am reviewing this codebase for security risk and need its trust boundaries and input handling",
      audience_framing: "a security engineer doing a first-pass review",
      modality_weights: { evaluate: 1, locate: 0.7 },
      focus_keywords: ["authentication", "authorization", "input validation", "secrets", "network"],
      output_shape_preference: "dossier",
      success_criterion: "enumerate where untrusted input enters and what checks it",
    },
  },
  {
    id: "integrator",
    label: "Adopter / integrator",
    blurb: "Public API, config, and cost of adoption.",
    profile: {
      raw_text:
        "I am deciding whether to adopt this library and need its public API, configuration, and operational cost",
      audience_framing: "an engineer evaluating this for production use",
      modality_weights: { understand: 1, evaluate: 0.7 },
      focus_keywords: ["public api", "configuration", "dependencies", "errors", "deployment"],
      output_shape_preference: "narrative",
      success_criterion: "know what integrating this would actually require",
    },
  },
  {
    id: "learner",
    label: "Learner",
    blurb: "How the system is shaped and why.",
    profile: {
      raw_text: "I want to understand how this codebase is structured and why it is built this way",
      audience_framing: "a developer new to this codebase",
      modality_weights: { understand: 1 },
      focus_keywords: ["architecture", "entry points", "data flow", "core abstractions"],
      output_shape_preference: "narrative",
      success_criterion: "explain the system's shape to someone else",
    },
  },
  {
    id: "maintainer",
    label: "Maintainer",
    blurb: "Fragility, debt, and what needs attention.",
    profile: {
      raw_text:
        "I maintain code like this and need to know where it is fragile, untested, or accumulating debt",
      audience_framing: "a maintainer triaging technical debt",
      modality_weights: { evaluate: 1, change: 0.6 },
      focus_keywords: ["complexity", "coupling", "test coverage", "error handling", "deprecated"],
      output_shape_preference: "ranked_list",
      success_criterion: "a prioritized list of areas that need attention",
    },
  },
];

export const CUSTOM_PERSONA_ID = "custom";

export function personaById(id: string): Persona | undefined {
  return PERSONAS.find((persona) => persona.id === id);
}

/**
 * Best-effort profile for free text, used when the server-side intent profiler
 * is unavailable. `raw_text` alone is a valid profile — the answer prompt just
 * gets less to work with.
 */
export function fallbackCustomProfile(rawText: string): IntentProfile {
  return { raw_text: rawText.trim() };
}
