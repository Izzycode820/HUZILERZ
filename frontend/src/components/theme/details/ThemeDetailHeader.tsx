'use client';

import React from 'react';
import { Badge } from '@/components/shadcn-ui/badge';
import { ThemeTemplateTemplateTypeChoices, ThemeTemplatePriceTierChoices } from '@/types/themes/graphql-base';

interface ThemeDetailHeaderProps {
  name: string;
  author: string;
  version: string;
  templateType: ThemeTemplateTemplateTypeChoices;
  priceTier: ThemeTemplatePriceTierChoices;
  priceAmount: string | null;
}

export function ThemeDetailHeader({
  name,
  author,
  version,
  templateType,
  priceTier,
  priceAmount,
}: ThemeDetailHeaderProps) {
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
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-4xl font-bold mb-2">{name}</h1>
          <p className="text-muted-foreground">
            by {author} · Version {version}
          </p>
        </div>

        <Badge variant={getPriceTierVariant(priceTier)} className="text-lg px-4 py-2">
          {formatPrice(priceAmount)}
        </Badge>
      </div>

      <div>
        <Badge variant="outline">{getTemplateTypeLabel(templateType)}</Badge>
      </div>
    </div>
  );
}
