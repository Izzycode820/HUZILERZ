import React from "react";
import { Package, Smartphone, Rocket, Coffee, Truck } from "lucide-react";

const FEATURES = [
    { icon: Package, text: "No minimum order" },
    { icon: Smartphone, text: "One on one services" },
    { icon: Rocket, text: "100% Free to use" },
    { icon: Coffee, text: "1000+ Products available" },
    { icon: Truck, text: "Free delivery for order over $80" },
];

export function ShippingInfo() {
    return (
        <section className="border-t border-b border-gray-100 bg-white">
            <div className="container mx-auto px-4">
                <div className="flex flex-wrap justify-between items-center py-8 gap-4">
                    {FEATURES.map((feature, index) => (
                        <React.Fragment key={index}>
                            <div className="flex items-center gap-3 text-gray-700 font-semibold text-sm sm:text-base">
                                <feature.icon className="w-6 h-6 stroke-1" />
                                <span>{feature.text}</span>
                            </div>
                            {/* Divider (hide on last item and on small screens where wrapping occurs) */}
                            {index < FEATURES.length - 1 && (
                                <div className="hidden lg:block w-px h-8 bg-gray-200" />
                            )}
                        </React.Fragment>
                    ))}
                </div>
            </div>
        </section>
    );
}
