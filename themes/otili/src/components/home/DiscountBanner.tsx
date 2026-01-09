import Link from 'next/link';
import { Button } from '../ui/Button';
import { homeConfig } from '@/lib/mock-data/home';

export function DiscountBanner() {
    const { discountBanner } = homeConfig;

    if (!discountBanner) return null;

    return (
        <section className="relative w-full py-24 overflow-hidden">
            {/* Background Image Parallax-ish feel */}
            <div
                className="absolute inset-0 bg-cover bg-center bg-no-repeat bg-fixed"
                style={{ backgroundImage: `url("${discountBanner.backgroundImage}")` }}
            >
                <div className="absolute inset-0 bg-black/50 backdrop-blur-[2px]" />
            </div>

            <div className="container relative mx-auto px-4 text-center text-white z-10">
                <h2 className="text-4xl font-black tracking-tighter sm:text-5xl md:text-6xl uppercase drop-shadow-lg">
                    {discountBanner.title}
                </h2>
                <p className="mt-4 text-xl font-medium text-white/90 sm:text-2xl drop-shadow-md">
                    {discountBanner.subtitle}
                </p>
                <div className="mt-8">
                    <Link href={discountBanner.href}>
                        <Button
                            size="lg"
                            className="h-14 min-w-[200px] rounded-none bg-white text-black hover:bg-white/90 uppercase tracking-widest font-bold text-sm"
                        >
                            {discountBanner.buttonText}
                        </Button>
                    </Link>
                </div>
            </div>
        </section>
    );
}
