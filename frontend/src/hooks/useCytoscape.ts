import { useEffect, useRef, type MutableRefObject } from 'react';
import cytoscape, { type Core, type ElementDefinition, type LayoutOptions } from 'cytoscape';
import coseBilkent from 'cytoscape-cose-bilkent';
import type { ColorMode, GraphData, GraphNode } from '@/types';
import { getNodeColor, getNodeShape, getNodeSize, computeTimeRange } from '@/utils/colorMode';

let registered = false;
function registerExtensions(): void {
  if (registered) return;
  try {
    cytoscape.use(coseBilkent);
    registered = true;
  } catch (err) {
    console.warn('[cytoscape] failed to register cose-bilkent:', err);
  }
}

export interface UseCytoscapeOptions {
  data: GraphData | null;
  colorMode: ColorMode;
  selectedNodeId: string | null;
  searchKeyword: string;
  onSelect: (node: GraphNode | null) => void;
  onHover: (node: GraphNode | null, position: { x: number; y: number }) => void;
  onZoom: (zoom: number) => void;
  onDoubleClick: (node: GraphNode) => void;
  onBackgroundDoubleClick: () => void;
}

export function useCytoscape(options: UseCytoscapeOptions): MutableRefObject<HTMLDivElement | null> {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);
  const callbacksRef = useRef(options);
  callbacksRef.current = options;

  useEffect(() => {
    registerExtensions();
    if (!containerRef.current) return undefined;

    const cy = cytoscape({
      container: containerRef.current,
      elements: [],
      minZoom: 0.2,
      maxZoom: 3,
      wheelSensitivity: 0.2,
      boxSelectionEnabled: true,
      selectionType: 'single',
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#888888',
            label: 'data(displayName)',
            color: '#F5F0E8',
            'font-family': 'JetBrains Mono, monospace',
            'font-size': 10,
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'text-outline-color': '#060A14',
            'text-outline-width': 2,
            width: 24,
            height: 24,
            'border-width': 1,
            'border-color': '#1A1F2E',
            opacity: 1,
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 3,
            'border-color': '#C9A96E',
            'overlay-color': '#C9A96E',
            'overlay-opacity': 0.15,
            'overlay-shape': 'round-rectangle',
          },
        },
        {
          selector: 'edge',
          style: {
            width: 1,
            'line-color': '#888888',
            'target-arrow-color': '#888888',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            opacity: 0.6,
          },
        },
      ],
    });

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const data = node.data() as GraphNode & { displayName?: string };
      callbacksRef.current.onSelect(data);
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        callbacksRef.current.onSelect(null);
      }
    });

    cy.on('mouseover', 'node', (evt) => {
      const node = evt.target;
      const data = node.data() as GraphNode;
      const pos = evt.renderedPosition;
      callbacksRef.current.onHover(data, { x: pos.x, y: pos.y });
    });

    cy.on('mouseout', 'node', () => {
      callbacksRef.current.onHover(null, { x: 0, y: 0 });
    });

    cy.on('dblclick', 'node', (evt) => {
      const node = evt.target;
      const data = node.data() as GraphNode;
      callbacksRef.current.onDoubleClick(data);
    });

    cy.on('dblclick', (evt) => {
      if (evt.target === cy) {
        callbacksRef.current.onBackgroundDoubleClick();
      }
    });

    cy.on('zoom', () => {
      callbacksRef.current.onZoom(cy.zoom());
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, []);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    if (!options.data) {
      cy.elements().remove();
      return;
    }
    const { nodes, edges } = options.data;
    const elements: ElementDefinition[] = [
      ...nodes.map((n) => {
        const { id: _ignoreId, ...rest } = n;
        void _ignoreId;
        return {
          group: 'nodes' as const,
          data: {
            id: n.id,
            ...rest,
            displayName: n.name,
          },
        };
      }),
      ...edges.map((e) => {
        const { source: _ignoreSource, target: _ignoreTarget, ...rest } = e;
        void _ignoreSource;
        void _ignoreTarget;
        return {
          group: 'edges' as const,
          data: {
            id: `${e.source}->${e.target}:${e.call_type}`,
            source: e.source,
            target: e.target,
            ...rest,
          },
        };
      }),
    ];
    cy.elements().remove();
    cy.add(elements);

    // cose-bilkent 的扩展选项不在 cytoscape 默认 LayoutOptions 中
    const layout = {
      name: 'cose-bilkent',
      animate: 'end',
      randomize: true,
      nodeRepulsion: 8000,
      idealEdgeLength: 80,
      edgeElasticity: 0.45,
      nestingFactor: 0.1,
      gravity: 0.25,
      numIter: 2500,
      tile: false,
      padding: 30,
    } as unknown as LayoutOptions;
    cy.layout(layout).run();
  }, [options.data]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy || !options.data) return;
    const { nodes } = options.data;
    const timeRange = computeTimeRange(nodes);
    const baseStyle = [
      {
        selector: 'node',
        style: {
          'background-color': (ele: cytoscape.NodeSingular): string => {
            const data = ele.data() as GraphNode;
            return getNodeColor(data, options.colorMode, timeRange);
          },
          width: (ele: cytoscape.NodeSingular): number => {
            const data = ele.data() as GraphNode;
            return getNodeSize(data);
          },
          height: (ele: cytoscape.NodeSingular): number => {
            const data = ele.data() as GraphNode;
            return getNodeSize(data);
          },
          shape: (ele: cytoscape.NodeSingular): string => {
            const data = ele.data() as GraphNode;
            return getNodeShape(data);
          },
          'border-color': '#1A1F2E',
          'border-width': 1,
          color: '#F5F0E8',
        },
      },
    ];
    cy.style().fromJson(baseStyle).update();
  }, [options.colorMode, options.data]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.nodes().unselect();
    if (options.selectedNodeId) {
      const node = cy.getElementById(options.selectedNodeId);
      if (node && node.length) {
        node.select();
      }
    }
  }, [options.selectedNodeId]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    const kw = options.searchKeyword.trim().toLowerCase();
    if (!kw) {
      cy.nodes().style('opacity', 1);
      cy.edges().style('opacity', 0.6);
      return;
    }
    const matchedNodes: cytoscape.NodeSingular[] = [];
    const unmatchedNodes: cytoscape.NodeSingular[] = [];
    cy.nodes().forEach((n) => {
      const data = n.data() as GraphNode;
      const author = (data.author || '').toLowerCase();
      const matches =
        data.name.toLowerCase().includes(kw) ||
        data.file_path.toLowerCase().includes(kw) ||
        author.includes(kw);
      if (matches) matchedNodes.push(n);
      else unmatchedNodes.push(n);
    });
    const matchedColl = cy.collection(matchedNodes as unknown as cytoscape.ElementDefinition[]);
    const unmatchedColl = cy.collection(unmatchedNodes as unknown as cytoscape.ElementDefinition[]);
    cy.batch(() => {
      unmatchedColl.style('opacity', 0.1);
      matchedColl.style('opacity', 1);
      cy.edges().style('opacity', 0.05);
      if (matchedColl.length > 0) {
        matchedColl.connectedEdges().style('opacity', 0.7);
      }
    });
    if (matchedColl.length > 0) {
      cy.animate({
        center: { eles: matchedColl },
        duration: 300,
        easing: 'ease-in-out-cubic',
      });
    }
  }, [options.searchKeyword]);

  return containerRef;
}
