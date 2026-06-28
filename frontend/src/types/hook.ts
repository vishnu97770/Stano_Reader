export interface HookResult {
  stroke_id: string;
  is_hook: boolean;
  hook_type: string | null;   // "L_HOOK_INITIAL" | "R_HOOK_INITIAL" | "N_HOOK_FINAL" | "FV_HOOK_FINAL"
  position: string | null;    // "INITIAL" | "FINAL"
  phoneme: string | null;
  confidence: number;
  reasoning: string | null;
}
