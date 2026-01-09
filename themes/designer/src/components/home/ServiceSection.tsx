"use client";

import { Truck, CircleDollarSign, Headset, ShieldCheck } from "lucide-react";

export default function ServiceSection() {
    const services = [
        { icon: Truck, title: "Free Shipping", desc: "For all oder over $99" },
        { icon: CircleDollarSign, title: "Money Back Guarantee", desc: "If good have Problems" },
        { icon: Headset, title: "Online Support 24/7", desc: "Dedicated support" },
        { icon: ShieldCheck, title: "Payment Secure", desc: "100% secure payment" },
    ];

    return (
        <section className="py-20">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                    {services.map((service, index) => (
                        <div key={index} className="flex items-start">
                            <service.icon size={36} className="text-primary mr-4 flex-shrink-0" />
                            <div>
                                <h6 className="font-semibold text-secondary mb-1">{service.title}</h6>
                                <p className="text-gray-500 text-sm">{service.desc}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
