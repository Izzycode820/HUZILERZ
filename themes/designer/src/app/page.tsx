import CategoriesGrid from "@/components/home/CategoriesGrid";
import NewProductSection from "@/components/home/NewProductSection";
import BannerSlider from "@/components/home/BannerSlider";
import TrendSection from "@/components/home/TrendSection";
import DiscountSection from "@/components/home/DiscountSection";
import ServiceSection from "@/components/home/ServiceSection";
import InstagramGrid from "@/components/home/InstagramGrid";

export default function Home() {
    return (
        <main>
            <CategoriesGrid />
            <NewProductSection />
            <BannerSlider />
            <TrendSection />
            <DiscountSection />
            <ServiceSection />
            <InstagramGrid />
        </main>
    );
}
