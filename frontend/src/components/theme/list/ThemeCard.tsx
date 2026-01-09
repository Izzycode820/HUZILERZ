'use client';

import React from 'react';
import { Card, CardContent } from '@/components/shadcn-ui/card';
import { Badge } from '@/components/shadcn-ui/badge';
import { ThemeTemplateTemplateTypeChoices, ThemeTemplatePriceTierChoices } from '@/types/themes/graphql-base';

interface ThemeCardProps {
  name: string;
  slug: string;
  previewImage: string;
  templateType: ThemeTemplateTemplateTypeChoices;
  priceTier: ThemeTemplatePriceTierChoices;
  priceAmount: string | null;
  onClick: () => void;
}

export function ThemeCard({
  name,
  slug,
  previewImage,
  templateType,
  priceTier,
  priceAmount,
  onClick,
}: ThemeCardProps) {
  const formatPrice = (amount: string | null) => {
    if (!amount || priceTier === ThemeTemplatePriceTierChoices.Free) return 'Free';
    return `${parseFloat(amount).toLocaleString()} FCFA`;
  };

  const getTemplateTypeLabel = (type: ThemeTemplateTemplateTypeChoices) => {
    const labels = {
      [ThemeTemplateTemplateTypeChoices.Ecommerce]: 'E-commerce',
      [ThemeTemplateTemplateTypeChoices.Services]: 'Services',
      [ThemeTemplateTemplateTypeChoices.Blog]: 'Blog',
      [ThemeTemplateTemplateTypeChoices.Restaurant]: 'Restaurant',
    };
    return labels[type] || type;
  };

  const getPriceTierVariant = (tier: ThemeTemplatePriceTierChoices) => {
    const variants = {
      [ThemeTemplatePriceTierChoices.Free]: 'secondary',
      [ThemeTemplatePriceTierChoices.Paid]: 'default',
      [ThemeTemplatePriceTierChoices.Exclusive]: 'destructive',
    };
    return variants[tier] as 'default' | 'secondary' | 'destructive';
  };

  return (
    <Card
      className="group cursor-pointer overflow-hidden transition-all duration-300 hover:shadow-lg hover:scale-[1.02]"
      onClick={onClick}
    >
      <div className="relative aspect-[4/3] overflow-hidden bg-muted">
        {previewImage ? (
          <img
            src={previewImage}
            alt={name}
            className="object-cover w-full h-full transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50">
            <div className="text-center text-gray-500">
              <div className="text-2xl font-bold mb-2">{getTemplateTypeLabel(templateType)}</div>
              <div className="text-sm">No Preview</div>
            </div>
          </div>
        )}
      </div>

      <CardContent className="p-4 space-y-3">
        <div>
          <h3 className="font-semibold text-lg line-clamp-1 group-hover:text-primary transition-colors">
            {name}
          </h3>
        </div>

        <div className="flex items-center justify-between">
          <Badge variant="outline" className="text-xs">
            {getTemplateTypeLabel(templateType)}
          </Badge>

          <Badge variant={getPriceTierVariant(priceTier)} className="text-xs">
            {formatPrice(priceAmount)}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
