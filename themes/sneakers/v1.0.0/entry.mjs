/**
 * Sneakers Theme Entry Point - Manifest Method
 *
 * PURPOSE: Export React components ONLY
 * - puck_config comes from DATABASE (loaded by backend)
 * - puck_data comes from DATABASE (user's customized copy)
 * - This file provides the actual React UI components
 *
 * Flow:
 * 1. Backend loads puck_config + puck_data from DB
 * 2. Frontend imports this entry.mjs for React components
 * 3. Puck matches components from config with React components from here
 */

// Import all theme sections/components
import HeroSection from "./src/components/sections/HeroSection/HeroSection.tsx";
import CategoriesSection from "./src/components/sections/CategoriesSection/CategoriesSection.tsx";
import CollectionSection_A from "./src/components/sections/CollectionSection_A/CollectionSection_A.tsx";
import CollectionSection_B from "./src/components/sections/CollectionSection_B/CollectionSection_B.tsx";
import ValuesSection from "./src/components/sections/ValuesSection/ValuesSection.tsx";
import OurGoalsSection from "./src/components/sections/OurGoalsSection/OurGoalsSection.tsx";
import SaleBannerSection from "./src/components/sections/SaleBannerSection/SaleBannerSection.tsx";

/**
 * Theme Export - Components ONLY
 */
export default {
  name: "Sneakers",
  version: "1.0.0",

  // React components for Puck to render
  components: {
    HeroSection,
    CategoriesSection,
    CollectionSection_A,
    CollectionSection_B,
    ValuesSection,
    OurGoalsSection,
    SaleBannerSection,
  }
};
