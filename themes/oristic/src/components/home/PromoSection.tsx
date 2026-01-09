import Link from 'next/link';
import { Button } from '../ui/Button';

export function PromoSection() {
    return (
        <section className="py-16 md:py-24">
            <div className="container mx-auto px-4">
                <div className="relative overflow-hidden rounded-2xl bg-black px-6 py-16 text-center shadow-xl sm:px-16 md:px-24">
                    {/* Background decorative element */}
                    <div className="absolute top-0 left-0 -translate-x-1/2 -translate-y-1/2 h-64 w-64 rounded-full bg-primary/20 blur-3xl" />
                    <div className="absolute bottom-0 right-0 translate-x-1/2 translate-y-1/2 h-64 w-64 rounded-full bg-primary/20 blur-3xl" />

                    <h2 className="mx-auto max-w-2xl text-3xl font-bold tracking-tight text-white sm:text-4xl">
                        Join the movement. Redefine your wardrobe today.
                    </h2>
                    <p className="mx-auto mt-6 max-w-xl text-lg text-gray-300">
                        Get 15% off your first order when you sign up for our newsletter. Plus, get early access to new drops and exclusive events.
                    </p>
                    <div className="mt-10 flex items-center justify-center gap-x-6">
                        <Link href="/shop">
                            <Button size="lg" className="bg-white text-black hover:bg-white/90">
                                Shop Now
                            </Button>
                        </Link>
                        <Link href="/signup">
                            <Button size="lg" variant="outline" className="text-white border-white hover:bg-white/10 hover:text-white">
                                Sign Up
                            </Button>
                        </Link>
                    </div>
                </div>
            </div>
        </section>
    );
}
