import { Breadcrumbs } from '@/components/shared/Breadcrumbs';

export default function AboutPage() {
    return (
        <div className="container mx-auto px-4 py-8 md:py-12 max-w-4xl">
            <Breadcrumbs
                items={[{ label: 'About Us' }]}
                className="mb-8"
            />

            <div className="space-y-16">
                {/* Hero Section */}
                <section className="text-center space-y-6">
                    <h1 className="text-4xl md:text-6xl font-black uppercase tracking-tighter">
                        We Are <span className="text-transparent bg-clip-text bg-gradient-to-r from-black to-gray-500">Merchflow</span>
                    </h1>
                    <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
                        Redefining the digital shopping experience with precision, speed, and an uncompromising eye for detail.
                    </p>
                </section>

                {/* Our Mission */}
                <section className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
                    <div className="h-64 md:h-96 w-full bg-neutral-100 relative overflow-hidden border border-border">
                        <div className="absolute inset-0 flex items-center justify-center text-neutral-300 font-bold text-6xl opacity-20 uppercase -rotate-12 select-none">
                            Identity
                        </div>
                    </div>
                    <div className="space-y-6">
                        <h2 className="text-2xl font-black uppercase tracking-wide">Our Mission</h2>
                        <div className="space-y-4 text-muted-foreground">
                            <p>
                                At Merchflow, we believe that style is not just about what you wear, but how you present yourself to the world. Our mission is to provide a curated collection of premium essentials that empower you to express your unique identity.
                            </p>
                            <p>
                                We are committed to quality, sustainability, and design that stands the test of time. Every piece in our collection is selected with care, ensuring that it meets our rigorous standards for craftsmanship and aesthetic appeal.
                            </p>
                        </div>
                    </div>
                </section>

                {/* Stats / Values */}
                <section className="grid grid-cols-2 md:grid-cols-4 gap-8 py-12 border-y border-border">
                    {[
                        { label: 'Founded', value: '2023' },
                        { label: 'Products', value: '500+' },
                        { label: 'Customers', value: '10k+' },
                        { label: 'Countries', value: '25+' },
                    ].map((stat) => (
                        <div key={stat.label} className="text-center space-y-2">
                            <div className="text-3xl font-black uppercase tracking-tight">{stat.value}</div>
                            <div className="text-sm text-muted-foreground uppercase tracking-widest">{stat.label}</div>
                        </div>
                    ))}
                </section>

                {/* Contact / CTA */}
                <section className="text-center space-y-8 bg-neutral-900 text-white p-12 md:p-24 relative overflow-hidden">
                    <div className="relative z-10 space-y-6">
                        <h2 className="text-3xl md:text-4xl font-black uppercase tracking-tight">Join the Movement</h2>
                        <p className="text-neutral-400 max-w-xl mx-auto">
                            Stay ahead of the curve. Subscribe to our newsletter for exclusive drops and insider access.
                        </p>
                        <button className="bg-white text-black px-8 py-4 text-sm font-bold uppercase tracking-wider hover:bg-neutral-200 transition-colors">
                            Get Started
                        </button>
                    </div>
                    {/* Abstract Background Element */}
                    <div className="absolute top-0 right-0 p-32 bg-white/5 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none" />
                    <div className="absolute bottom-0 left-0 p-32 bg-white/5 rounded-full blur-3xl -ml-16 -mb-16 pointer-events-none" />
                </section>
            </div>
        </div>
    );
}
