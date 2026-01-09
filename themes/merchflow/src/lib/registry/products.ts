import { CatalogProduct } from "./types";

export const CATALOG: CatalogProduct[] = [
    // --- CLOTHING: TOPS ---
    {
        id: "classic-tee",
        categoryId: "clothing-tops",
        name: "Unisex Heavy Cotton Tee",
        brand: "Gildan 5000",
        description: "The unisex heavy cotton tee is the basic staple of any wardrobe. It is the foundation upon which casual fashion grows. No side seams mean there are no itchy interruptions under the arms. The shoulders have tape for improved durability.",
        basePrice: 12.35,
        premiumPrice: 9.85,
        rating: 4.8,
        reviewCount: 1240,
        isBestSeller: true,
        colors: [
            { name: "White", hex: "#FFFFFF" },
            { name: "Black", hex: "#111111" },
            { name: "Navy", hex: "#1E3A8A" },
            { name: "Red", hex: "#EF4444" },
            { name: "Sport Grey", hex: "#9CA3AF" }
        ],
        sizes: [
            { label: "S", dims: { width: "18in", length: "28in" } },
            { label: "M", dims: { width: "20in", length: "29in" } },
            { label: "L", dims: { width: "22in", length: "30in" } },
            { label: "XL", dims: { width: "24in", length: "31in" } },
            { label: "2XL", dims: { width: "26in", length: "32in" } },
        ],
        features: [
            { icon: "ShieldCheck", title: "100% Cotton", description: "Made from specially spun fibers that make very strong and smooth fabric, perfect for printing." },
            { icon: "Minimize2", title: "Without side seams", description: "Knitted in one piece using tubular knit, it reduces fabric waste and makes garment more attractive." },
            { icon: "Maximize2", title: "Ribbed knit collar", description: "Ribbed knit makes collar highly elastic and helps retain its shape." },
            { icon: "Layers", title: "Shoulder tape", description: "Twill tape covers the shoulder seams to stabilize the back of the shirt and to prevent stretching." }
        ],
        careInstructions: ["Machine wash: warm (max 40C or 105F)", "Non-chlorine: bleach as needed", "Tumble dry: medium", "Do not iron", "Do not dryclean"],
        printAreas: [
            {
                id: "front",
                label: "Front Side",
                aspectRatio: 0.8,
                baseImage: "/assets/canvas/tshirt-preview.png",
                editor: { top: 20, left: 28, width: 44, height: 55 }
            },
            {
                id: "back",
                label: "Back Side",
                aspectRatio: 0.8,
                baseImage: "/assets/canvas/tshirt-preview.png",
                editor: { top: 20, left: 28, width: 44, height: 55 }
            }
        ]
    },
    {
        id: "classic-hoodie",
        categoryId: "clothing-warm",
        name: "Unisex Heavy Blend™ Hooded Sweatshirt",
        brand: "Gildan 18500",
        description: "Relaxation itself. Made with a thick blend of cotton and polyester, it feels plush, soft and warm, a perfect choice for any cold day. In the front, the spacious kangaroo pocket adds daily practicality.",
        basePrice: 22.50,
        premiumPrice: 18.25,
        rating: 4.9,
        reviewCount: 890,
        colors: [
            { name: "White", hex: "#FFFFFF" },
            { name: "Black", hex: "#111111" },
            { name: "Forest Green", hex: "#22543D" },
            { name: "Maroon", hex: "#701A27" }
        ],
        sizes: [
            { label: "S", dims: { width: "20in", length: "27in" } },
            { label: "M", dims: { width: "22in", length: "28in" } },
            { label: "L", dims: { width: "24in", length: "29in" } },
            { label: "XL", dims: { width: "26in", length: "30in" } },
        ],
        features: [
            { icon: "Feather", title: "50% Cotton 50% Polyester", description: "Made from specially spun fibers that make very strong and smooth fabric, perfect for printing." },
            { icon: "Pocket", title: "Spacious Pocket", description: "Kangaroo pouch pocket will always keep your hands warm." }
        ],
        careInstructions: ["Machine wash: warm", "Tumble dry: medium"],
        printAreas: [
            {
                id: "front",
                label: "Front",
                aspectRatio: 0.8,
                baseImage: "/assets/canvas/tshirt-editor.png", // Placeholder until hoodie asset
                editor: { top: 25, left: 30, width: 40, height: 40 }
            }
        ]
    },

    // --- HOME: DRINKWARE ---
    {
        id: "premium-mug",
        categoryId: "home-drinkware",
        name: "Ceramic Coffee Mug (11oz)",
        brand: "Generic",
        description: "Warm-up with a nice cuppa out of this customized ceramic coffee mug. It’s BPA and Lead-free, microwave & dishwasher-safe, and made of white, durable ceramic in an 11-ounce size.",
        basePrice: 7.95,
        premiumPrice: 5.50,
        rating: 4.9,
        reviewCount: 450,
        isBestSeller: true,
        colors: [{ name: "White", hex: "#FFFFFF" }],
        sizes: [{ label: "11oz", dims: { height: "3.74in", diameter: "3.15in" } }],
        features: [
            { icon: "Coffee", title: "Microwave-safe", description: "Mug can be safely placed in microwave for food or liquid heating." },
            { icon: "Droplets", title: "Dishwasher-safe", description: "Suitable for dishwasher use." },
            { icon: "Sparkles", title: "Glossy Finish", description: "Full wrap decoration, bright and intense colors." }
        ],
        careInstructions: ["Clean in dishwasher or wash by hand with warm water and dish soap."],
        printAreas: [
            {
                id: "wrap",
                label: "Full Wrap",
                aspectRatio: 2.2,
                baseImage: "/assets/canvas/mug-preview.png",
                editor: { top: 10, left: 10, width: 80, height: 80 }
            }
        ]
    },

    // --- ACCESSORIES: PHONE ---
    {
        id: "phone-case-tough",
        categoryId: "electronics-phone",
        name: "Tough Phone Case",
        brand: "Generic",
        description: "Double layer clip-on protective case with extra durability. The outer shell is made of impact-resistant polycarbonate, while the inner liner sports TPU lining for maximum impact absorption.",
        basePrice: 15.65,
        premiumPrice: 12.50,
        rating: 4.7,
        reviewCount: 310,
        colors: [{ name: "Glossy", hex: "#F3F4F6" }, { name: "Matte", hex: "#374151" }],
        sizes: [{ label: "iPhone 15", dims: {} }, { label: "Samsung S24", dims: {} }],
        features: [
            { icon: "Shield", title: "Dual layer case", description: "For extra durability and protection." },
            { icon: "Smartphone", title: "Impact resistant", description: "Polycarbonate outer shell and TPU inner liner." }
        ],
        careInstructions: ["Clean with damp cotton or microfiber cloth."],
        printAreas: [
            {
                id: "back",
                label: "Back Surface",
                aspectRatio: 0.5,
                baseImage: "/assets/canvas/phone-case-preview.png",
                editor: { top: 0, left: 0, width: 100, height: 100 }
            }
        ]
    },

    // --- ACCESSORIES: BAGS ---
    {
        id: "basic-tote",
        categoryId: "accessories-bags",
        name: "Basic Canvas Tote Bag",
        brand: "Generic",
        description: "This practical, high-quality tote bag is available in three sizes. All over print provides comfort with style on the beach or out in town. Made from reliable materials, lasting for seasons.",
        basePrice: 14.50,
        premiumPrice: 11.25,
        rating: 4.8,
        reviewCount: 150,
        colors: [{ name: "Natural", hex: "#F5F5DC" }],
        sizes: [{ label: "One Size", dims: { width: "15in", height: "16in" } }],
        features: [
            { icon: "ShoppingBag", title: "Durable Material", description: "100% Polyester body, retains shape and dries quickly." },
            { icon: "Anchor", title: "Reinforced Stitching", description: "Handles with reinforced stitching for stability." },
            { icon: "Box", title: "Boxed Corners", description: "Front and back sides are sewn together by creating extra space at sides." }
        ],
        careInstructions: ["Remove all items from the bag before cleaning. Suggested to pretreat visible stains with stain remover. Mix warm water with laundry detergent and clean the bag with terry washcloth or a soft bristle brush. Let the bag air dry."],
        printAreas: [
            {
                id: "front",
                label: "Front Side",
                aspectRatio: 0.85,
                baseImage: "/assets/canvas/tote-bag-preview.png",
                editor: { top: 25, left: 25, width: 50, height: 50 }
            }
        ]
    },
];

export function getProductsByCategory(categoryId: string) {
    // Simple prefix match to allow "clothing" to show "clothing-tops", "clothing-warm", etc.
    return CATALOG.filter(p => p.categoryId === categoryId || p.categoryId.startsWith(categoryId + "-"));
}

export function getProduct(id: string) {
    return CATALOG.find(p => p.id === id);
}
