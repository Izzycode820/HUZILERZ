import {
  InfoBanner,
  Header,
  Hero,
  ShopByCategory,
  FeaturedProducts,
  HowItWorks,
  Collections,
  ProductSelector,
  PromotionalGrid,
  ShippingInfo,
  CustomerReviews,
  Footer
} from "@/components/sections";

export default function Home() {
  return (
    <main className="min-h-screen">
      <InfoBanner />
      <Header />
      <Hero />
      <ShopByCategory />
      <FeaturedProducts />
      <HowItWorks />
      <Collections />
      <ProductSelector />
      <PromotionalGrid />
      <ShippingInfo />
      <CustomerReviews />
      <Footer />
    </main>
  );
}
