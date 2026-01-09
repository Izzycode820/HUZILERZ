"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import { Play } from "lucide-react";
import { Header } from "../common"; // Import the refactored Header

const ROLES = ["Entrepreneurs", "Solopreneurs", "Hustlers"];

export default function Hero() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setIndex((prev) => (prev + 1) % ROLES.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="relative h-screen w-full bg-huzilerz-black">
      {/* 1. VIDEO BACKGROUND & OVERLAY */}
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 bg-black/60 z-10" />
        <video
          key="/landing/cat.mp4" // Add key to force re-render on src change
          autoPlay
          loop
          muted
          playsInline
          className="h-full w-full object-cover"
          src="/landing/cat.mp4"
        />
      </div>
      
      {/* 2. FLOATING HEADER */}
      <Header />

      {/* 3. CONTENT CONTAINER (Left Aligned) */}
      <div className="relative z-20 flex h-full flex-col justify-center px-6 md:px-12 max-w-7xl mx-auto">
        <div className="max-w-4xl space-y-8">
          {/* MAIN HEADLINE */}
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-semibold leading-[1.1] text-white tracking-tight text-left">
            Huzilerz Camp <br /> for all{" "}
            <span className="block text-huzilerz-lime md:inline">
              <AnimatePresence mode="wait">
                <motion.span
                  key={ROLES[index]}
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  exit={{ y: -20, opacity: 0 }}
                  transition={{ duration: 0.5, ease: "circOut" }}
                  className="inline-block"
                >
                  {ROLES[index]}
                </motion.span>
              </AnimatePresence>
            </span>
          </h1>

          {/* SLOGAN */}
          <motion.p
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.8 }}
            className="text-xl md:text-2xl text-gray-200 font-light max-w-2xl text-left"
          >
            No hustle is too small to be called a brand.
          </motion.p>

          {/* SHARP-CORNER BUTTONS */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="flex flex-col sm:flex-row gap-4 pt-4 items-start"
          >
            {/* Primary Button */}
            <button className="h-14 px-8 bg-white text-black font-bold text-lg rounded-none hover:bg-huzilerz-lime transition-all duration-300">
              Start Your Empire
            </button>
            
            {/* Secondary Button */}
            <button className="h-14 px-8 flex items-center gap-3 border border-white/30 text-white font-medium text-lg rounded-none hover:bg-white/10 transition-all backdrop-blur-sm">
              <Play size={20} fill="currentColor" />
              Watch the Vision
            </button>
          </motion.div>
        </div>
      </div>
    </section>
  );
}