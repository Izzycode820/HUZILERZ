import Link from 'next/link';
import Image from 'next/image';
import { categories } from '@/lib/mock-data/categories';
import { Button } from '../ui/Button';

export function FeaturedCategories() {
    // Use first 3 items for a 1-Large + 2-Small grid
    const featuredCats = categories.slice(0, 3);

    return (
        <section className="py-16 md:py-24">
            <div className="container mx-auto px-4">
                <div className="mb-12 text-center">
                    <h2 className="text-3xl font-bold tracking-tight uppercase">Collections</h2>
                    <div className="mx-auto mt-4 h-1 w-20 bg-primary" /> {/* Decorative line */}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 auto-rows-[300px]">
                    {featuredCats.map((cat, index) => {
                        // First item spans 2 columns and 2 rows (Large)
                        const isLarge = index === 0;
                        const gridClass = isLarge ? 'md:col-span-2 md:row-span-2' : 'md:col-span-2 md:row-span-1';

                        return (
                            <Link
                                key={cat.id}
                                href={`/shop/${cat.slug}`}
                                className={`group relative overflow-hidden bg-muted ${gridClass}`}
                            >
                                <Image
                                    src={cat.image || '/placeholders/category.jpg'}
                                    alt={cat.name}
                                    fill
                                    className="object-cover transition-transform duration-700 group-hover:scale-105"
                                    sizes={isLarge ? '(max-width: 768px) 100vw, 50vw' : '(max-width: 768px) 100vw, 25vw'}
                                    priority={index < 2}
                                />
                                <div className="absolute inset-0 bg-black/10 transition-colors group-hover:bg-black/20" />

                                <div className="absolute inset-0 flex flex-col justify-end p-8">
                                    <div className="transform translate-y-4 opacity-100 transition-all duration-300 group-hover:-translate-y-0">
                                        <h3 className="text-2xl md:text-3xl font-bold text-white uppercase tracking-wider mb-2 drop-shadow-md">
                                            {cat.name}
                                        </h3>
                                        <div className="h-0.5 w-0 bg-white transition-all duration-300 group-hover:w-16 mb-4" />
                                        <Button
                                            variant="secondary"
                                            className="rounded-none bg-white text-black hover:bg-black hover:text-white transition-colors"
                                        >
                                            Shop Now
                                        </Button>
                                    </div>
                                </div>
                            </Link>
                        );
                    })}
                </div>
            </div>
        </section>
    );
}
