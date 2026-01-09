'use client';

import { AccordionItem } from '../ui/Accordion';
import { categories } from '@/lib/mock-data/categories';
import { Button } from '../ui/Button'; // Assuming Button component exists

export function FilterSidebar({ className }: { className?: string }) {
    return (
        <div className={className}>
            <div className="flex items-center justify-between py-4 md:hidden">
                <h2 className="text-lg font-black uppercase tracking-wide">Filters</h2>
                <Button variant="ghost" size="sm" className="rounded-none uppercase font-bold">Close</Button>
            </div>

            <AccordionItem title="Categories" defaultOpen>
                <ul className="space-y-2 text-sm text-muted-foreground">
                    {categories.map((cat) => (
                        <li key={cat.id}>
                            <label className="flex items-center gap-2 cursor-pointer hover:text-foreground">
                                <input type="checkbox" className="border-input rounded-none accent-primary" />
                                {cat.name}
                            </label>
                        </li>
                    ))}
                </ul>
            </AccordionItem>

            <AccordionItem title="Price" defaultOpen>
                <div className="space-y-4">
                    <div className="flex items-center gap-2">
                        <input type="range" min="0" max="1000" className="w-full h-1 bg-secondary rounded-none appearance-none cursor-pointer accent-primary" />
                    </div>
                    <div className="flex items-center justify-between text-sm">
                        <span>$0</span>
                        <span>$1000+</span>
                    </div>
                </div>
            </AccordionItem>

            <AccordionItem title="Size">
                <div className="grid grid-cols-4 gap-2">
                    {['XS', 'S', 'M', 'L', 'XL', 'XXL'].map((size) => (
                        <button key={size} className="flex h-8 w-full items-center justify-center border border-input text-xs hover:bg-primary hover:text-primary-foreground transition-colors">
                            {size}
                        </button>
                    ))}
                </div>
            </AccordionItem>

            <AccordionItem title="Color">
                <div className="flex flex-wrap gap-2">
                    {[
                        { name: 'Black', class: 'bg-black' },
                        { name: 'White', class: 'bg-white border' },
                        { name: 'Red', class: 'bg-red-500' },
                        { name: 'Blue', class: 'bg-blue-500' },
                        { name: 'Green', class: 'bg-green-500' },
                    ].map((color) => (
                        <button
                            key={color.name}
                            className={`h-6 w-6 rounded-full ring-offset-2 hover:ring-2 ring-primary ${color.class}`}
                            aria-label={color.name}
                            title={color.name}
                        />
                    ))}
                </div>
            </AccordionItem>
        </div>
    );
}
