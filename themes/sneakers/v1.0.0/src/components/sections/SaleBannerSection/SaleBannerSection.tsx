import { Button } from '../../shadcn-ui/button';
import { Badge } from '../../shadcn-ui/badge';
import { ArrowRight } from 'lucide-react';

interface SaleBannerSectionProps {
  headline: string;
  description: string;
  offerText: string;
  ctaText: string;
  ctaLink?: string;
  backgroundImage: string;
  overlayOpacity?: number;
}

export default function SaleBannerSection({
  headline,
  description,
  offerText,
  ctaText,
  ctaLink = "#",
  backgroundImage,
  overlayOpacity = 70,
}: SaleBannerSectionProps) {
  return (
    <section className="py-8 bg-background">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative overflow-hidden rounded-none shadow-lg min-h-[450px] flex items-center border border-gray-100 dark:border-gray-800">
          {/* Background */}
          <div
            className="absolute inset-0 bg-cover bg-center bg-no-repeat transition-transform hover:scale-105 duration-700"
            style={{ backgroundImage: `url(${backgroundImage})` }}
          />
          <div
            className="absolute inset-0 bg-black"
            style={{ opacity: overlayOpacity / 100 }}
          />

          {/* Content */}
          <div className="relative z-10 w-full py-16">
            <div className="max-w-3xl mx-auto text-center space-y-6 px-4">
              <div className="space-y-3">
                <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-white uppercase tracking-tighter leading-none">
                  {headline}
                </h2>
                <p className="text-base sm:text-lg text-white/90 max-w-xl mx-auto font-medium">
                  {description}
                </p>
              </div>

              <div className="flex flex-col items-center justify-center gap-6">
                <div className="p-3 border border-white/30 backdrop-blur-sm bg-white/10 rounded-none">
                  <div className="text-2xl sm:text-4xl font-black text-white uppercase tracking-widest" dangerouslySetInnerHTML={{ __html: offerText }} />
                </div>

                <Button asChild size="lg" className="min-w-[180px] h-12 rounded-none bg-white text-black hover:bg-white/90 uppercase tracking-wide font-bold text-base border border-transparent hover:border-white transition-all">
                  <a href={ctaLink}>
                    {ctaText}
                  </a>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
