"use client";

import React, { useState } from "react";
import { PRODUCTS } from "@/lib/data/products";
import { ProductConfig, ProductView } from "@/lib/types/canvas";
import { Layers, Image as ImageIcon, Type, ArrowLeft, Download, Eye } from "lucide-react";
import { cn } from "@/lib/utils";
import * as fabric from "fabric";
import { useSearchParams } from "next/navigation";


import { FabricCanvas } from "./FabricCanvas";

// Placeholder for the Canvas Component
const CanvasWorkbench = ({ product, view, onCanvasReady }: { product: ProductConfig, view: ProductView, onCanvasReady: (canvas: fabric.Canvas) => void }) => {
    return (
        <div className="relative w-full h-full flex items-center justify-center bg-gray-50 border-2 border-dashed border-gray-200 m-4 rounded-xl">
            {/* Editor Base Image */}
            <div className="relative h-[80%] aspect-[3/4] shadow-sm border border-gray-200 bg-white">
                <img
                    src={view.editorBaseImage}
                    alt={view.name}
                    className="w-full h-full object-contain p-4 pointer-events-none select-none"
                />

                {/* Print Area Guide (Dotted Line) & Interactive Canvas */}
                <div
                    className="absolute border-2 border-dashed border-[#EB4335] bg-[#EB4335]/5 overflow-hidden"
                    style={{
                        top: `${view.printArea.top}%`,
                        left: `${view.printArea.left}%`,
                        width: `${view.printArea.width}%`,
                        height: `${view.printArea.height}%`
                    }}
                >
                    {/* The Fabric Canvas lives here */}
                    <FabricCanvas view={view} onCanvasReady={onCanvasReady} />

                    {/* Label */}
                    <span className="absolute -top-6 left-0 text-[10px] font-bold text-[#EB4335] uppercase tracking-wider bg-white px-1 pointer-events-none">Print Area</span>
                </div>
            </div>
        </div>
    );
};

