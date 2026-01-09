"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

export default function ProductTabs() {
    const [activeTab, setActiveTab] = useState("desc");

    return (
        <div className="mt-20">
            <div className="flex justify-center border-b border-gray-200 mb-8">
                <button
                    onClick={() => setActiveTab("desc")}
                    className={cn(
                        "px-8 py-4 font-semibold text-lg text-secondary border-b-2 border-transparent hover:text-primary transition-colors",
                        activeTab === "desc" && "border-primary text-secondary"
                    )}
                >
                    Description
                </button>
                <button
                    onClick={() => setActiveTab("spec")}
                    className={cn(
                        "px-8 py-4 font-semibold text-lg text-secondary border-b-2 border-transparent hover:text-primary transition-colors",
                        activeTab === "spec" && "border-primary text-secondary"
                    )}
                >
                    Specification
                </button>
                <button
                    onClick={() => setActiveTab("reviews")}
                    className={cn(
                        "px-8 py-4 font-semibold text-lg text-secondary border-b-2 border-transparent hover:text-primary transition-colors",
                        activeTab === "reviews" && "border-primary text-secondary"
                    )}
                >
                    Reviews ( 2 )
                </button>
            </div>

            <div className="max-w-4xl mx-auto">
                {activeTab === "desc" && (
                    <div className="space-y-4 text-gray-600">
                        <h6 className="text-secondary font-bold uppercase mb-2">Description</h6>
                        <p>Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut loret fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt loret. Neque porro lorem quisquam est, qui dolorem ipsum quia dolor si. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut loret fugit, sed quia ipsu consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Nulla consequat massa quis enim.</p>
                        <p>Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem.</p>
                    </div>
                )}
                {activeTab === "spec" && (
                    <div className="space-y-4 text-gray-600">
                        <h6 className="text-secondary font-bold uppercase mb-2">Specification</h6>
                        <p>Specification content goes here...</p>
                    </div>
                )}
                {activeTab === "reviews" && (
                    <div className="space-y-4 text-gray-600">
                        <h6 className="text-secondary font-bold uppercase mb-2">Reviews</h6>
                        <p>Reviews content goes here...</p>
                    </div>
                )}
            </div>
        </div>
    );
}
