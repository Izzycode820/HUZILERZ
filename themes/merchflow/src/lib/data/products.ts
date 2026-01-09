import { ProductConfig } from "../types/canvas";

export const PRODUCTS: ProductConfig[] = [
    {
        id: "classic-tee",
        name: "Unisex Heavy Cotton Tee",
        category: "Mens Clothing",
        brand: "Gildan 5000",
        basePrice: 12.35,
        premiumPrice: 9.85,
        rating: 4.8,
        reviewCount: 1240,
        description: "The unisex heavy cotton tee is the basic staple of any wardrobe. It is the foundation upon which casual fashion grows. All it needs is a personalized design to elevate things to profitability. The specially spun fibers provide a smooth surface for premium printing vividity and sharpness.",
        features: [
            {
                icon: "ShieldCheck", // Simple icon naming convention or mapping
                title: "100% Cotton",
                description: "Made from specially spun fibers that make very strong and smooth fabric, perfect for printing."
            },
            {
                icon: "Minimize2",
                title: "Without side seams",
                description: "Knitted in one piece using tubular knit, it reduces fabric waste and makes garment more attractive."
            },
            {
                icon: "Maximize2",
                title: "Ribbed knit collar",
                description: "Ribbed knit makes collar highly elastic and helps retain its shape."
            },
            {
                icon: "Layers",
                title: "Shoulder tape",
                description: "Twill tape covers the shoulder seams to stabilize the back of the shirt and to prevent stretching."
            }
        ],
        careInstructions: [
            "Machine wash: warm (max 40C or 105F)",
            "Non-chlorine: bleach as needed",
            "Tumble dry: medium",
            "Do not iron",
            "Do not dryclean"
        ],
        colors: [
            { name: "White", hex: "#FFFFFF" },
            { name: "Black", hex: "#111111" },
            { name: "Heather Grey", hex: "#9CA3AF" },
            { name: "Navy", hex: "#1E3A8A" },
            { name: "Red", hex: "#EF4444" },
            { name: "Royal", hex: "#3B82F6" },
        ],
        sizes: [
            { label: "S", width: "18.00", length: "28.00", sleeve: "15.62" },
            { label: "M", width: "20.00", length: "29.00", sleeve: "17.00" },
            { label: "L", width: "22.00", length: "30.00", sleeve: "18.50" },
            { label: "XL", width: "24.00", length: "31.00", sleeve: "20.00" },
            { label: "2XL", width: "26.00", length: "32.00", sleeve: "21.50" },
            { label: "3XL", width: "28.00", length: "33.00", sleeve: "22.88" },
        ],
        views: [
            {
                id: "front",
                name: "Front Side",
                editorBaseImage: "/assets/canvas/tshirt-editor.png",
                previewBaseImage: "/assets/canvas/tshirt-preview.png",
                printArea: {
                    top: 20,
                    left: 28,
                    width: 44,
                    height: 55,
                },
            },
            {
                id: "back",
                name: "Back Side",
                editorBaseImage: "/assets/canvas/tshirt-editor.png",
                previewBaseImage: "/assets/canvas/tshirt-preview.png",
                printArea: {
                    top: 20,
                    left: 28,
                    width: 44,
                    height: 55,
                },
            },
        ],
    },
    {
        id: "premium-mug",
        name: "Ceramic Coffee Mug (11oz)",
        category: "Drinkware",
        brand: "Generic",
        basePrice: 7.95,
        premiumPrice: 5.50,
        rating: 4.9,
        reviewCount: 450,
        description: "Warm-up with a nice cuppa out of this customized ceramic coffee mug. It’s BPA and Lead-free, microwave & dishwasher-safe, and made of white, durable ceramic in an 11-ounce size.",
        features: [
            {
                icon: "Coffee",
                title: "Microwave-safe",
                description: "Mug can be safely placed in microwave for food or liquid heating."
            },
            {
                icon: "Droplets",
                title: "Dishwasher-safe",
                description: "Suitable for dishwasher use."
            },
            {
                icon: "Sparkles",
                title: "Glossy Finish",
                description: "Full wrap decoration, bright and intense colors."
            }
        ],
        careInstructions: [
            "Clean in dishwasher or wash by hand with warm water and dish soap."
        ],
        colors: [
            { name: "White", hex: "#FFFFFF" },
        ],
        sizes: [
            { label: "11oz", width: "3.74", length: "3.15" }
        ],
        views: [
            {
                id: "side-right",
                name: "Right Side",
                editorBaseImage: "/assets/canvas/mug-preview.png",
                previewBaseImage: "/assets/canvas/mug-preview.png",
                printArea: {
                    top: 25,
                    left: 30,
                    width: 40,
                    height: 50,
                },
            },
            {
                id: "side-left",
                name: "Left Side",
                editorBaseImage: "/assets/canvas/mug-preview.png",
                previewBaseImage: "/assets/canvas/mug-preview.png",
                printArea: {
                    top: 25,
                    left: 30,
                    width: 40,
                    height: 50,
                },
            },
        ],
    },
];
