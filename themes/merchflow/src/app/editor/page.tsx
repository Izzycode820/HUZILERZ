import React, { Suspense } from "react";
import { CanvasEditor } from "@/components/canvas/CanvasEditor";

export default function EditorPage() {
    return (
        <Suspense fallback={<div className="flex h-screen items-center justify-center">Loading Editor...</div>}>
            <CanvasEditor />
        </Suspense>
    );
}
