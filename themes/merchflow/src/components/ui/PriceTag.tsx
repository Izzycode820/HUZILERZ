import { cn } from "@/lib/utils";

export function PriceTag({ price, premiumPrice, className }: { price: number, premiumPrice?: number, className?: string }) {
    return (
        <div className={cn("flex flex-col", className)}>
            <span className="font-bold text-gray-900 text-lg">
                From USD {price.toFixed(2)}
            </span>
            {premiumPrice && (
                <span className="text-[#008060] text-xs font-semibold">
                    From USD {premiumPrice.toFixed(2)} with MerchFlow Premium
                </span>
            )}
        </div>
    );
}
