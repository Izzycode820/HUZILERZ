import { ReactNode } from "react";

// Button component types
export interface ButtonProps {
  children: ReactNode;
  size?: "small" | "medium" | "large" | "extraLarge";
  variant?: "primary" | "secondary";
  iconEnd?: boolean;
  onClick?: () => void;
  className?: string;
}

// Rating component types
export type RatingValue = "one" | "two" | "three" | "threeHalf" | "four" | "fourHalf" | "five";

export interface RatingProps {
  rating: RatingValue;
}

// ProductCard component types
export interface ProductCardProps {
  image: string;
  title?: string;
  description?: string;
  price?: string;
  rating?: RatingValue;
  size?: "default" | "small";
}

// Value component types
export interface ValueProps {
  icon: ReactNode;
  title: string;
  description: string;
}

// Product data types
export interface Product {
  id: string;
  image: string;
  title: string;
  description: string;
  price: number;
  rating: RatingValue;
  category: string;
  featured?: boolean;
  onSale?: boolean;
}

// Category types
export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
}

// Navigation types
export interface NavItem {
  label: string;
  href: string;
  children?: NavItem[];
}

// Footer types
export interface FooterSection {
  title: string;
  links: FooterLink[];
}

export interface FooterLink {
  label: string;
  href: string;
}

// Theme configuration types
export interface ThemeConfig {
  name: string;
  version: string;
  description: string;
  author: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    text: string;
  };
  fonts: {
    primary: string;
    secondary: string;
  };
}