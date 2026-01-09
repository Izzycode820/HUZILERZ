'use client';

import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

interface CartAnimationProps {
    startPosition: { x: number; y: number };
    onComplete: () => void;
}

export function CartAnimation({ startPosition, onComplete }: CartAnimationProps) {
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);

        // Get cart button position
        const cartButton = document.getElementById('cart-button');
        if (!cartButton) {
            onComplete();
            return;
        }

        const cartRect = cartButton.getBoundingClientRect();
        const endPosition = {
            x: cartRect.left + cartRect.width / 2,
            y: cartRect.top + cartRect.height / 2,
        };

        // Calculate distance and duration
        const distance = Math.sqrt(
            Math.pow(endPosition.x - startPosition.x, 2) +
            Math.pow(endPosition.y - startPosition.y, 2)
        );
        const duration = Math.min(800, Math.max(400, distance));

        // Trigger animation end
        const timer = setTimeout(() => {
            onComplete();
        }, duration);

        return () => clearTimeout(timer);
    }, [startPosition, onComplete]);

    if (!mounted) return null;

    return createPortal(
        <div
            className="fixed pointer-events-none z-[9999]"
            style={{
                left: startPosition.x,
                top: startPosition.y,
            }}
        >
            <div
                className="relative"
                style={{
                    animation: `fly-to-cart 800ms cubic-bezier(0.22, 1, 0.36, 1) forwards`,
                }}
            >
                <div className="h-6 w-6 rounded-full bg-primary animate-ping" />
                <div className="absolute inset-0 h-6 w-6 rounded-full bg-primary" />
            </div>
            <style jsx>{`
        @keyframes fly-to-cart {
          0% {
            transform: translate(0, 0) scale(1);
            opacity: 1;
          }
          100% {
            transform: translate(
              calc(${document.getElementById('cart-button')?.getBoundingClientRect().left || 0}px - ${startPosition.x}px + 12px),
              calc(${document.getElementById('cart-button')?.getBoundingClientRect().top || 0}px - ${startPosition.y}px + 12px)
            ) scale(0.3);
            opacity: 0;
          }
        }
      `}</style>
        </div>,
        document.body
    );
}
