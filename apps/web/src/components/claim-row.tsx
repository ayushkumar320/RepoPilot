"use client";

import { CaretDown, CaretRight, ShieldCheck, WarningCircle } from "@phosphor-icons/react";
import { useCallback, useState } from "react";

import { ApiError, api, type ClaimStatus } from "../lib/api/generated";
import type { StoredClaim } from "../lib/session-store";
import { SourceView } from "./source-view";

function claimBadgeClass(status: ClaimStatus): string {
  if (status === "flagged" || status === "rejected") {
    return "status-badge status-badge-warning";
  }
  // "unverified" = the verifier could not run (e.g. every provider was
  // exhausted). Neutral treatment — neither confirmed nor found wanting.
  if (status === "unverified") {
    return "status-badge status-badge-neutral";
  }
  return "status-badge status-badge-success";
}

function claimBadgeLabel(status: ClaimStatus): string {
  if (status === "flagged" || status === "rejected") return "Review";
  if (status === "unverified") return "Unverified";
  return "Verified";
}

/**
 * One verified source, and the code behind it.
 *
 * The claim already states a `file:line`; this is what lets a reader check it
 * without leaving the answer. It opens inline rather than in a side panel —
 * the synchronized viewer that used to occupy a third column was removed in
 * `cf18b1b`, and the point here is to make a citation checkable, not to
 * reintroduce a permanent column that is empty most of the time.
 *
 * Clicking does both jobs: it selects the claim (which re-anchors the
 * "Related code" panel below) and toggles its source. One control, because a
 * separate "view source" button beside a row that is already a button would
 * be two targets for one intent.
 */
export function ClaimRow({
  claim,
  active,
  onSelect,
}: {
  claim: StoredClaim;
  active: boolean;
  onSelect: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [source, setSource] = useState<{ content: string; startLine: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const flagged = claim.status === "flagged" || claim.status === "rejected";
  const unverified = claim.status === "unverified";
  const ref = claim.refs[0];

  const toggle = useCallback(async () => {
    onSelect();
    if (open) {
      setOpen(false);
      return;
    }
    setOpen(true);
    if (source !== null) return;
    try {
      const chunk = await api.getChunk(claim.chunkId);
      setSource({ content: chunk.content, startLine: chunk.ref.start_line });
    } catch (caught) {
      setError(
        caught instanceof ApiError ? caught.message : "Could not load the source for this claim.",
      );
    }
  }, [onSelect, open, source, claim.chunkId]);

  return (
    <div className="claim-row-wrap">
      <button
        type="button"
        className="claim-row"
        aria-expanded={open}
        data-active={active}
        data-flagged={flagged}
        data-unverified={unverified}
        onClick={() => void toggle()}
      >
        <span className="claim-icon" aria-hidden="true">
          {flagged || unverified ? (
            <WarningCircle size={19} weight="fill" />
          ) : (
            <ShieldCheck size={19} weight="fill" />
          )}
        </span>
        <span className="claim-content">
          <strong>{claim.text}</strong>
          <span className="claim-reference">
            {open ? <CaretDown size={13} aria-hidden="true" /> : <CaretRight size={13} aria-hidden="true" />}
            {ref.file_path}:{ref.start_line}-{ref.end_line}
          </span>
          {claim.verifier_note ? <small>{claim.verifier_note}</small> : null}
        </span>
        <span className={claimBadgeClass(claim.status)}>{claimBadgeLabel(claim.status)}</span>
      </button>

      {open ? (
        <div className="claim-source">
          {error ? (
            <p className="neighbour-note">{error}</p>
          ) : source === null ? (
            <p className="neighbour-note">Loading source…</p>
          ) : (
            <SourceView content={source.content} startLine={source.startLine} />
          )}
        </div>
      ) : null}
    </div>
  );
}
