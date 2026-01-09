import React from "react";
import Link from "next/link";
import { Search, User, Heart, ShoppingBag, Menu } from "lucide-react";
import { cn } from "@/lib/utils";

export function Header() {
    return (
        <header className="bg-white sticky top-0 z-50 border-b border-gray-100">
            <div className="container mx-auto px-4 h-20 flex items-center justify-between gap-4">
                {/* Mobile Menu */}
                <button className="lg:hidden p-2">
                    <Menu className="w-6 h-6" />
                </button>

                {/* Navigation (Desktop) */}
                <nav className="hidden lg:flex items-center gap-8 text-sm font-semibold uppercase tracking-wide text-gray-700">
                    <div className="group relative cursor-pointer">
                        <span className="bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-full transition-colors flex items-center gap-1">
                            Home <span className="text-[10px] opacity-50">▼</span>
                        </span>
                    </div>
                    <Link href="#" className="hover:text-red-500 transition-colors flex items-center gap-1">
                        MerchFlow <span className="text-[10px] opacity-50">▼</span>
                    </Link>
                    <Link href="/catalog" className="hover:text-red-500 transition-colors flex items-center gap-1 font-bold text-[#EB4335]">
                        Catalog <span className="text-[10px] opacity-50">▼</span>
                    </Link>
                    <a href="#" className="hover:text-red-500 transition-colors flex items-center gap-1">
                        Blog <span className="text-[10px] opacity-50">▼</span>
                    </a>
                    <a href="#" className="hover:text-red-500 transition-colors flex items-center gap-1">
                        Pages <span className="text-[10px] opacity-50">▼</span>
                    </a>
                    <a href="#" className="hover:text-red-500 transition-colors">Contact</a>
                </nav>

                {/* Logo */}
                <div className="text-2xl font-bold tracking-wider font-serif absolute left-1/2 -translate-x-1/2 lg:static lg:transform-none lg:text-3xl">
                    MERCHFLOW
                </div>

                {/* Search & Actions */}
                <div className="flex items-center gap-4 md:gap-6">
                    <div className="hidden md:flex items-center bg-white border border-gray-200 rounded-full px-4 py-2 w-64 focus-within:border-gray-400 transition-colors">
                        <Search className="w-4 h-4 text-gray-400 mr-2" />
                        <input
                            type="text"
                            placeholder="What are you looking for?"
                            className="bg-transparent outline-none w-full text-sm placeholder:text-gray-400"
                        />
                    </div>

                    <div className="flex items-center gap-4 text-gray-700">
                        <button className="hover:text-red-500 transition-colors">
                            <User className="w-6 h-6" />
                        </button>
                        <button className="hidden sm:block hover:text-red-500 transition-colors relative">
                            <Heart className="w-6 h-6" />
                            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center">0</span>
                        </button>
                        <button className="hover:text-red-500 transition-colors relative">
                            <ShoppingBag className="w-6 h-6" />
                            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center">0</span>
                        </button>
                    </div>
                </div>
            </div>
        </header>
    );
}
