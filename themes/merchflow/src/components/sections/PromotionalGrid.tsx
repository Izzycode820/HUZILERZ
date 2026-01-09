import React from "react";
import { ArrowUpRight, ArrowRight, Check } from "lucide-react";
import { cn } from "@/lib/utils";

export function PromotionalGrid() {
    return (
        <section className="py-20 bg-white">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 auto-rows-[300px]">
                    {/* Card 1: Promotional Products (Large Green) */}
                    <div className="lg:col-span-1 bg-[#4ADE80] rounded-3xl p-8 relative overflow-hidden group">
                        <div className="relative z-10 h-full flex flex-col justify-between">
                            <div>
                                <h3 className="text-white font-bold text-sm uppercase tracking-wider mb-2">Promotional Products</h3>
                                <div className="text-5xl font-bold text-white mb-2">SAVE 25%</div>
                                <p className="text-white/90">At prices for every budget.</p>
                            </div>
                            <button className="bg-white text-[#4ADE80] px-6 py-2 rounded-full font-bold w-fit flex items-center gap-2 hover:bg-gray-100 transition-colors">
                                Shop Now <ArrowUpRight className="w-4 h-4 ml-1" />
                            </button>
                        </div>
                        {/* Decorative Image Placeholder */}
                        <div className="absolute top-1/2 right-[-20px] w-48 h-48 bg-emerald-600/30 rounded-full blur-2xl group-hover:scale-110 transition-transform" />
                    </div>

                    {/* Card 2: Anniversary (Purple) with Badge */}
                    <div className="bg-[#8B5CF6] rounded-3xl p-8 relative overflow-hidden md:col-span-1">
                        <div className="text-center relative z-10">
                            <h3 className="text-2xl font-bold text-white mb-2">ANNIVERSARY GIFTS</h3>
                            <p className="text-white/80 text-sm">Your better half deserves the very best.</p>
                        </div>
                        {/* Sale Badge */}
                        <div className="absolute bottom-4 right-4 bg-[#EC4899] text-white p-4 rounded-full font-bold text-center rotate-12 shadow-lg animate-pulse">
                            <span className="block text-xs">SALE</span>
                            <span className="text-xl">30%</span>
                        </div>
                    </div>

                    {/* Card 3: Personalized Gifts (Green/Brown) */}
                    <div className="bg-[#86EFAC] rounded-3xl p-6 flex flex-col justify-end relative overflow-hidden group">
                        <img
                            src="https://placehold.co/400x300/F0FDF4/000000/png?text=Gifts"
                            alt="Personalized Gifts"
                            className="absolute inset-0 w-full h-full object-cover opacity-50 group-hover:opacity-60 transition-opacity"
                        />
                        <div className="relative z-10 bg-[#4ADE80] p-4 rounded-xl">
                            {/* Red Tag */}
                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-[#EF4444] text-white px-3 py-1 rounded-full text-xs font-bold transform -rotate-2">
                                SALE 25% OFF
                            </div>
                            <h3 className="text-xl font-bold text-white text-center mt-2">PERSONALIZED GIFTS</h3>
                            <p className="text-white/90 text-center text-sm">We picked gifts for all your people</p>
                        </div>
                    </div>

                    {/* Card 4: 50% Off (Orange) */}
                    <div className="bg-[#F97316] rounded-3xl p-8 relative overflow-hidden group flex items-center">
                        <div className="relative z-10 w-full text-center">
                            <h3 className="text-5xl font-bold text-white mb-2">50% OFF</h3>
                            <p className="text-white font-bold tracking-widest uppercase">Almost Everything</p>
                        </div>
                        {/* Lemon Decorations */}
                        <div className="absolute top-4 left-4 w-16 h-16 bg-yellow-400 rounded-full opacity-80 mix-blend-overlay" />
                        <div className="absolute bottom-4 right-4 w-20 h-20 bg-yellow-400 rounded-full opacity-80 mix-blend-overlay" />
                    </div>

                    {/* Card 5: Wedding Invites (Pink) */}
                    <div className="bg-[#EC4899] rounded-3xl p-8 relative overflow-hidden md:col-span-1 group">
                        <div className="relative z-10">
                            <h3 className="text-3xl font-bold text-white leading-tight">
                                WEDDING INVITES FOR <br /> UNDER $50
                            </h3>
                            <button className="mt-4 bg-black text-white px-4 py-2 rounded-full text-xs font-bold uppercase hover:scale-105 transition-transform">
                                % OFF ALL ITEMS
                            </button>
                        </div>
                    </div>

                    {/* Card 6: We Take Care Of (Blue) */}
                    <div className="bg-[#60A5FA] rounded-3xl p-8 relative overflow-hidden flex flex-col justify-center">
                        <h3 className="text-3xl font-bold text-white mb-6">
                            WE TAKE CARE OF:
                        </h3>
                        <ul className="space-y-3 text-white font-medium mb-8">
                            <li className="flex items-center gap-2">
                                <div className="w-1 h-1 bg-white rounded-full" /> Quality control
                            </li>
                            <li className="flex items-center gap-2">
                                <div className="w-1 h-1 bg-white rounded-full" /> Order fulfillment
                            </li>
                            <li className="flex items-center gap-2">
                                <div className="w-1 h-1 bg-white rounded-full" /> Printing tech
                            </li>
                        </ul>
                        <button className="bg-white text-[#60A5FA] px-6 py-2 rounded-full font-bold w-fit flex items-center gap-2 hover:bg-gray-100 transition-colors">
                            Shop Now <ArrowUpRight className="w-4 h-4 ml-1" />
                        </button>

                        {/* Illustration Placeholder */}
                        <div className="absolute bottom-0 right-0 w-32 h-32 bg-blue-400 rounded-tl-3xl opacity-50" />
                    </div>

                </div>
            </div>
        </section>
    );
}
