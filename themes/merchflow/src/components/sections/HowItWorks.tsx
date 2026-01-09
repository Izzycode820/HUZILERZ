import React from "react";
import { cn } from "@/lib/utils";

const STEPS = [
    {
        number: "01",
        title: "Choose An Item",
        description: "Browse our catalog of over 500 premium products including t-shirts, hoodies, mugs, and more."
    },
    {
        number: "02",
        title: "Customize The Item",
        description: "Use our easy design tool to add your logos, text, and artwork to your chosen products."
    },
    {
        number: "03",
        title: "Complete Your Purchase",
        description: "Place your order and we'll handle printing, packaging, and shipping directly to you or your customers."
    }
];

export function HowItWorks() {
    return (
        <section className="py-24 bg-[#FFF5F5] overflow-hidden">
            <div className="container mx-auto px-4">
                {/* Header */}
                <div className="text-center max-w-3xl mx-auto mb-16">
                    <h2 className="text-4xl font-bold text-gray-900 mb-4 uppercase tracking-wide">Here's How It Works</h2>
                    <p className="text-gray-600 text-lg">
                        Create and sell beautiful custom products in minutes. MerchFlow prints and delivers 1000+ products at the lowest prices around. No risk, all reward.
                    </p>
                </div>

                <div className="grid md:grid-cols-2 gap-12 items-center">
                    {/* Left Column: Steps */}
                    <div className="space-y-12">
                        {STEPS.map((step) => (
                            <div key={step.number} className="flex gap-6 group">
                                <div className="flex-shrink-0">
                                    <span className="w-12 h-12 rounded-full bg-[#EB4335] text-white flex items-center justify-center font-bold text-lg shadow-lg group-hover:scale-110 transition-transform duration-300">
                                        {step.number}
                                    </span>
                                </div>
                                <div className="space-y-2">
                                    <h3 className="text-xl font-bold text-gray-900 group-hover:text-[#EB4335] transition-colors">
                                        {step.title}
                                    </h3>
                                    <p className="text-gray-500 leading-relaxed">
                                        {step.description}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Right Column: Illustration */}
                    <div className="relative">
                        {/* Decorative Elements */}
                        <div className="absolute -top-10 -right-10 w-64 h-64 bg-red-100 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob" />
                        <div className="absolute -bottom-10 -left-10 w-64 h-64 bg-pink-100 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob animation-delay-2000" />

                        {/* Main Image Container */}
                        <div className="relative bg-white rounded-3xl shadow-2xl p-8 border border-gray-100 transform hover:rotate-1 transition-transform duration-500">
                            {/* Simulating the UI in the image */}
                            <div className="flex gap-4">
                                {/* Person Illustration Placeholder */}
                                <div className="w-1/3 flex items-end">
                                    <img
                                        src="https://placehold.co/150x300/FCA5A5/FFFFFF/png?text=User"
                                        alt="User customizing"
                                        className="rounded-xl w-full"
                                    />
                                </div>
                                {/* Interface */}
                                <div className="w-2/3 space-y-4">
                                    <div className="flex gap-2 mb-4">
                                        <div className="w-3 h-3 rounded-full bg-red-400" />
                                        <div className="w-3 h-3 rounded-full bg-yellow-400" />
                                        <div className="w-3 h-3 rounded-full bg-green-400" />
                                    </div>
                                    <div className="grid grid-cols-3 gap-2">
                                        <div className="aspect-square bg-blue-100 rounded-lg flex items-center justify-center border-2 border-red-500 relative">
                                            <span className="text-xs text-blue-500">Shirt</span>
                                            {/* Cursor */}
                                            <div className="absolute -bottom-2 -right-2 w-4 h-4 bg-black transform rotate-45" />
                                        </div>
                                        <div className="aspect-square bg-red-100 rounded-lg flex items-center justify-center">
                                            <span className="text-xs text-red-500">Gift</span>
                                        </div>
                                        <div className="aspect-square bg-gray-100 rounded-lg flex items-center justify-center">
                                            <span className="text-xs text-gray-500">Watch</span>
                                        </div>
                                    </div>
                                    <div className="h-4 bg-gray-100 rounded w-full" />
                                    <div className="h-4 bg-gray-100 rounded w-3/4" />
                                    <button className="w-full bg-[#6366F1] text-white py-2 rounded-lg font-bold text-sm mt-4">
                                        SHOP
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
