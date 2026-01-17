'use client';

import { useState, useEffect, useRef } from 'react';
import { Search, X, Loader2, ChevronLeft, ChevronRight } from 'lucide-react';
import { useDebounce } from '@/hooks/useDebounce';
import { useLazyQuery, useMutation } from '@apollo/client/react';
import { GetProductsPaginatedDocument } from '@/services/products/__generated__/get-products-paginated.generated';
import { AddToCartDocument } from '@/services/cart/__generated__/add-to-cart.generated';
import { GetCartDocument } from '@/services/cart/__generated__/get-cart.generated';
import { useSession } from '@/lib/session/SessionProvider';
import { triggerFlyToCartAnimation } from '@/lib/animations/flyToCart';
import { CompactProductCard } from './CompactProductCard';
import { Link } from 'react-router-dom';

/**
 * Search Modal Component
 * Opens only when user starts typing (not on click)
 * Debounced search with pagination and mobile-responsive design
 */

interface SearchModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const RESULTS_PER_PAGE = 10;

export function SearchModal({ isOpen, onClose }: SearchModalProps) {
    const [searchTerm, setSearchTerm] = useState('');
    const [currentPage, setCurrentPage] = useState(1);
    const debouncedSearch = useDebounce(searchTerm, 300);
    const inputRef = useRef<HTMLInputElement>(null);

    const { guestSessionId, createGuestSession } = useSession();
    const [searchProducts, { data, loading }] = useLazyQuery(GetProductsPaginatedDocument);

    // Add to cart mutation with optimistic updates
    const [addToCart] = useMutation(AddToCartDocument, {
        optimisticResponse: (variables) => ({
            __typename: 'Mutation' as const,
            addToCart: {
                __typename: 'AddToCart' as const,
                cart: {
                    __typename: 'CartType' as const,
                    id: guestSessionId || 'temp-cart-id',
                    subtotal: '0',
                    discountCode: null,
                    discountAmount: null,
                    total: null,
                    hasDiscount: null,
                    appliedDiscount: null,
                    itemCount: null,
                    items: null
                }
            }
        }),
        update: (cache, { data }) => {
            if (data?.addToCart?.cart) {
                cache.writeQuery({
                    query: GetCartDocument,
                    variables: { sessionId: guestSessionId || '' },
                    data: {
                        __typename: 'Query',
                        cart: data.addToCart.cart
                    }
                });
            }
        },
    });

    const handleAddToCart = async (productId: string, startPos?: { x: number; y: number }) => {
        // Trigger animation immediately
        if (startPos) {
            triggerFlyToCartAnimation(startPos.x, startPos.y);
        }

        try {
            let sessionId = guestSessionId;
            if (!sessionId) {
                sessionId = await createGuestSession();
            }

            if (!sessionId) return;

            await addToCart({
                variables: {
                    input: {
                        sessionId,
                        productId: productId,
                        quantity: 1,
                    }
                }
            });
        } catch (e) {
            console.error('Failed to add to cart:', e);
        }
    };

    // Execute search when debounced value changes
    useEffect(() => {
        if (debouncedSearch.trim()) {
            setCurrentPage(1); // Reset to first page on new search
            searchProducts({
                variables: {
                    search: debouncedSearch,
                    first: RESULTS_PER_PAGE * 3, // Fetch more for pagination
                },
            });
        }
    }, [debouncedSearch, searchProducts]);

    // Focus input when modal opens
    useEffect(() => {
        if (isOpen && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isOpen]);

    // Close on ESC key
    useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        if (isOpen) {
            document.addEventListener('keydown', handleEsc);
            return () => document.removeEventListener('keydown', handleEsc);
        }
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    const allProducts = data?.products?.edges?.map(edge => edge?.node).filter(Boolean) || [];

    // Pagination logic
    const totalResults = allProducts.length;
    const totalPages = Math.ceil(totalResults / RESULTS_PER_PAGE);
    const startIndex = (currentPage - 1) * RESULTS_PER_PAGE;
    const endIndex = startIndex + RESULTS_PER_PAGE;
    const paginatedProducts = allProducts.slice(startIndex, endIndex);

    const hasResults = allProducts.length > 0;
    const showResults = debouncedSearch.trim().length > 0;

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/50 z-50 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal - Larger on desktop */}
            <div className="fixed inset-x-0 top-0 md:top-16 md:left-1/2 md:-translate-x-1/2 md:max-w-4xl z-50 bg-background shadow-2xl md:rounded-lg overflow-hidden max-h-[95vh] md:max-h-[85vh] flex flex-col">
                {/* Search Input */}
                <div className="p-4 border-b border-border flex items-center gap-3 flex-shrink-0">
                    <Search className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                    <input
                        ref={inputRef}
                        type="text"
                        placeholder="Search products..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="flex-1 bg-transparent outline-none text-base placeholder:text-muted-foreground"
                    />
                    {loading && <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />}
                    <button
                        onClick={onClose}
                        className="p-1 hover:bg-accent rounded-full transition-colors"
                        aria-label="Close search"
                    >
                        <X className="h-5 w-5" />
                    </button>
                </div>

                {/* Results */}
                <div className="flex-1 overflow-y-auto">
                    {!showResults && (
                        <div className="text-center py-16 text-muted-foreground px-4">
                            <Search className="h-12 w-12 mx-auto mb-3 opacity-50" />
                            <p>Start typing to search products</p>
                        </div>
                    )}

                    {showResults && loading && allProducts.length === 0 && (
                        <div className="text-center py-16">
                            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
                            <p className="mt-3 text-muted-foreground">Searching...</p>
                        </div>
                    )}

                    {showResults && !loading && !hasResults && (
                        <div className="text-center py-16 text-muted-foreground px-4">
                            <p>No products found for "{debouncedSearch}"</p>
                        </div>
                    )}

                    {hasResults && (
                        <div className="p-4">
                            {/* Compact Product List - Grid on Desktop, List on Mobile */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2">
                                {paginatedProducts.map((product: any) => (
                                    <CompactProductCard
                                        key={product.id}
                                        id={product.id}
                                        name={product.name}
                                        slug={product.slug}
                                        price={parseFloat(product.price)}
                                        compareAtPrice={product.compareAtPrice ? parseFloat(product.compareAtPrice) : undefined}
                                        imageUrl={product.mediaUploads?.[0]?.optimizedWebp || product.mediaUploads?.[0]?.thumbnailWebp}
                                        onAddToCart={handleAddToCart}
                                        onClose={onClose}
                                    />
                                ))}
                            </div>

                            {/* Pagination */}
                            {totalPages > 1 && (
                                <div className="flex items-center justify-between mt-6 pt-4 border-t border-border">
                                    <button
                                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                        disabled={currentPage === 1}
                                        className="flex items-center gap-1 px-3 py-2 text-sm hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                    >
                                        <ChevronLeft className="h-4 w-4" />
                                        Previous
                                    </button>

                                    <span className="text-sm text-muted-foreground">
                                        Page {currentPage} of {totalPages}
                                    </span>

                                    <button
                                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                        disabled={currentPage === totalPages}
                                        className="flex items-center gap-1 px-3 py-2 text-sm hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                    >
                                        Next
                                        <ChevronRight className="h-4 w-4" />
                                    </button>
                                </div>
                            )}

                            {/* View All Link */}
                            <Link
                                href={`/products?search=${encodeURIComponent(debouncedSearch)}`}
                                onClick={onClose}
                                className="block mt-4 text-center py-3 border border-primary text-primary hover:bg-primary hover:text-primary-foreground transition-colors font-medium"
                            >
                                View All {totalResults} Results
                            </Link>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}
