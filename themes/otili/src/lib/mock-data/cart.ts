import { Product, products } from './products';

export interface CartItem {
    id: string;
    product: Product;
    variantId?: string;
    quantity: number;
}

export const cartItems: CartItem[] = [
    {
        id: 'item_1',
        product: products[0], // Cotton T-shirt
        variantId: 'var_1', // S / White
        quantity: 1,
    },
    {
        id: 'item_2',
        product: products[2], // Leather Tote
        quantity: 1,
    }
];
