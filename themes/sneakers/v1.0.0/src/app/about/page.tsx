'use client';

import { useQuery } from '@apollo/client/react';
import { GetStoreSettingsDocument } from '@/services/settings/__generated__/get-store-settings.generated';
import { Skeleton } from '@/components/shadcn-ui/skeleton';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { Phone, Mail, MessageCircle, MapPin } from 'lucide-react';
import { Button } from '@/components/shadcn-ui/button';
import Link from 'next/link';

// About Page Skeleton
function AboutSkeleton() {
    return (
        <div className="container mx-auto px-4 py-8 md:py-12 max-w-4xl">
            <Skeleton className="h-4 w-20 mb-8" />
            <Skeleton className="h-12 w-64 mx-auto mb-6" />
            <Skeleton className="h-6 w-96 mx-auto mb-12" />

            <div className="space-y-8">
                <div className="text-center space-y-4">
                    <Skeleton className="h-4 w-full max-w-2xl mx-auto" />
                    <Skeleton className="h-4 w-full max-w-xl mx-auto" />
                    <Skeleton className="h-4 w-full max-w-lg mx-auto" />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="border border-border p-6 text-center">
                            <Skeleton className="h-10 w-10 mx-auto mb-4 rounded-full" />
                            <Skeleton className="h-5 w-32 mx-auto mb-2" />
                            <Skeleton className="h-4 w-40 mx-auto" />
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default function AboutPage() {
    const { data, loading } = useQuery(GetStoreSettingsDocument, {
        fetchPolicy: 'cache-first',
    });

    const settings = data?.storeSettings;

    if (loading && !settings) {
        return <AboutSkeleton />;
    }

    // Format WhatsApp link
    const whatsappLink = settings?.whatsappNumber
        ? `https://wa.me/${settings.whatsappNumber.replace(/\D/g, '')}`
        : null;

    return (
        <div className="container mx-auto px-4 py-8 md:py-12 max-w-4xl">
            <Breadcrumbs
                items={[{ label: 'About' }]}
                className="mb-8"
            />

            {/* Hero Section */}
            <div className="text-center mb-16">
                <h1 className="text-4xl md:text-5xl font-black uppercase tracking-tighter mb-4">
                    {settings?.storeName || 'About Us'}
                </h1>
                {settings?.storeDescription && (
                    <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                        {settings.storeDescription}
                    </p>
                )}
            </div>

            {/* About Content */}
            <div className="prose prose-lg max-w-none text-center mb-16">
                <p className="text-muted-foreground leading-relaxed">
                    Welcome to {settings?.storeName || 'our store'}. We are dedicated to bringing you
                    the finest products with exceptional quality and service. Our team is passionate
                    about curating the best selection for our customers.
                </p>
            </div>

            {/* Contact Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* WhatsApp */}
                {settings?.whatsappNumber && (
                    <div className="border border-border bg-card p-8 text-center group hover:border-foreground transition-colors">
                        <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <MessageCircle className="h-6 w-6 text-green-600" />
                        </div>
                        <h3 className="font-bold uppercase tracking-wide mb-2">WhatsApp</h3>
                        <p className="text-muted-foreground text-sm mb-4">
                            {settings.whatsappNumber}
                        </p>
                        {whatsappLink && (
                            <Button asChild variant="outline" size="sm" className="rounded-none">
                                <a href={whatsappLink} target="_blank" rel="noopener noreferrer">
                                    Chat Now
                                </a>
                            </Button>
                        )}
                    </div>
                )}

                {/* Phone */}
                {settings?.phoneNumber && (
                    <div className="border border-border bg-card p-8 text-center group hover:border-foreground transition-colors">
                        <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Phone className="h-6 w-6 text-blue-600" />
                        </div>
                        <h3 className="font-bold uppercase tracking-wide mb-2">Phone</h3>
                        <p className="text-muted-foreground text-sm mb-4">
                            {settings.phoneNumber}
                        </p>
                        <Button asChild variant="outline" size="sm" className="rounded-none">
                            <a href={`tel:${settings.phoneNumber}`}>
                                Call Us
                            </a>
                        </Button>
                    </div>
                )}

                {/* Email */}
                {settings?.supportEmail && (
                    <div className="border border-border bg-card p-8 text-center group hover:border-foreground transition-colors">
                        <div className="h-12 w-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Mail className="h-6 w-6 text-purple-600" />
                        </div>
                        <h3 className="font-bold uppercase tracking-wide mb-2">Email</h3>
                        <p className="text-muted-foreground text-sm mb-4 break-all">
                            {settings.supportEmail}
                        </p>
                        <Button asChild variant="outline" size="sm" className="rounded-none">
                            <a href={`mailto:${settings.supportEmail}`}>
                                Send Email
                            </a>
                        </Button>
                    </div>
                )}
            </div>

            {/* No Contact Info Fallback */}
            {!settings?.whatsappNumber && !settings?.phoneNumber && !settings?.supportEmail && (
                <div className="text-center text-muted-foreground py-12">
                    <MapPin className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Contact information coming soon.</p>
                </div>
            )}

            {/* CTA Section */}
            <div className="text-center mt-16 pt-8 border-t border-border">
                <h2 className="text-2xl font-black uppercase tracking-tighter mb-4">
                    Start Shopping
                </h2>
                <p className="text-muted-foreground mb-6">
                    Browse our collection of premium products.
                </p>
                <Button asChild size="lg" className="rounded-none uppercase font-bold tracking-wide">
                    <Link href="/products">View Products</Link>
                </Button>
            </div>
        </div>
    );
}
