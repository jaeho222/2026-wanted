"use client";

import { useMemo, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  type Node,
  type Edge,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import type { OpinionMap, Claim, RelationType } from "../types";

// stance 별 노드 색 (밝은 배경 모던 팔레트)
const STANCE_STYLE: Record<string, { bg: string; border: string }> = {
  positive: { bg: "#e0f2fe", border: "#0284c7" }, // 파랑
  negative: { bg: "#ffe4e6", border: "#e11d48" }, // 빨강
  neutral: { bg: "#f4f4f5", border: "#71717a" }, // 회색
};

// relation 별 엣지 색
const RELATION_STYLE: Record<RelationType, { stroke: string; label: string }> = {
  support: { stroke: "#16a34a", label: "지지" },
  attack: { stroke: "#dc2626", label: "반박" },
  related: { stroke: "#a1a1aa", label: "연관" },
};

// claim 들을 원형으로 배치 (외부 레이아웃 라이브러리 없이)
function layoutNodes(claims: Claim[]): Node[] {
  const cx = 400;
  const cy = 300;
  const radius = 220;
  return claims.map((c, i) => {
    // 첫 노드는 중앙, 나머지는 원형
    const isCenter = i === 0;
    const angle = (2 * Math.PI * (i - 1)) / Math.max(claims.length - 1, 1);
    const x = isCenter ? cx : cx + radius * Math.cos(angle);
    const y = isCenter ? cy : cy + radius * Math.sin(angle);
    // count 클수록 노드 크게
    const size = 90 + Math.min(c.count / 30, 70);
    const style = STANCE_STYLE[c.stance] ?? STANCE_STYLE.neutral;
    return {
      id: c.id,
      position: { x, y },
      data: { label: `${c.text}\n(${c.count.toLocaleString()})` },
      style: {
        width: size,
        height: size,
        borderRadius: "50%",
        background: style.bg,
        border: `2px solid ${style.border}`,
        fontSize: 12,
        fontWeight: 600,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center" as const,
        padding: 8,
        whiteSpace: "pre-line" as const,
        color: "#1f2937",
      },
    };
  });
}

export default function OpinionMapOverlay({
  data,
  onClose,
}: {
  data: OpinionMap;
  onClose: () => void;
}) {
  const [selected, setSelected] = useState<Claim | null>(null);
  const [innerUrl, setInnerUrl] = useState("");

  const nodes = useMemo(() => layoutNodes(data.claims), [data]);

  const edges: Edge[] = useMemo(
    () =>
      data.relations.map((r, i) => {
        const s = RELATION_STYLE[r.type];
        return {
          id: `e${i}`,
          source: r.from,
          target: r.to,
          label: s.label,
          animated: r.type === "attack",
          style: { stroke: s.stroke, strokeWidth: 2 },
          labelStyle: { fill: s.stroke, fontSize: 11, fontWeight: 600 },
          markerEnd: { type: MarkerType.ArrowClosed, color: s.stroke },
        };
      }),
    [data]
  );

  // 가장 큰 논쟁 = count 최대 claim
  const biggest = [...data.claims].sort((a, b) => b.count - a.count)[0];
  const hidden = data.hidden_opinions[0];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="flex h-[85vh] w-full max-w-6xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
        {/* 헤더 */}
        <div className="flex items-center justify-between border-b border-neutral-100 px-6 py-4">
          <div>
            <h2 className="text-lg font-bold">{data.topic}</h2>
            {data.meta && (
              <p className="text-xs text-neutral-500">
                {data.meta.total_comments?.toLocaleString()} comments ·{" "}
                {data.claims.length} claims
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="rounded-lg px-3 py-1.5 text-sm text-neutral-500 transition hover:bg-neutral-100"
          >
            ✕ 닫기
          </button>
        </div>

        {/* 본문: 그래프 + 우측 상세 */}
        <div className="flex flex-1 overflow-hidden">
          {/* 그래프 */}
          <div className="relative flex-1">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodeClick={(_, node) => {
                const c = data.claims.find((cl) => cl.id === node.id);
                if (c) setSelected(c);
              }}
              fitView
              proOptions={{ hideAttribution: true }}
            >
              <Background color="#e5e7eb" gap={20} />
              <Controls showInteractive={false} />
            </ReactFlow>

            {/* 범례 */}
            <div className="absolute left-4 top-4 flex flex-col gap-1 rounded-lg bg-white/90 px-3 py-2 text-xs shadow">
              <span className="flex items-center gap-2">
                <span className="h-0.5 w-4 bg-green-600" /> 지지
              </span>
              <span className="flex items-center gap-2">
                <span className="h-0.5 w-4 bg-red-600" /> 반박
              </span>
              <span className="flex items-center gap-2">
                <span className="h-0.5 w-4 bg-neutral-400" /> 연관
              </span>
            </div>
          </div>

          {/* 우측 상세 패널 */}
          <div className="w-80 shrink-0 overflow-y-auto border-l border-neutral-100 p-5">
            {selected ? (
              <div>
                <button
                  onClick={() => setSelected(null)}
                  className="mb-3 text-xs text-neutral-400 hover:text-neutral-600"
                >
                  ← 인사이트로 돌아가기
                </button>
                <h3 className="text-base font-bold">{selected.text}</h3>
                <p className="mt-1 text-xs text-neutral-500">
                  {selected.count.toLocaleString()}개 댓글 · {selected.stance}
                </p>
                <h4 className="mt-4 mb-2 text-xs font-semibold text-neutral-400">
                  실제 대표 댓글
                </h4>
                <ul className="flex flex-col gap-2">
                  {selected.sample_comments.map((c, i) => (
                    <li
                      key={i}
                      className="rounded-lg bg-neutral-50 px-3 py-2 text-sm text-neutral-700"
                    >
                      “{c}”
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                <h3 className="text-sm font-semibold">이 댓글창의 인사이트</h3>

                <div className="rounded-xl border border-neutral-100 p-3">
                  <p className="text-xs font-medium text-neutral-400">
                    🔥 가장 큰 논쟁
                  </p>
                  <p className="mt-1 text-sm font-semibold">{biggest.text}</p>
                  <p className="text-xs text-neutral-500">
                    {biggest.count.toLocaleString()}개 댓글
                  </p>
                </div>

                {hidden && (
                  <div className="rounded-xl border border-neutral-100 p-3">
                    <p className="text-xs font-medium text-neutral-400">
                      👀 숨은 의견
                    </p>
                    <p className="mt-1 text-sm font-semibold">{hidden.text}</p>
                    <p className="text-xs text-neutral-500">
                      전체 {Math.round(hidden.share * 100)}% · 인기댓글{" "}
                      {Math.round(hidden.top_share * 100)}%
                    </p>
                  </div>
                )}

                <p className="text-xs text-neutral-400">
                  노드를 클릭하면 실제 대표 댓글을 볼 수 있어요.
                </p>

                {/* 맵 안에서 다른 URL 직접 입력 */}
                <div className="mt-2 border-t border-neutral-100 pt-4">
                  <p className="mb-2 text-xs font-semibold">
                    다른 영상 분석하기
                  </p>
                  <input
                    value={innerUrl}
                    onChange={(e) => setInnerUrl(e.target.value)}
                    placeholder="YouTube URL"
                    className="mb-2 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-neutral-400"
                  />
                  <button
                    onClick={() =>
                      alert("백엔드 연결 후 실시간 분석됩니다")
                    }
                    className="w-full rounded-lg bg-neutral-900 px-3 py-2 text-sm font-medium text-white hover:bg-neutral-700"
                  >
                    Analyze
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
