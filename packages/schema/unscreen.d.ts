/* Generated from services/engine/engine/model. Do not edit; run `pnpm schema`. */

/**
 * Root that pulls every wire type into one schema.
 */
export interface UnScreenSchema {
  client_message: Hello | Frame | PointerMsg | Ask | Settings;
  document: Document;
  server_message: Snapshot | Patch | Announce | PointerTarget | Answer | Status | Error;
  session_grant: SessionGrant;
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Hello".
 */
export interface Hello {
  caps: ClientCaps;
  client: string;
  resume_version: number | null;
  type: "hello";
}
export interface ClientCaps {
  max_width: number;
  webp: boolean;
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Frame".
 */
export interface Frame {
  change_score: number;
  /**
   * @maxItems 4096
   */
  changed_tiles: number[];
  h: number;
  mime: "image/webp" | "image/jpeg" | "image/png";
  pointer: Point | null;
  seq: number;
  ts: number;
  type: "frame";
  w: number;
}
/**
 * Normalised 0..1000 of the full frame.
 *
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Point".
 */
export interface Point {
  x: number;
  y: number;
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "PointerMsg".
 */
export interface PointerMsg {
  type: "pointer";
  xy: Point;
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Ask".
 */
export interface Ask {
  q: string;
  type: "ask";
  version: number;
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Settings".
 */
export interface Settings {
  focus_ref: string | null;
  numeric_style: "old_to_new" | "new_only";
  type: "settings";
  verbosity: "all" | "important" | "quiet";
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Document".
 */
export interface Document {
  blocks: Block[] | null;
  code: Code | null;
  content_bbox: Box;
  content_type: "sheet" | "code" | "slide" | "doc" | "unknown";
  sheet: Sheet | null;
  title: string | null;
  version: number;
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Block".
 */
export interface Block {
  bbox: Box;
  confidence: number;
  id: string;
  kind: "heading" | "paragraph" | "list_item" | "figure" | "table_ref";
  level: number | null;
  text: string;
  uncertain: boolean;
  unreadable: boolean;
}
/**
 * Axis-aligned box, normalised 0..1000 (x grows right, y grows down).
 *
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Box".
 */
export interface Box {
  x0: number;
  x1: number;
  y0: number;
  y1: number;
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Code".
 */
export interface Code {
  file_name: string | null;
  language: string | null;
  lines: CodeLine[];
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "CodeLine".
 */
export interface CodeLine {
  bbox: Box;
  confidence: number;
  id: string;
  n: number | null;
  text: string;
  uncertain: boolean;
  unreadable: boolean;
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Sheet".
 */
export interface Sheet {
  columns: Cell[];
  header_rows: number;
  rows: Row[];
  sheet_name: string | null;
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Cell".
 */
export interface Cell {
  bbox: Box;
  confidence: number;
  id: string;
  text: string;
  uncertain: boolean;
  unreadable: boolean;
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Row".
 */
export interface Row {
  cells: Cell[];
  id: string;
  key: string | null;
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Snapshot".
 */
export interface Snapshot {
  doc: Document;
  type: "snapshot";
  version: number;
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Patch".
 */
export interface Patch {
  base: number;
  ops: PatchOp[];
  type: "patch";
  version: number;
}
/**
 * RFC 6902 operation. Only add, remove and replace are emitted.
 *
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "PatchOp".
 */
export interface PatchOp {
  op: "add" | "remove" | "replace";
  path: string;
  value: unknown;
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Announce".
 */
export interface Announce {
  kind:
    | "content_type"
    | "title"
    | "cell"
    | "row_added"
    | "row_removed"
    | "scroll"
    | "line"
    | "lines_added"
    | "lines_removed"
    | "block"
    | "uncertain"
    | "status";
  priority: "content_type" | "focus" | "other";
  refs: string[];
  text: string;
  type: "announce";
  version: number;
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "PointerTarget".
 */
export interface PointerTarget {
  ref: string | null;
  text: string;
  type: "pointer_target";
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Answer".
 */
export interface Answer {
  q: string;
  refs: string[];
  text: string;
  type: "answer";
  version: number;
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Status".
 */
export interface Status {
  content_bbox: Box | null;
  detail: string | null;
  latency_ms: number | null;
  stage: "idle" | "classify" | "reconstruct" | "region" | "verify" | "diff" | "busy" | "ask";
  type: "status";
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "Error".
 */
export interface Error {
  code:
    "bad_message" | "bad_frame" | "rate_limited" | "engine_busy" | "model_error" | "session_expired" | "unauthorized";
  message: string;
  type: "error";
}
/**
 * Response of POST /v1/session.
 *
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "SessionGrant".
 */
export interface SessionGrant {
  expires_in_s: number;
  protocol: string;
  session_id: string;
  token: string;
}
/**
 * This interface was referenced by `UnScreenSchema`'s JSON-Schema
 * via the `definition` "ClientCaps".
 */
export interface ClientCaps1 {
  max_width: number;
  webp: boolean;
}
