"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { Search, Heart, ShoppingBag, Menu, X, User } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { usePathname } from "next/navigation";

const navLinks = [
    { href: "/", label: "Home" },
    { href: "/shop", label: "Shop" }, /* Combined Women/Men/Shop for simplicity or creating specific routes */
    { href: "/women", label: "Women's" },
    { href: "/men", label: "Men's" },
    {
        href: "#",
        label: "Pages",
        dropdown: [
            { href: "/product/1", label: "Product Details" },
            { href: "/cart", label: "Shop Cart" },
            { href: "/checkout", label: "Checkout" },
            { href: "/blog/1", label: "Blog Details" },
        ],
    },
    { href: "/blog", label: "Blog" },
    { href: "/contact", label: "Contact" },
];

export default function Navbar() {
    const [isOpen, setIsOpen] = useState(false);
    const [isScrolled, setIsScrolled] = useState(false);
    const pathname = usePathname();

    useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 50);
        };
        window.addEventListener("scroll", handleScroll);
        return () => window.removeEventListener("scroll", handleScroll);
    }, []);

    return (
        <>
            <header
                className={cn(
                    "fixed top-0 left-0 w-full z-50 transition-all duration-300 bg-white shadow-sm",
                    isScrolled ? "py-2" : "py-4"
                )}
            >
                <div className="container mx-auto px-4">
                    <div className="flex justify-between items-center">
                        {/* Logo */}
                        <Link href="/" className="flex items-center">
                            <img src="/img/logo.png" alt="Ashion" className="h-8 md:h-10" />
                        </Link>

                        {/* Desktop Menu */}
                        <nav className="hidden lg:flex items-center space-x-8">
                            {navLinks.map((link, index) => (
                                <div key={index} className="relative group">
                                    <Link
                                        href={link.href}
                                        className={cn(
                                            "text-sm font-semibold uppercase tracking-wider hover:text-primary transition-colors py-2 relative",
                                            pathname === link.href ? "text-primary border-b-2 border-primary" : "text-secondary"
                                        )}
                                    >
                                        {link.label}
                                    </Link>

                                    {link.dropdown && (
                                        <div className="absolute top-full left-0 w-48 bg-secondary text-white opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 transform translate-y-2 group-hover:translate-y-0 pt-2 pb-2">
                                            {link.dropdown.map((dropItem, i) => (
                                                <Link
                                                    key={i}
                                                    href={dropItem.href}
                                                    className="block px-4 py-2 text-sm hover:bg-gray-800 transition-colors"
                                                >
                                                    {dropItem.label}
                                                </Link>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </nav>

                        {/* Icons */}
                        <div className="flex items-center space-x-4 md:space-x-6">
                            <div className="hidden md:flex items-center text-xs text-gray-500 space-x-4 mr-4">
                                <Link href="/login" className="hover:text-primary transition-colors">Login</Link>
                                <Link href="/register" className="hover:text-primary transition-colors">Register</Link>
                            </div>

                            <button className="hover:text-primary transition-colors">
                                <Search size={20} />
                            </button>
                            <Link href="/wishlist" className="relative hover:text-primary transition-colors">
                                <Heart size={20} />
                                <span className="absolute -top-2 -right-2 bg-secondary text-white text-[10px] w-4 h-4 rounded-full flex items-center justify-center">2</span>
                            </Link>
                            <Link href="/cart" className="relative hover:text-primary transition-colors">
                                <ShoppingBag size={20} />
                                <span className="absolute -top-2 -right-2 bg-secondary text-white text-[10px] w-4 h-4 rounded-full flex items-center justify-center">2</span>
                            </Link>

                            <button
                                className="lg:hidden text-secondary"
                                onClick={() => setIsOpen(true)}
                            >
                                <Menu size={24} />
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Mobile Menu Offcanvas */}
            <AnimatePresence>
                {isOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setIsOpen(false)}
                            className="fixed inset-0 bg-black/50 z-50 lg:hidden"
                        />
                        <motion.div
                            initial={{ x: "-100%" }}
                            animate={{ x: 0 }}
                            exit={{ x: "-100%" }}
                            transition={{ type: "tween", duration: 0.3 }}
                            className="fixed top-0 left-0 h-full w-[80%] max-w-[300px] bg-white z-50 lg:hidden overflow-y-auto p-8"
                        >
                            <div className="flex justify-between items-center mb-8">
                                <img src="/img/logo.png" alt="Ashion" className="h-8" />
                                <button onClick={() => setIsOpen(false)} className="p-2 border border-gray-200 rounded-full hover:bg-primary hover:text-white transition-all">
                                    <X size={20} />
                                </button>
                            </div>

                            <div className="flex space-x-4 mb-8 text-sm text-gray-500">
                                <Link href="/login" onClick={() => setIsOpen(false)}>Login</Link>
                                <Link href="/register" onClick={() => setIsOpen(false)}>Register</Link>
                            </div>

                            <nav className="flex flex-col space-y-4">
                                {navLinks.map((link, index) => (
                                    <div key={index}>
                                        <Link
                                            href={link.href}
                                            onClick={() => !link.dropdown && setIsOpen(false)}
                                            className="block text-secondary font-medium uppercase hover:text-primary transition-colors"
                                        >
                                            {link.label}
                                        </Link>
                                        {link.dropdown && (
                                            <div className="pl-4 mt-2 space-y-2 border-l-2 border-gray-100">
                                                {link.dropdown.map((dropItem, i) => (
                                                    <Link
                                                        key={i}
                                                        href={dropItem.href}
                                                        onClick={() => setIsOpen(false)}
                                                        className="block text-sm text-gray-500 hover:text-primary"
                                                    >
                                                        {dropItem.label}
                                                    </Link>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </nav>

                            <div className="mt-8 flex space-x-4">
                                <div className="flex space-x-3 text-secondary">
                                    {/* Social Icons Placeholder */}
                                </div>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>

            {/* Spacer for fixed header */}
            <div className="h-[80px]" />
        </>
    );
}