export function CanvasEditor() {
    const searchParams = useSearchParams();
    const initialProductId = searchParams.get("product") || PRODUCTS[0].id; // Default to first product if none

    const [activeProduct, setActiveProduct] = useState<ProductConfig>(
        PRODUCTS.find(p => p.id === initialProductId) || PRODUCTS[0]
    );
    // Initialize view based on the (potentially new) activeProduct
    const [activeViewId, setActiveViewId] = useState<string>(activeProduct.views[0].id);
    const activeView = activeProduct.views.find(v => v.id === activeViewId) || activeProduct.views[0];

    // Effect: Update state when URL changes or initial load 
    React.useEffect(() => {
        const productId = searchParams.get("product");
        if (productId) {
            const foundProduct = PRODUCTS.find(p => p.id === productId);
            if (foundProduct) {
                setActiveProduct(foundProduct);
                setActiveViewId(foundProduct.views[0].id);
            }
        }
    }, [searchParams]);

    // Handle Image Upload
    const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file || !fabricCanvasRef.current) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            const imgObj = new Image();
            imgObj.src = e.target?.result as string;
            imgObj.onload = () => {
                const fabricImg = new fabric.Image(imgObj);

                // Scale down if too big
                fabricImg.scaleToWidth(200);

                fabricCanvasRef.current?.add(fabricImg);
                fabricCanvasRef.current?.centerObject(fabricImg);
                fabricCanvasRef.current?.setActiveObject(fabricImg);
                fabricCanvasRef.current?.renderAll();
            };
        };
        reader.readAsDataURL(file);

        // Reset input
        event.target.value = '';
    };

    const fabricCanvasRef = React.useRef<fabric.Canvas | null>(null);
    const fileInputRef = React.useRef<HTMLInputElement>(null);

    const handleCanvasReady = (canvas: fabric.Canvas) => {
        fabricCanvasRef.current = canvas;
    };

    return (
        <div className="fixed inset-0 z-50 bg-white flex flex-col">
            {/* Top Bar */}
            <header className="h-16 border-b border-gray-200 flex items-center justify-between px-4">
                <div className="flex items-center gap-4">
                    <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                        <ArrowLeft className="w-5 h-5 text-gray-600" />
                    </button>
                    <div>
                        <h1 className="font-bold text-gray-900 leading-tight">{activeProduct.name}</h1>
                        <span className="text-xs text-gray-500">Design Mode</span>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <button className="flex items-center gap-2 px-4 py-2 text-sm font-bold text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
                        <Eye className="w-4 h-4" />
                        Preview
                    </button>
                    <button className="flex items-center gap-2 px-6 py-2 text-sm font-bold text-white bg-[#EB4335] hover:bg-[#D33025] rounded-lg transition-colors shadow-sm">
                        Save Product
                    </button>
                </div>
            </header>

            {/* Main Workspace */}
            <div className="flex-1 flex overflow-hidden">
                {/* Left Sidebar (Assets) */}
                <aside className="w-20 border-r border-gray-200 flex flex-col items-center py-6 gap-6 bg-white shrink-0">
                    {/* Hidden File Input */}
                    <input
                        type="file"
                        ref={fileInputRef}
                        className="hidden"
                        accept="image/*"
                        onChange={handleImageUpload}
                    />

                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="flex flex-col items-center gap-1.5 group"
                    >
                        <div className="w-10 h-10 rounded-lg bg-gray-50 group-hover:bg-[#EB4335]/10 flex items-center justify-center transition-colors">
                            <ImageIcon className="w-5 h-5 text-gray-600 group-hover:text-[#EB4335]" />
                        </div>
                        <span className="text-[10px] font-medium text-gray-500 group-hover:text-[#EB4335]">Upload</span>
                    </button>
                    <button className="flex flex-col items-center gap-1.5 group">
                        <div className="w-10 h-10 rounded-lg bg-gray-50 group-hover:bg-[#EB4335]/10 flex items-center justify-center transition-colors">
                            <Type className="w-5 h-5 text-gray-600 group-hover:text-[#EB4335]" />
                        </div>
                        <span className="text-[10px] font-medium text-gray-500 group-hover:text-[#EB4335]">Text</span>
                    </button>
                    <button className="flex flex-col items-center gap-1.5 group">
                        <div className="w-10 h-10 rounded-lg bg-gray-50 group-hover:bg-[#EB4335]/10 flex items-center justify-center transition-colors">
                            <Layers className="w-5 h-5 text-gray-600 group-hover:text-[#EB4335]" />
                        </div>
                        <span className="text-[10px] font-medium text-gray-500 group-hover:text-[#EB4335]">Layers</span>
                    </button>
                    <div className="h-px w-10 bg-gray-200 my-2" />
                </aside>

                {/* Center Canvas */}
                <main className="flex-1 bg-gray-100 flex flex-col">
                    <CanvasWorkbench product={activeProduct} view={activeView} onCanvasReady={handleCanvasReady} />

                    {/* Bottom View Switcher */}
                    <div className="h-16 bg-white border-t border-gray-200 flex items-center justify-center gap-2 px-4">
                        {activeProduct.views.map((view) => (
                            <button
                                key={view.id}
                                onClick={() => setActiveViewId(view.id)}
                                className={cn(
                                    "px-4 py-1.5 text-xs font-bold rounded-full border transition-all",
                                    activeViewId === view.id
                                        ? "bg-gray-900 text-white border-gray-900"
                                        : "bg-white text-gray-600 border-gray-300 hover:border-gray-400"
                                )}
                            >
                                {view.name}
                            </button>
                        ))}
                    </div>
                </main>

                {/* Right Sidebar (Settings) - Collapsible or Context Aware */}
                <aside className="w-80 border-l border-gray-200 bg-white hidden xl:flex flex-col">
                    <div className="p-4 border-b border-gray-200">
                        <h3 className="font-bold text-gray-900">Variants & Layers</h3>
                    </div>
                    <div className="p-4">
                        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Product Colors</h4>
                        <div className="flex flex-wrap gap-2">
                            {activeProduct.colors.map((color) => (
                                <button
                                    key={color.name}
                                    title={color.name}
                                    className="w-8 h-8 rounded-full border border-gray-200 shadow-sm hover:scale-110 transition-transform"
                                    style={{ backgroundColor: color.hex }}
                                />
                            ))}
                        </div>
                    </div>
                </aside>
            </div>
        </div>
    );
}
