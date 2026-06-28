import type { AIRefinementResult, Domain } from '../../types/ai';
import { DOMAIN_LABELS } from '../../types/ai';

interface AIPanelProps {
  result: AIRefinementResult | null;
  isRefining: boolean;
  error: string | null;
  enabled: boolean;
  domain: Domain;
  onToggle: (enabled: boolean) => void;
  onDomainChange: (domain: Domain) => void;
}

const DOMAINS: Domain[] = ['general', 'legal', 'diplomatic', 'parliamentary'];

export default function AIPanel({
  result,
  isRefining,
  error,
  enabled,
  domain,
  onToggle,
  onDomainChange,
}: AIPanelProps) {
  const hasRefinement = result !== null && !result.fallback_used;

  return (
    <div className="flex flex-col shrink-0 bg-white rounded-lg border border-gray-200">
      {/* Header + toggle */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          AI Refinement
        </h2>
        <span className="text-[10px] text-gray-400">β</span>

        {enabled && isRefining && (
          <span className="ml-auto text-xs text-indigo-500 animate-pulse">
            querying…
          </span>
        )}

        {/* Toggle */}
        <button
          onClick={() => onToggle(!enabled)}
          className={`ml-auto w-8 h-4 rounded-full transition-colors relative ${
            enabled ? 'bg-indigo-500' : 'bg-gray-200'
          }`}
          title={enabled ? 'Disable AI refinement' : 'Enable AI refinement'}
          aria-label={enabled ? 'Disable AI refinement' : 'Enable AI refinement'}
        >
          <span
            className={`absolute top-0.5 left-0.5 w-3 h-3 rounded-full bg-white shadow transition-transform ${
              enabled ? 'translate-x-4' : 'translate-x-0'
            }`}
          />
        </button>
      </div>

      <div className="px-4 py-3 space-y-3">
        {/* Domain selector */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-gray-400 uppercase tracking-wide shrink-0">
            Domain
          </span>
          <select
            value={domain}
            onChange={(e) => onDomainChange(e.target.value as Domain)}
            disabled={!enabled}
            className="flex-1 text-xs bg-gray-50 border border-gray-200 rounded px-1.5 py-1 text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {DOMAINS.map((d) => (
              <option key={d} value={d}>
                {DOMAIN_LABELS[d]}
              </option>
            ))}
          </select>
        </div>

        {/* Status / results */}
        {!enabled && (
          <p className="text-xs text-gray-400">
            Enable to let a local LLM re-rank candidates using context.
          </p>
        )}

        {enabled && error && (
          <p className="text-xs text-red-500">{error}</p>
        )}

        {enabled && !error && !result && !isRefining && (
          <p className="text-xs text-gray-400">
            Draw a stroke to trigger refinement.
          </p>
        )}

        {enabled && result?.fallback_used && !isRefining && !error && (
          <p className="text-xs text-gray-400">
            {result.was_invoked
              ? 'Ollama unavailable — using deterministic ranking.'
              : 'Using deterministic ranking (skip rule matched).'}
          </p>
        )}

        {enabled && hasRefinement && (
          <div className="space-y-2">
            {result.promoted_candidate && (
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-gray-400 uppercase tracking-wide shrink-0">
                  Promoted
                </span>
                <span className="text-sm font-semibold text-indigo-700">
                  ✦ {result.promoted_candidate}
                </span>
                <span className="text-[10px] font-mono text-emerald-600 ml-auto">
                  +{Math.round(result.confidence_boost * 100)}%
                </span>
              </div>
            )}

            {result.reasoning && (
              <div>
                <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-0.5">
                  Reasoning
                </p>
                <p className="text-xs text-gray-600 leading-relaxed">{result.reasoning}</p>
              </div>
            )}

            {/* Ranking comparison */}
            {result.original_ranking.length > 0 && (
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-0.5">
                    Before
                  </p>
                  <ol className="space-y-0.5">
                    {result.original_ranking.slice(0, 5).map((w, i) => (
                      <li key={w} className="text-xs text-gray-500 font-mono">
                        <span className="text-gray-300 mr-1">{i + 1}.</span>
                        {w}
                      </li>
                    ))}
                  </ol>
                </div>
                <div>
                  <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-0.5">
                    After ✦
                  </p>
                  <ol className="space-y-0.5">
                    {result.refined_ranking.slice(0, 5).map((w, i) => (
                      <li
                        key={w}
                        className={`text-xs font-mono ${
                          w === result.promoted_candidate
                            ? 'text-indigo-600 font-semibold'
                            : 'text-gray-500'
                        }`}
                      >
                        <span className="text-gray-300 mr-1">{i + 1}.</span>
                        {w}
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
