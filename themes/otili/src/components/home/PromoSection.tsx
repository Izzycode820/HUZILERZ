import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { homeConfig } from '@/lib/mock-data/home';

export function PromoSection() {
    const { promo } = homeConfig;

    return (
        <section className="bg-primary text-primary-foreground py-16 md:py-24">
            <div className="container mx-auto px-4 text-center">
                <h2 className="text-3xl font-bold tracking-tight sm:text-4xl uppercase">{promo.title}</h2>
                <p className="mx-auto mt-4 max-w-2xl text-lg text-primary-foreground/80">
                    {promo.description}
                </p>

                <div className="mx-auto mt-8 flex max-w-md flex-col gap-4 sm:flex-row">
                    <Input
                        type="email"
                        placeholder={promo.placeholder}
                        className="h-12 border-primary-foreground/20 bg-primary-foreground/10 text-primary-foreground placeholder:text-primary-foreground/50 rounded-none focus-visible:ring-primary-foreground/30"
                    />
                    <Button size="lg" variant="secondary" className="h-12 rounded-none px-8 font-bold uppercase tracking-wide">
                        {promo.buttonText}
                    </Button>
                </div>
            </div>
        </section>
    );
}
