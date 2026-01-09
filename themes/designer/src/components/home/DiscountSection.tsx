"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const CountdownItem = ({ value, label }: { value: number; label: string }) => (
    <div className="flex flex-col items-center mr-8 last:mr-0 min-w-[60px]">
        <span className="text-3xl font-semibold text-secondary">{value.toString().padStart(2, '0')}</span>
        <span className="text-sm font-medium text-secondary">{label}</span>
    </div>
);

export default function DiscountSection() {
    const [timeLeft, setTimeLeft] = useState({ days: 22, hours: 18, minutes: 46, seconds: 5 });

    useEffect(() => {
        const timer = setInterval(() => {
            setTimeLeft(prev => {
                if (prev.seconds > 0) return { ...prev, seconds: prev.seconds - 1 };
                if (prev.minutes > 0) return { ...prev, minutes: prev.minutes - 1, seconds: 59 };
                if (prev.hours > 0) return { ...prev, hours: prev.hours - 1, minutes: 59, seconds: 59 };
                if (prev.days > 0) return { ...prev, days: prev.days - 1, hours: 23, minutes: 59, seconds: 59 };
                return prev;
            });
        }, 1000);
        return () => clearInterval(timer);
    }, []);

    return (
        <section className="py-20">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-0">
                    <div className="h-[400px] lg:h-auto order-2 lg:order-1 relative">
                        <img src="/img/discount.jpg" alt="Discount" className="w-full h-full object-cover" />
                        {/* Large circle cut out effect simulated with absolute div if needed, but simplicity first */}
                    </div>
                    <div className="bg-[#f4f4f4] p-[50px] lg:p-[75px] text-center flex flex-col items-center justify-center order-1 lg:order-2">
                        <div className="relative mb-8">
                            <div className="w-[150px] h-[150px] bg-white rounded-full absolute -top-[50px] left-1/2 -translate-x-1/2 -z-10 hidden sm:block"></div>
                            <span className="text-xs font-medium uppercase text-secondary tracking-widest block mb-2">Discount</span>
                            <h2 className="text-5xl md:text-6xl font-cookie text-primary mb-2">Summer 2025</h2>
                            <h5 className="font-bold text-primary text-lg">
                                <span className="text-secondary text-sm font-normal mr-1">Sale</span> 50%
                            </h5>
                        </div>

                        <div className="flex justify-center mb-8">
                            <CountdownItem value={timeLeft.days} label="Days" />
                            <CountdownItem value={timeLeft.hours} label="Hour" />
                            <CountdownItem value={timeLeft.minutes} label="Min" />
                            <CountdownItem value={timeLeft.seconds} label="Sec" />
                        </div>

                        <Link
                            href="/shop"
                            className="inline-block uppercase font-bold text-sm text-secondary border-b-2 border-primary pb-1 hover:text-primary transition-colors"
                        >
                            Shop now
                        </Link>
                    </div>
                </div>
            </div>
        </section>
    );
}
