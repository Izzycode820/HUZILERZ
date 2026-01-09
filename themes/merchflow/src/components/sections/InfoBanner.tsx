import React from "react";
import { Phone, MapPin, Gift, Truck, ChevronDown, Globe } from "lucide-react";
import { cn } from "@/lib/utils";

interface InfoBannerProps {
    className?: string;
}

export function InfoBanner({ className }: InfoBannerProps) {
    return (
        <div className={cn("w-full bg-[#FA4D56] text-white text-[13px] font-medium py-2.5", className)}>
            <div className="container mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-2">
                {/* Left Section: Contact & Address */}
                <div className="flex items-center gap-6 hidden lg:flex">
                    <div className="flex items-center gap-2 cursor-pointer hover:text-white/90 transition-colors">
                        <Phone className="w-4 h-4" />
                        <span>Call Us: +1 800-123 456</span>
                    </div>
                    <div className="flex items-center gap-2 cursor-pointer hover:text-white/90 transition-colors">
                        <MapPin className="w-4 h-4" />
                        <span>2972 Westheimer Rd. Santa Ana</span>
                    </div>
                </div>

                {/* Center Section: Promotions */}
                <div className="flex items-center justify-center gap-2 text-center flex-1">
                    <Gift className="w-4 h-4 animate-pulse hidden sm:block" />
                    <span className="whitespace-nowrap">
                        Buy 3 Get 15% Off! Use code: <span className="font-bold">SALE15</span>
                        <span className="mx-2 opacity-50">|</span>
                        Buy 5 Get 20% Off! Use code: <span className="font-bold">SALE20</span>
                    </span>
                </div>

                {/* Right Section: Util Links */}
                <div className="flex items-center gap-6 hidden md:flex">
                    <a href="#" className="flex items-center gap-2 hover:text-white/90 transition-colors">
                        <Truck className="w-4 h-4" />
                        <span>Track Order</span>
                    </a>
                    <div className="flex items-center gap-4">
                        <button className="flex items-center gap-1 hover:text-white/90 transition-colors">
                            <Globe className="w-4 h-4" />
                            <span>English</span>
                            <ChevronDown className="w-3 h-3 opacity-75" />
                        </button>
                        <button className="flex items-center gap-1 hover:text-white/90 transition-colors">
                            <span>USD</span>
                            <ChevronDown className="w-3 h-3 opacity-75" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
