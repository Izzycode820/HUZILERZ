import Link from 'next/link';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';

export function Footer() {
    return (
        <footer className="border-t border-border bg-background">
            <div className="container mx-auto px-4 py-12 md:py-16">
                <div className="grid grid-cols-1 gap-8 md:grid-cols-4 lg:grid-cols-5">
                    <div className="lg:col-span-2">
                        <Link href="/" className="text-xl font-bold tracking-tight">
                            MERCHFLOW
                        </Link>
                        <p className="mt-4 max-w-sm text-sm text-muted-foreground">
                            Your premium destination for fashion, accessories, and lifestyle products.
                            Quality and style in every detail.
                        </p>
                    </div>

                    <div>
                        <h3 className="text-sm font-semibold">Shop</h3>
                        <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
                            <li><Link href="/shop/new-arrivals" className="hover:text-foreground">New Arrivals</Link></li>
                            <li><Link href="/shop/women" className="hover:text-foreground">Women</Link></li>
                            <li><Link href="/shop/men" className="hover:text-foreground">Men</Link></li>
                            <li><Link href="/shop/accessories" className="hover:text-foreground">Accessories</Link></li>
                        </ul>
                    </div>

                    <div>
                        <h3 className="text-sm font-semibold">Company</h3>
                        <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
                            <li><Link href="/about" className="hover:text-foreground">About Us</Link></li>
                            <li><Link href="/contact" className="hover:text-foreground">Contact</Link></li>
                            <li><Link href="/terms" className="hover:text-foreground">Terms & Conditions</Link></li>
                            <li><Link href="/privacy" className="hover:text-foreground">Privacy Policy</Link></li>
                        </ul>
                    </div>

                    <div>
                        <h3 className="text-sm font-semibold">Newsletter</h3>
                        <p className="mt-4 text-sm text-muted-foreground">
                            Subscribe to get special offers, free giveaways, and once-in-a-lifetime deals.
                        </p>
                        <form className="mt-4 flex gap-2" onSubmit={(e) => e.preventDefault()}>
                            <Input type="email" placeholder="Enter your email" className="bg-background" />
                            <Button type="submit" size="sm">
                                Subscribe
                            </Button>
                        </form>
                    </div>
                </div>

                <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border pt-8 text-xs text-muted-foreground md:flex-row">
                    <p>&copy; {new Date().getFullYear()} Merchflow. All rights reserved.</p>
                    <div className="flex gap-4">
                        {/* Payment icons could go here */}
                        <span>Visa</span>
                        <span>Mastercard</span>
                        <span>PayPal</span>
                        <span>Amex</span>
                    </div>
                </div>
            </div>
        </footer>
    );
}
