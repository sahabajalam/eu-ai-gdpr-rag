"use client"

import React, { useEffect } from 'react';
import ReactFlow, {
    Node,
    Edge,
    Background,
    Controls,
    useNodesState,
    useEdgesState,
    MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

interface GraphData {
    nodes: Array<{
        id: string;
        label: string;
        title: string;
        type: string; // 'retrieved' | 'cited'
    }>;
    edges: Array<{
        id: string;
        source: string;
        target: string;
    }>;
}

interface GraphVisualizerProps {
    data: GraphData;
    onNodeSelect?: (nodeId: string) => void;
}

export const GraphVisualizer = React.memo(function GraphVisualizer({ data, onNodeSelect }: GraphVisualizerProps) {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    // Memoize the layout calculation to prevent re-calc on every render
    useEffect(() => {
        if (!data || !data.nodes || data.nodes.length === 0) {
            setNodes([]);
            setEdges([]);
            return;
        }

        const convertedNodes: Node[] = data.nodes.map((n, i) => {
            const isRetrieved = n.type === 'retrieved';
            const angle = (i / data.nodes.length) * 2 * Math.PI;
            const radius = isRetrieved ? 100 : 250;

            return {
                id: n.id,
                position: {
                    x: 250 + radius * Math.cos(angle),
                    y: 250 + radius * Math.sin(angle)
                },
                data: { label: n.label },
                style: {
                    background: isRetrieved ? '#3b82f6' : '#e2e8f0',
                    color: isRetrieved ? '#fff' : '#000',
                    border: '1px solid #777',
                    width: 150,
                    fontSize: 12,
                    cursor: 'pointer'
                },
            };
        });

        const convertedEdges: Edge[] = data.edges.map((e) => ({
            id: e.id,
            source: e.source,
            target: e.target,
            animated: true,
            markerEnd: {
                type: MarkerType.ArrowClosed,
            },
            style: { stroke: '#94a3b8' }
        }));

        setNodes(convertedNodes);
        setEdges(convertedEdges);

    }, [data, setNodes, setEdges]);

    return (
        <div className="w-full h-full border rounded-lg bg-gray-50">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={(_, node) => onNodeSelect?.(node.id)}
                fitView
            >
                <Background />
                <Controls />
            </ReactFlow>
        </div>
    );
});
