import Link from 'next/link';
import Image from 'next/image';
import { categories } from '@/lib/mock-data/categories';
import { Button } from '../ui/Button';

export function FeaturedCategories() {
    // Only show first 3 categories for featured section
    const featuredCats = categories.slice(1, 4);

    return (
        <section className="py-16 md:py-24">
            <div className="container mx-auto px-4">
                <div className="mb-12 text-center">
                    <h2 className="text-3xl font-bold tracking-tight">Shop by Category</h2>
                    <p className="mt-4 text-muted-foreground">Browse our curated collections</p>
                </div>

                <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                    {featuredCats.map((cat) => (
                        <Link
                            key={cat.id}
                            href={`/shop/${cat.slug}`}
                            className="group relative h-[400px] overflow-hidden rounded-lg bg-muted"
                        >
                            <Image
                                src={cat.image || '/placeholders/category.jpg'}
                                alt={cat.name}
                                fill
                                className="object-cover transition-transform duration-500 group-hover:scale-110"
                                unoptimized
                            />
                            <div className="absolute inset-0 bg-black/20 transition-colors group-hover:bg-black/30" />
                            <div className="absolute bottom-6 left-6">
                                <h3 className="text-2xl font-bold text-white">{cat.name}</h3>
                                <Button
                                    variant="link"
                                    className="mt-2 h-auto p-0 text-white decoration-white underline-offset-4 hover:decoration-white/80"
                                >
                                    Explore Collection &rarr;
                                </Button>
                            </div>
                        </Link>
                    ))}
                </div>
            </div>
        </section>
    );
}
