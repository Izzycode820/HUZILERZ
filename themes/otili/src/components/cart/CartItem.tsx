'use client';

import Image from 'next/image';
import { Minus, Plus, Trash2 } from 'lucide-react';
import { Button } from '../ui/Button';
import { CartItem as CartItemType } from '@/lib/mock-data/cart';

interface CartItemProps {
    item: CartItemType;
}

export function CartItem({ item }: CartItemProps) {
    return (
        <div className="flex gap-4 py-6 border-b border-border last:border-0">
            <div className="relative h-28 w-24 flex-none overflow-hidden bg-muted">
                <Image
                    src={item.product.images[0]?.url || '/placeholders/product.jpg'}
                    alt={item.product.title}
                    fill
                    className="object-cover"
                    unoptimized
                />
            </div>

            <div className="flex flex-1 flex-col justify-between">
                <div className="flex justify-between gap-4">
                    <div>
                        <h3 className="text-base font-semibold uppercase tracking-wide">{item.product.title}</h3>
                        <p className="mt-1 text-sm text-muted-foreground">{item.product.vendor}</p>
                        {item.variantId && <p className="mt-1 text-xs text-muted-foreground uppercase">Size: S / Color: White</p>}
                    </div>
                    <p className="text-sm font-bold">${item.product.price.toFixed(2)}</p>
                </div>

                <div className="flex items-center justify-between mt-4">
                    <div className="flex items-center gap-4">
                        <div className="flex items-center border border-border">
                            <button className="p-2 hover:bg-accent transition-colors">
                                <Minus className="h-3 w-3" />
                            </button>
                            <span className="w-8 text-center text-sm font-medium">{item.quantity}</span>
                            <button className="p-2 hover:bg-accent transition-colors">
                                <Plus className="h-3 w-3" />
                            </button>
                        </div>
                    </div>
                    <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive">
                        <Trash2 className="mr-2 h-4 w-4" /> Remove
                    </Button>
                </div>
            </div>
        </div>
    );
}
