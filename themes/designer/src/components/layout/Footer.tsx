"use client";

import Link from "next/link";
import { Facebook, Twitter, Youtube, Instagram, Linkedin, Heart } from "lucide-react";

export default function Footer() {
    return (
        <footer className="bg-secondary text-white pt-16 pb-8">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-12">
                    {/* About */}
                    <div>
                        <Link href="/" className="mb-6 block">
                            {/* Logo usually white version in footer, applying filter or using text if image not available */}
                            <img src="/img/logo.png" alt="Ashion" className="h-8 brightness-0 invert" />
                        </Link>
                        <p className="text-gray-400 text-sm leading-relaxed mb-6">
                            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt cilisis.
                        </p>
                        <div className="flex gap-2">
                            {[1, 2, 3, 4, 5].map((i) => (
                                <div key={i} className="bg-white p-1 rounded-sm w-10 h-6 relative">
                                    {/* Payment icons placeholder - using img/payment/payment-x.png */}
                                    <img src={`/img/payment/payment-${i}.png`} alt="Payment" className="w-full h-full object-contain" />
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h6 className="text-white font-bold uppercase mb-6 font-montserrat">Quick Links</h6>
                        <ul className="space-y-3 text-sm text-gray-400">
                            {["About", "Blogs", "Contact", "FAQ"].map((item) => (
                                <li key={item}>
                                    <Link href="#" className="hover:text-primary transition-colors">{item}</Link>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Account */}
                    <div>
                        <h6 className="text-white font-bold uppercase mb-6 font-montserrat">Account</h6>
                        <ul className="space-y-3 text-sm text-gray-400">
                            {["My Account", "Orders Tracking", "Checkout", "Wishlist"].map((item) => (
                                <li key={item}>
                                    <Link href="#" className="hover:text-primary transition-colors">{item}</Link>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Newsletter */}
                    <div>
                        <h6 className="text-white font-bold uppercase mb-6 font-montserrat">Newsletter</h6>
                        <form className="relative mb-6">
                            <input
                                type="email"
                                placeholder="Email"
                                className="w-full bg-transparent border border-gray-600 rounded-full py-3 px-5 text-white placeholder-gray-500 focus:border-primary focus:outline-none transition-colors"
                            />
                            <button type="submit" className="absolute right-0 top-0 h-full px-6 bg-primary text-white rounded-r-full font-bold uppercase text-xs hover:bg-white hover:text-primary transition-all">
                                Subscribe
                            </button>
                        </form>
                        <div className="flex space-x-4">
                            {[Facebook, Twitter, Youtube, Instagram, Linkedin].map((Icon, i) => (
                                <a key={i} href="#" className="w-10 h-10 bg-[#333] rounded-full flex items-center justify-center hover:bg-primary transition-colors">
                                    <Icon size={16} />
                                </a>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="border-t border-gray-800 pt-6 mt-8 text-center text-sm text-gray-500">
                    <p>
                        Copyright &copy; {new Date().getFullYear()} All rights reserved | This template is made with
                        <Heart size={14} className="inline mx-1 text-primary fill-primary" />
                        by <a href="https://colorlib.com" target="_blank" className="text-primary hover:underline">Colorlib</a>
                    </p>
                </div>
            </div>
        </footer>
    );
}
