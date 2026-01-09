import { Button } from '../../shadcn-ui/button';
import { ArrowRight } from 'lucide-react';

interface HeroSectionProps {
  headline: string;
  description: string;
  ctaText: string;
  ctaLink?: string;
  mediaType?: 'image' | 'video';
  mediaUrl: string;
  videoUrl?: string;
  overlayOpacity?: number;
  textAlignment?: 'left' | 'center' | 'right';
}

export default function HeroSection({
  headline,
  description,
  ctaText,
  ctaLink = '#',
  mediaType = 'image',
  mediaUrl,
  videoUrl,
  overlayOpacity = 50,
  textAlignment = 'center',
}: HeroSectionProps) {
  const alignmentClasses = {
    left: 'items-start text-left',
    center: 'items-center text-center',
    right: 'items-end text-right',
  };

  return (
    <section className="relative h-[80vh] w-full flex items-center justify-center overflow-hidden">
      {/* Background Media */}
      {mediaType === 'video' ? (
        <video
          autoPlay
          loop
          muted
          playsInline
          className="absolute inset-0 h-full w-full object-cover"
        >
          <source src={videoUrl || mediaUrl} type="video/mp4" />
        </video>
      ) : (
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: `url(${mediaUrl})` }}
        />
      )}

      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black"
        style={{ opacity: overlayOpacity / 100 }}
      />

      {/* Content */}
      <div className="relative z-10 container mx-auto px-4 sm:px-6 lg:px-8">
        <div className={`flex flex-col gap-6 max-w-4xl mx-auto ${alignmentClasses[textAlignment]}`}>
          <h1
            className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold text-white tracking-tighter uppercase leading-none"
            dangerouslySetInnerHTML={{ __html: headline }}
          />
          <div
            className="text-lg sm:text-xl text-white/90 max-w-2xl font-medium text-rendering-optimizeLegibility [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5"
            dangerouslySetInnerHTML={{ __html: description }}
          />
          <div className="mt-4">
            <Button asChild size="lg" className="min-w-[180px] rounded-none bg-white text-black hover:bg-white/90 uppercase tracking-wide font-bold h-14">
              <a href={ctaLink}>
                {ctaText}
              </a>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
