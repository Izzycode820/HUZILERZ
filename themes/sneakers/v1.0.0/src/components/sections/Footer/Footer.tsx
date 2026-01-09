'use client';

import { Separator } from '../../shadcn-ui/separator';
import { Instagram, Twitter, Facebook, Linkedin, Youtube, Globe } from 'lucide-react';

const getSocialIcon = (platform: string) => {
  const normalized = platform.toLowerCase();
  if (normalized.includes('instagram')) return <Instagram className="h-5 w-5" />;
  if (normalized.includes('twitter') || normalized.includes('x')) return <Twitter className="h-5 w-5" />;
  if (normalized.includes('facebook')) return <Facebook className="h-5 w-5" />;
  if (normalized.includes('linkedin')) return <Linkedin className="h-5 w-5" />;
  if (normalized.includes('youtube')) return <Youtube className="h-5 w-5" />;
  return <Globe className="h-5 w-5" />;
};

interface FooterLink {
  label: string;
  href: string;
}

interface FooterColumn {
  title: string;
  links: FooterLink[];
}

interface SocialLink {
  platform: string;
  url: string;
  // icon property is deprecated in favor of platform auto-detection
  icon?: string;
}

interface FooterProps {
  storeName: string;
  description?: string;
  columns?: FooterColumn[];
  socialLinks?: SocialLink[];
  copyrightText?: string;
  showPaymentMethods?: boolean;
}

export default function Footer({
  storeName,
  description,
  columns = [],
  socialLinks = [],
  copyrightText,
  showPaymentMethods = true,
}: FooterProps) {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-background border-t border-border overflow-hidden pt-20 pb-10 relative">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">

        {/* Large Fade Brand Name */}
        <div className="absolute top-0 left-0 w-full flex justify-center -translate-y-1/2 select-none pointer-events-none opacity-5">
          <h1 className="text-[20vw] font-black uppercase tracking-tighter leading-none whitespace-nowrap">
            {storeName}
          </h1>
        </div>

        {/* Main Footer */}
        <div className="md:py-16 relative">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-12">
            {/* Brand Column */}
            <div className="md:col-span-4 space-y-6">
              <h3 className="text-2xl font-bold uppercase tracking-tight">{storeName}</h3>
              {description && (
                <p className="text-muted-foreground max-w-sm text-base">
                  {description}
                </p>
              )}
              {/* Social Links */}
              {socialLinks.length > 0 && (
                <div className="flex gap-4 pt-2">
                  {socialLinks.map((social, index) => (
                    <a
                      key={index}
                      href={social.url}
                      className="h-10 w-10 flex items-center justify-center rounded-full bg-secondary text-secondary-foreground hover:bg-primary hover:text-primary-foreground transition-all duration-300"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <span className="sr-only">{social.platform}</span>
                      {getSocialIcon(social.platform)}
                    </a>
                  ))}
                </div>
              )}
            </div>

            {/* Link Columns */}
            <div className="md:col-span-8 grid grid-cols-1 sm:grid-cols-3 gap-8">
              {columns.map((column, index) => (
                <div key={index} className="space-y-6">
                  <h4 className="text-sm font-bold uppercase tracking-widest text-foreground/80">
                    {column.title}
                  </h4>
                  <ul className="space-y-4">
                    {column.links.map((link, linkIndex) => (
                      <li key={linkIndex}>
                        <a
                          href={link.href}
                          className="text-base text-muted-foreground hover:text-foreground hover:underline transition-all"
                        >
                          {link.label}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>

        <Separator className="my-8" />

        {/* Bottom Bar */}
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <p className="text-sm text-muted-foreground text-center md:text-left">
            {copyrightText || `© ${currentYear} ${storeName}. All rights reserved.`}
          </p>

          {showPaymentMethods && (
            <div className="flex items-center gap-4 text-muted-foreground opacity-70 grayscale hover:grayscale-0 transition-all">
              <div className="flex gap-3">
                {/* Placeholders for payment icons */}
                <div className="w-10 h-6 bg-gray-200 rounded"></div>
                <div className="w-10 h-6 bg-gray-200 rounded"></div>
                <div className="w-10 h-6 bg-gray-200 rounded"></div>
              </div>
            </div>
          )}
        </div>
      </div>
    </footer>
  );
}
