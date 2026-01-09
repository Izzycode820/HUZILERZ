/**
 * Landing Page - Clean Implementation
 * Modern landing page with a hero and interactive scroll section.
 * Organized component structure
 */

import React from 'react';
import { Hero, SolutionScroll } from '@/components/landing/sections';

export default function LandingPage() {
  return (
    <>
      <Hero />
      <SolutionScroll />
    </>
  );
}