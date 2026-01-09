import Link from 'next/link';
import { Button } from '../ui/Button';

export function Hero() {
    return (
        <section className="relative flex h-[80vh] w-full items-center justify-center overflow-hidden bg-muted text-center">
            {/* Background Image Placeholder - In real app, use Next Image */}
            <div
                className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat"
                style={{ backgroundImage: 'url("https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&q=80&w=2000")' }}
            >
                <div className="absolute inset-0 bg-black/40" /> {/* Overlay */}
            </div>

            <div className="relative z-10 flex max-w-4xl flex-col items-center gap-6 px-4 text-white">
                <h1 className="text-4xl font-extrabold tracking-tighter sm:text-5xl md:text-6xl lg:text-7xl">
                    Elevate Your Style
                </h1>
                <p className="max-w-2xl text-lg font-medium text-white/90 sm:text-xl">
                    Discover the new collection. Timeless pieces crafted for the modern individual.
                    Refined aesthetics for every occasion.
                </p>
                <div className="flex flex-col gap-4 sm:flex-row">
                    <Link href="/shop/new-arrivals">
                        <Button size="lg" className="min-w-[160px] bg-white text-black hover:bg-white/90">
                            Shop New Arrivals
                        </Button>
                    </Link>
                    <Link href="/shop/sale">
                        <Button size="lg" variant="outline" className="min-w-[160px] border-white text-white hover:bg-white/20 hover:text-white">
                            View Sale
                        </Button>
                    </Link>
                </div>
            </div>
        </section>
    );
}
