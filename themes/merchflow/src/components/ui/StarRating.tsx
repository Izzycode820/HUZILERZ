import { Star, StarHalf } from "lucide-react";
import { cn } from "@/lib/utils";

export function StarRating({ rating, count, className }: { rating: number, count?: number, className?: string }) {
    return (
        <div className={cn("flex items-center gap-1", className)}>
            <div className="flex text-yellow-400">
                {[1, 2, 3, 4, 5].map((star) => (
                    <Star
                        key={star}
                        className={cn(
                            "w-4 h-4",
                            star <= Math.round(rating) ? "fill-current" : "text-gray-300"
                        )}
                    />
                ))}
            </div>
            {count !== undefined && (
                <span className="text-sm text-gray-500 underline decoration-gray-300 underline-offset-2">
                    {count} reviews
                </span>
            )}
        </div>
    );
}
