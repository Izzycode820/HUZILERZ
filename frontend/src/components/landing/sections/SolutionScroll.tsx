"use client";

import { useScroll, useTransform, motion, MotionValue, useSpring, AnimatePresence } from "framer-motion";
import { useRef, useState, useEffect } from "react";
import { cn } from "@/lib/utils";

const MARQUEE_ROWS = [
  // ROW 1: Left -> Right
  [
    "Brand Owner", "Reseller", "Creative Director", "Agency Owner",
    "SaaS Founder", "Content Creator", "Brand Owner", "Reseller"
  ],
  // ROW 2: Right -> Left (Target: Dropshipping)
  [
    "Affiliate", "Middle Man", "DROPSHIPPING", "Consultant",
    "Influencer", "Affiliate", "Middle Man", "DROPSHIPPING"
  ],
  // ROW 3: Left -> Right
  [
    "Digital Artist", "Developer", "Course Creator", "Coach",
    "Freelancer", "Digital Artist", "Developer", "Course Creator"
  ]
];

const SWAP_TEXTS = ["become an entrepreneur", "start an online business", "become a brand"];

const SolutionScroll = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [textIndex, setTextIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setTextIndex((prev) => (prev + 1) % SWAP_TEXTS.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  // SMOOTH SCROLL
  const smoothProgress = useSpring(scrollYProgress, { stiffness: 100, damping: 20, restDelta: 0.001 });

  // --- ACT 1: THE TITLE LOCK (0 - 0.45) ---
  // Fade In: 0.0 -> 0.1
  // STAY VISIBLE: 0.1 -> 0.4 (The "Visual Rest")
  // Fade Out: 0.4 -> 0.45
  const titleOpacity = useTransform(smoothProgress, [0, 0.1, 0.4, 0.45], [0, 1, 1, 0]);
  const titleY = useTransform(smoothProgress, [0, 0.45], [20, 0]); // Subtle rise

  // --- GAP (0.45 - 0.5) --- 
  // Nothing visible here. Visual cleanser.

  // --- ACT 2: THE MARQUEE & VIDEO (0.5 - 1.0) ---
  // Fade In: 0.5 -> 0.55
  const marqueeOpacity = useTransform(smoothProgress, [0.5, 0.55, 0.9, 0.95], [0, 1, 1, 0]); // Fades out at 0.9 to reveal Static Lock

  // --- ACT 3: THE STATIC LOCK (0.9 - 1.0) ---
  // This layer sits EXACTLY where the marquee would be, but is static and centered.
  const staticLockOpacity = useTransform(smoothProgress, [0.9, 0.95], [0, 1]);
  const highlightScale = useTransform(smoothProgress, [0.9, 0.95], [1, 1.2]);
  const highlightColor = useTransform(smoothProgress, [0.9, 0.95], ["#ffffff", "#D4FF00"]);

  return (
    <section ref={containerRef} className="relative h-[500vh] bg-huzilerz-black overflow-clip">
      {/* Increased height to 500vh to give more scroll room for the gap */}

      {/* STICKY VIEWPORT */}
      <div className="sticky top-0 h-screen w-full overflow-hidden flex flex-col items-center justify-center">

        {/* BACKGROUND VIDEO (Only visible in Act 2) */}
        <IdentityMontage progress={smoothProgress} />

        {/* ACT 1: TITLE (Left Aligned, Thin) */}
        <motion.div
          style={{ opacity: titleOpacity, y: titleY }}
          className="absolute inset-0 flex items-center z-20 pointer-events-none container mx-auto px-6 md:px-20"
        >
          <div className="flex flex-col items-start justify-center space-y-12">

            {/* 1. How to */}
            <h2 className="text-4xl md:text-6xl lg:text-8xl font-thin tracking-tight text-white/90">
              How to
            </h2>

            {/* 2. Switcher (Italic, Smaller) */}
            <div className="h-[1.5em] overflow-visible flex items-center ml-2 md:ml-4">
              <AnimatePresence mode="wait">
                <motion.span
                  key={SWAP_TEXTS[textIndex]}
                  initial={{ y: 20, opacity: 0, filter: "blur(5px)" }}
                  animate={{ y: 0, opacity: 1, filter: "blur(0px)" }}
                  exit={{ y: -20, opacity: 0, filter: "blur(5px)" }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                  className="text-3xl md:text-5xl lg:text-7xl font-thin italic tracking-wide text-gray-300 whitespace-nowrap"
                >
                  {SWAP_TEXTS[textIndex]}
                </motion.span>
              </AnimatePresence>
            </div>

            {/* 3. Today */}
            <h2 className="text-4xl md:text-6xl lg:text-8xl font-thin tracking-tight text-white/90">
              today.
            </h2>
          </div>
        </motion.div>

        {/* ACT 2: AUTO-PLAY MARQUEE (Moves continuously) */}
        <motion.div
          style={{ opacity: marqueeOpacity }}
          className="absolute inset-0 z-30 flex flex-col justify-center gap-8 md:gap-16 pointer-events-none"
        >
          <AutoMarqueeRow direction="left" text={MARQUEE_ROWS[0]} speed={20} />
          <AutoMarqueeRow direction="right" text={MARQUEE_ROWS[1]} speed={25} /> {/* The Middle Row */}
          <AutoMarqueeRow direction="left" text={MARQUEE_ROWS[2]} speed={20} />
        </motion.div>

        {/* ACT 3: STATIC LOCK (The "Stop" State) */}
        {/* Only visible at the end. Contains the highlighted "Dropshipping" centered. */}
        <motion.div
          style={{ opacity: staticLockOpacity }}
          className="absolute inset-0 z-40 flex flex-col justify-center gap-8 md:gap-16 pointer-events-none"
        >
          {/* Row 1 (Static Faded) */}
          <div className="w-full flex justify-center opacity-10 blur-sm">
            <span className="text-6xl md:text-8xl font-bold text-gray-500 uppercase tracking-tight">BRAND OWNER</span>
          </div>

          {/* Row 2 (Detailed Highlight) */}
          <div className="w-full flex justify-center items-center scale-110">
            <motion.span
              style={{ scale: highlightScale, color: highlightColor, textShadow: "0 0 50px rgba(212,255,0,0.5)" }}
              className="text-6xl md:text-9xl font-black uppercase tracking-tight z-50"
            >
              DROPSHIPPING
            </motion.span>
          </div>

          {/* Row 3 (Static Faded) */}
          <div className="w-full flex justify-center opacity-10 blur-sm">
            <span className="text-6xl md:text-8xl font-bold text-gray-500 uppercase tracking-tight">DEVELOPER</span>
          </div>
        </motion.div>

      </div>

    </section>
  );
};

// --- SUBCOMPONENTS ---

const AutoMarqueeRow = ({ text, direction, speed }: { text: string[], direction: "left" | "right", speed: number }) => {
  return (
    <div className="relative flex w-full overflow-hidden whitespace-nowrap mask-linear-fade">
      <motion.div
        className="flex gap-12 md:gap-24 min-w-full"
        animate={{ x: direction === "left" ? "-50%" : "50%" }}
        initial={{ x: "0%" }}
        transition={{ repeat: Infinity, ease: "linear", duration: speed }}
      >
        {/* Double the array to create seamless loop */}
        {[...text, ...text, ...text].map((item, i) => (
          <span
            key={i}
            className="text-6xl md:text-8xl font-bold text-gray-700/50 uppercase tracking-tight shrink-0"
          >
            {item}
          </span>
        ))}
      </motion.div>
    </div>
  )
}

// Simulated High-Speed Montage Video Background
const IdentityMontage = ({ progress }: { progress: MotionValue<number> }) => {
  // Reveal background at 0.5 (Act 2 start)
  const opacity = useTransform(progress, [0.5, 0.55], [0, 1]);

  // Simulate Video Flash Effect (this would ideally be a real video)
  return (
    <motion.div
      style={{ opacity }}
      className="absolute inset-0 z-0 bg-[#050505]"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-gray-900/40 via-[#050505] to-[#050505]" />

      {/* Grid of "Flashing" Images representing choices */}
      <div className="w-full h-full opacity-20 grid grid-cols-4 grid-rows-4 gap-4 p-4 transform scale-110">
        {Array.from({ length: 16 }).map((_, i) => (
          <MontageCell key={i} index={i} />
        ))}
      </div>

      <div className="absolute inset-0 bg-gradient-to-t from-[#050505] via-transparent to-[#050505]" />
      <div className="absolute inset-0 bg-gradient-to-r from-[#050505] via-transparent to-[#050505]" />
    </motion.div>
  )
}

const MontageCell = ({ index }: { index: number }) => {
  // In a real app, these would be frantic video clips or changing images
  return (
    <div className={cn(
      "w-full h-full rounded-lg bg-gray-800/20 border border-white/5",
      index % 2 === 0 ? "animate-pulse" : "opacity-50"
    )}></div>
  )
}

export default SolutionScroll;
