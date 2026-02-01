import React from 'react';
import ReactFlow, { Background, Controls, type Edge, type Node } from 'reactflow';
import 'reactflow/dist/style.css';

import { mindmapService } from '../api/services';
import type { TopicMindmap as TopicMindmapPayload } from '../types';
import { Loading } from './ui/Loading';

const mindmapCache = new Map<string, TopicMindmapPayload>();
const mindmapErrorCache = new Map<string, string>();

const nodeColors: Record<string, { bg: string; border: string; text: string }> = {
    center: { bg: '#111827', border: '#374151', text: '#f9fafb' },
    definition: { bg: '#e0f2fe', border: '#38bdf8', text: '#0c4a6e' },
    formula: { bg: '#f0fdf4', border: '#4ade80', text: '#166534' },
    example: { bg: '#fffbeb', border: '#facc15', text: '#78350f' },
    section: { bg: '#f3f4f6', border: '#9ca3af', text: '#1f2937' },
    key_point: { bg: '#eef2ff', border: '#818cf8', text: '#3730a3' },
};

function buildLayout(nodes: Node[], edges: Edge[]): Node[] {
    const byId = new Map(nodes.map((n) => [n.id, n] as const));
    const children = new Map<string, string[]>();
    for (const e of edges) {
        const src = String(e.source);
        const tgt = String(e.target);
        if (!children.has(src)) children.set(src, []);
        children.get(src)!.push(tgt);
    }

    const rootId = 'central';
    const levels: string[][] = [];
    const visited = new Set<string>([rootId]);
    let frontier = [rootId];

    while (frontier.length > 0 && levels.length < 6) {
        const next: string[] = [];
        for (const id of frontier) {
            const kids = children.get(id) || [];
            for (const k of kids) {
                if (!visited.has(k)) {
                    visited.add(k);
                    next.push(k);
                }
            }
        }
        if (next.length === 0) break;
        levels.push(next);
        frontier = next;
    }

    const laidOut: Node[] = [];

    const root = byId.get(rootId);
    if (root) {
        laidOut.push({
            ...root,
            position: { x: 0, y: 0 },
        });
    }

    const yStep = 180;
    const xStep = 250;

    for (let depth = 0; depth < levels.length; depth++) {
        const level = levels[depth];
        const count = level.length;
        const y = (depth + 1) * yStep;
        const width = (count - 1) * xStep;
        for (let i = 0; i < count; i++) {
            const id = level[i];
            const node = byId.get(id);
            if (!node) continue;
            const x = -width / 2 + i * xStep;
            laidOut.push({
                ...node,
                position: { x, y },
            });
        }
    }

    // Include any remaining nodes (fallback) spaced below
    let extrasY = (levels.length + 1) * yStep;
    for (const n of nodes) {
        if (laidOut.find((x) => x.id === n.id)) continue;
        laidOut.push({
            ...n,
            position: { x: 0, y: extrasY },
        });
        extrasY += 80;
    }

    return laidOut;
}

function toReactFlow(payload: TopicMindmapPayload): { nodes: Node[]; edges: Edge[] } {
    const nodes: Node[] = payload.nodes.map((n) => {
        const colors = nodeColors[n.type] || { bg: '#ffffff', border: '#d1d5db', text: '#111827' };
        return {
            id: n.id,
            data: { label: n.label },
            position: { x: 0, y: 0 },
            style: {
                background: colors.bg,
                border: `2px solid ${colors.border}`,
                color: colors.text,
                borderRadius: '9999px',
                padding: '12px 20px',
                fontWeight: 600,
                fontSize: '14px',
                maxWidth: 280,
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
            },
        };
    });

    const edges: Edge[] = payload.edges.map((e, idx) => ({
        id: `e${idx}-${e.source}-${e.target}`,
        source: e.source,
        target: e.target,
        animated: true,
        type: 'smoothstep',
        style: { strokeWidth: 2.5, stroke: '#cbd5e1' },
    }));

    return { nodes: buildLayout(nodes, edges), edges };
}

export function TopicMindmap({ topicId }: { topicId: string }) {
    const [data, setData] = React.useState<TopicMindmapPayload | null>(null);
    const [error, setError] = React.useState<string | null>(null);
    const [isLoading, setIsLoading] = React.useState(false);

    React.useEffect(() => {
        let mounted = true;

        const cached = mindmapCache.get(topicId);
        const cachedErr = mindmapErrorCache.get(topicId);

        if (cached) {
            setData(cached);
            return;
        }
        if (cachedErr) {
            setError(cachedErr);
            return;
        }

        (async () => {
            setIsLoading(true);
            try {
                const resp = await mindmapService.getTopicMindmap(topicId);
                if (!mounted) return;
                mindmapCache.set(topicId, resp.data);
                setData(resp.data);
            } catch (e: any) {
                const msg = e?.response?.data?.detail || 'Mindmap will appear after sufficient content is indexed for this topic.';
                mindmapErrorCache.set(topicId, msg);
                if (!mounted) return;
                setError(msg);
            } finally {
                if (mounted) setIsLoading(false);
            }
        })();

        return () => {
            mounted = false;
        };
    }, [topicId]);

    if (isLoading) {
        return (
            <div className="h-full flex items-center justify-center">
                <Loading size="sm" text="Generating mindmap..." />
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-full flex items-center justify-center text-xs font-bold text-muted-foreground text-center px-6">
                {error}
            </div>
        );
    }

    if (!data) return null;

    const rf = toReactFlow(data);

    return (
        <div className="w-full h-full">
            <ReactFlow
                nodes={rf.nodes}
                edges={rf.edges}
                nodesDraggable={false}
                nodesConnectable={false}
                elementsSelectable={false}
                fitView
                fitViewOptions={{ padding: 0.2, duration: 800 }}
            >
                <Background gap={18} size={1} color="#e2e8f0" />
                <Controls showInteractive={false} />
            </ReactFlow>
        </div>
    );
}
