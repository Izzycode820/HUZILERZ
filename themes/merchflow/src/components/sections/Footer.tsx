"use client";

import React from "react";
import { ArrowUpRight, ArrowUp } from "lucide-react";

export function Footer() {
    return (
        <footer className="bg-[#1c1c1c] text-white pt-20">
            <div className="container mx-auto px-4 pb-12">
                <div className="flex flex-col lg:flex-row gap-12 justify-between">
                    {/* Brand & Newsletter */}
                    <div className="lg:w-1/3 space-y-8">
                        <h1 className="text-5xl font-serif tracking-tighter">MERCHFLOW</h1>
                        <div className="relative max-w-sm border-b border-gray-700 pb-2">
                            <input
                                type="email"
                                placeholder="Enter your email..."
                                className="w-full bg-transparent outline-none placeholder:text-gray-500 text-white pr-20"
                            />
                            <button className="absolute right-0 top-0 text-sm font-bold flex items-center gap-1 hover:text-gray-300 transition-colors">
                                Subscribe <ArrowUpRight className="w-4 h-4" />
                            </button>
                        </div>
                        <p className="text-gray-500 text-xs">
                            © 2024 <span className="text-white font-bold">MerchFlow.</span> All Rights Reserved
                        </p>
                    </div>

                    {/* Links Columns */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8 lg:w-2/3">
                        <div>
                            <h4 className="font-bold text-xs uppercase tracking-widest mb-6 text-gray-400">Information</h4>
                            <ul className="space-y-4 text-sm text-gray-300">
                                <li className="hover:text-white cursor-pointer transition-colors">Help Center</li>
                                <li className="hover:text-white cursor-pointer transition-colors">Shipping</li>
                                <li className="hover:text-white cursor-pointer transition-colors">Returns</li>
                                <li className="hover:text-white cursor-pointer transition-colors">Policies</li>
                                <li className="hover:text-white cursor-pointer transition-colors">Gift Cards</li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-bold text-xs uppercase tracking-widest mb-6 text-gray-400">Useful Links</h4>
                            <ul className="space-y-4 text-sm text-gray-300">
                                <li className="hover:text-white cursor-pointer transition-colors">My Account</li>
                                <li className="hover:text-white cursor-pointer transition-colors">Order Tracking</li>
                                <li className="hover:text-white cursor-pointer transition-colors">All Products</li>
                                <li className="hover:text-white cursor-pointer transition-colors">All Services</li>
                                <li className="hover:text-white cursor-pointer transition-colors">Service Detail</li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-bold text-xs uppercase tracking-widest mb-6 text-gray-400">About Us</h4>
                            <ul className="space-y-4 text-sm text-gray-300">
                                <li className="hover:text-white cursor-pointer transition-colors">Our story</li>
                                <li className="hover:text-white cursor-pointer transition-colors">Contacts</li>
                                <li className="hover:text-white cursor-pointer transition-colors">Affiliate Program</li>
                                <li className="hover:text-white cursor-pointer transition-colors">Referral Program</li>
                                <li className="hover:text-white cursor-pointer transition-colors">Careers</li>
                            </ul>
                        </div>
                        <div className="relative">
                            <h4 className="font-bold text-xs uppercase tracking-widest mb-6 text-gray-400">Our Category</h4>
                            <ul className="space-y-4 text-sm text-gray-300">
                                <li className="hover:text-white cursor-pointer transition-colors">Jewelry</li>
                                <li className="hover:text-white cursor-pointer transition-colors">Clothing & bags</li>
                                <li className="hover:text-white cursor-pointer transition-colors">Packaging</li>
                                <li className="hover:text-white cursor-pointer transition-colors">Home & living</li>
                                <li className="hover:text-white cursor-pointer transition-colors">Business cards</li>
                            </ul>

                            {/* Scroll to Top Button (Hidden on mobile, layout adjustment) */}
                            <button
                                onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                                className="absolute -bottom-0 right-0 lg:right-[-20px] bg-white text-black w-10 h-10 rounded-full flex items-center justify-center hover:bg-gray-200 transition-colors"
                            >
                                <ArrowUp className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Bottom Social Bar */}
            <div className="border-t border-gray-800">
                <div className="container mx-auto">
                    <div className="grid grid-cols-2 md:grid-cols-5 divide-x divide-gray-800 border-x border-gray-800 text-center">
                        {["FACEBOOK", "INSTAGRAM", "TWITTER", "TIKTOK", "PINTEREST"].map((social) => (
                            <a
                                key={social}
                                href="#"
                                className="py-6 text-xs font-bold tracking-widest text-gray-400 hover:text-white hover:bg-[#252525] transition-all block md:border-b-0 border-b last:border-b-0 border-gray-800"
                            >
                                {social}
                            </a>
                        ))}
                    </div>
                </div>
            </div>
        </footer>
    );
}
