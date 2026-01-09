import { Category } from "./types";

export const CATEGORIES: Category[] = [
    // --- CLOTHING & APPAREL ---
    { id: "clothing", label: "Clothing & Apparel", image: "clothing-main.jpg" },
    { id: "clothing-tops", label: "Tops", parentId: "clothing", description: "T-Shirts, Polos, Tank Tops, Crop Tops" },
    { id: "clothing-warm", label: "Warm Wear", parentId: "clothing", description: "Hoodies, Sweatshirts, Jackets, Vests" },
    { id: "clothing-bottoms", label: "Bottoms", parentId: "clothing", description: "Leggings, Joggers, Sweatpants, Shorts, Skirts" },
    { id: "clothing-headwear", label: "Headwear", parentId: "clothing", description: "Caps, Beanies, Hats, Visors" },
    { id: "clothing-footwear", label: "Footwear", parentId: "clothing", description: "Shoes, Slides, Flip Flops, Socks" },
    { id: "clothing-kids", label: "Kids & Baby", parentId: "clothing", description: "Onesies, Tees, Bibs" },

    // --- ELECTRONICS & TECH ---
    { id: "electronics", label: "Electronics & Tech", image: "tech-main.jpg" },
    { id: "electronics-phone", label: "Phone Cases", parentId: "electronics", description: "iPhone, Samsung, Tough, Slim" },
    { id: "electronics-computer", label: "Computer", parentId: "electronics", description: "Laptop Sleeves, Skins, Mouse Pads" },
    { id: "electronics-audio", label: "Audio", parentId: "electronics", description: "AirPod Cases, Headphone Stands" },
    { id: "electronics-wearables", label: "Wearables", parentId: "electronics", description: "Apple Watch Bands" },

    // --- HOME & LIVING ---
    { id: "home", label: "Home & Living", image: "home-main.jpg" },
    { id: "home-drinkware", label: "Drinkware", parentId: "home", description: "Mugs, Tumblers, Bottles" },
    { id: "home-bedding", label: "Bedding", parentId: "home", description: "Pillows, Blankets, Duvets" },
    { id: "home-bathroom", label: "Bathroom", parentId: "home", description: "Curtains, Towels, Mats" },
    { id: "home-kitchen", label: "Kitchen", parentId: "home", description: "Aprons, Mitts, Magnets" },
    { id: "home-decor", label: "Decor", parentId: "home", description: "Clocks, Ornaments, Candles" },

    // --- WALL ART ---
    { id: "wall-art", label: "Wall Art", image: "art-main.jpg" },
    { id: "wall-art-prints", label: "Prints", parentId: "wall-art", description: "Canvas, Posters, Metal, Wood" },
    { id: "wall-art-textiles", label: "Textiles", parentId: "wall-art", description: "Tapestries, Flags" },

    // --- ACCESSORIES ---
    { id: "accessories", label: "Accessories", image: "accessories-main.jpg" },
    { id: "accessories-bags", label: "Bags", parentId: "accessories", description: "Totes, Backpacks, Duffles" },
    { id: "accessories-travel", label: "Travel", parentId: "accessories", description: "Tags, Passport Covers" },
    { id: "accessories-small", label: "Small Goods", parentId: "accessories", description: "Keychains, Pins, Mirrors" },
    { id: "accessories-masks", label: "Masks", parentId: "accessories", description: "Face Masks, Bandanas" },

    // --- STATIONERY ---
    { id: "stationery", label: "Stationery", image: "stationery-main.jpg" },
    { id: "stationery-paper", label: "Paper", parentId: "stationery", description: "Notebooks, Journals" },
    { id: "stationery-mailing", label: "Mailing", parentId: "stationery", description: "Stickers, Cards" },
    { id: "stationery-office", label: "Office", parentId: "stationery", description: "Clipboards, Folders" },

    // --- PETS ---
    { id: "pets", label: "Pet Products", image: "pets-main.jpg", description: "Bandanas, Beds, Bowls, Collars" },
];

export function getSubcategories(parentId: string) {
    return CATEGORIES.filter(c => c.parentId === parentId);
}

export function getRootCategories() {
    return CATEGORIES.filter(c => !c.parentId);
}

export function getCategory(id: string) {
    return CATEGORIES.find(c => c.id === id);
}
