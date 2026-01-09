/**
 * Fly-to-Cart Animation
 * Pure DOM-based animation using transforms for 60fps performance
 * No React dependencies - immune to re-renders
 */

export function triggerFlyToCartAnimation(startX: number, startY: number) {
    // Get cart icon position
    const cartIcon = document.getElementById('cart-button');
    if (!cartIcon) {
        console.warn('Cart button not found - animation skipped');
        return;
    }

    const cartRect = cartIcon.getBoundingClientRect();
    const endX = cartRect.left + cartRect.width / 2;
    const endY = cartRect.top + cartRect.height / 2;

    // Create animated circle
    const circle = document.createElement('div');
    circle.className = 'fly-to-cart-animation';

    // Position at start coordinates
    circle.style.cssText = `
    position: fixed;
    left: ${startX}px;
    top: ${startY}px;
    width: 40px;
    height: 40px;
    background: hsl(var(--primary));
    border-radius: 50%;
    z-index: 9999;
    pointer-events: none;
    transform: translate(-50%, -50%);
  `;

    // Add to DOM
    document.body.appendChild(circle);

    // Trigger animation on next frame (force reflow)
    requestAnimationFrame(() => {
        circle.style.transition = 'all 600ms cubic-bezier(0.4, 0, 0.2, 1)';
        circle.style.transform = `
      translate(${endX - startX - 20}px, ${endY - startY - 20}px) 
      scale(0.2)
    `;
        circle.style.opacity = '0';
    });

    // Cleanup after animation
    circle.addEventListener('transitionend', () => {
        circle.remove();
    });

    // Fallback cleanup in case transitionend doesn't fire
    setTimeout(() => {
        if (circle.parentNode) {
            circle.remove();
        }
    }, 700);
}
