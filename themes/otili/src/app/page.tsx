import { Hero } from "@/components/home/Hero";
import { FeaturedCategories } from "@/components/home/FeaturedCategories";
import { TrendingProducts } from "@/components/home/TrendingProducts";
import { DiscountBanner } from "@/components/home/DiscountBanner";
import { PromoSection } from "@/components/home/PromoSection";

export default function Home() {
    return (
        <div className="flex flex-col min-h-screen">
            <Hero />
            <FeaturedCategories />
            <DiscountBanner />
            <TrendingProducts />
            <PromoSection />
        </div>
    );
}
