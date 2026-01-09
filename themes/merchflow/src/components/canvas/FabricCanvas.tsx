"use client";

import React, { useEffect, useRef, useState } from "react";
// Dynamic import for fabric to avoid SSR issues
import * as fabric from "fabric";
import { ProductView } from "@/lib/types/canvas";

interface FabricCanvasProps {
    view: ProductView;
    onCanvasReady?: (canvas: fabric.Canvas) => void;
}

export function FabricCanvas({ view, onCanvasReady }: FabricCanvasProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [fabricCanvas, setFabricCanvas] = useState<fabric.Canvas | null>(null);

    // Initialize Canvas
    useEffect(() => {
        if (!canvasRef.current || !containerRef.current) return;

        // Create Fabric Canvas
        // We start with a fixed size, but we'll resize it to fit the print area
        const canvas = new fabric.Canvas(canvasRef.current, {
            width: 500, // Initial placeholder
            height: 500,
            backgroundColor: 'transparent',
            preserveObjectStacking: true,
            selection: true,
        });

        setFabricCanvas(canvas);
        if (onCanvasReady) onCanvasReady(canvas);

        return () => {
            canvas.dispose();
        };
    }, []);

    // Handle Resizing & Updates based on View
    useEffect(() => {
        if (!fabricCanvas || !containerRef.current) return;

        // The container is the "Print Area" div provided by the parent
        const { clientWidth, clientHeight } = containerRef.current;

        fabricCanvas.setDimensions({
            width: clientWidth,
            height: clientHeight
        });

        // Optional: Add a subtle border or grid if in editor mode specific to fabric
        // For now, we keep it clean.

        fabricCanvas.renderAll();

    }, [fabricCanvas, view, containerRef.current?.clientWidth, containerRef.current?.clientHeight]);

    return (
        <div ref={containerRef} className="w-full h-full relative">
            <canvas ref={canvasRef} />
        </div>
    );
}
