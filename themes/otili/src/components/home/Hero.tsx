import Link from 'next/link';
import { Button } from '../ui/Button';
import { homeConfig } from '@/lib/mock-data/home';

export function Hero() {
    const { hero } = homeConfig;

    return (
        <section className="relative flex h-[80vh] w-full items-center justify-center overflow-hidden bg-muted text-center">
            {/* Background Image - Optimized with next/image in real implementation or standard img for now to simplify external domain config */}
            <div
                className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat"
                style={{ backgroundImage: `url("${hero.backgroundImage}")` }}
            >
                <div className="absolute inset-0 bg-black/40" /> {/* Overlay */}
            </div>

            <div className="relative z-10 flex max-w-4xl flex-col items-center gap-6 px-4 text-white">
                <h1 className="text-4xl font-extrabold tracking-tighter sm:text-5xl md:text-6xl lg:text-7xl uppercase">
                    {hero.title}
                </h1>
                <p className="max-w-2xl text-lg font-medium text-white/90 sm:text-xl">
                    {hero.subtitle}
                </p>
                <div className="flex flex-col gap-4 sm:flex-row">
                    <Link href={hero.buttons[0].href}>
                        <Button size="lg" className="min-w-[180px] rounded-none bg-white text-black hover:bg-white/90 uppercase tracking-wide font-bold">
                            {hero.buttons[0].text}
                        </Button>
                    </Link>
                    <Link href={hero.buttons[1].href}>
                        <Button size="lg" variant="outline" className="min-w-[180px] rounded-none border-2 border-white text-white bg-transparent hover:bg-white hover:text-black uppercase tracking-wide font-bold">
                            {hero.buttons[1].text}
                        </Button>
                    </Link>
                </div>
            </div>
        </section>
    );
}
