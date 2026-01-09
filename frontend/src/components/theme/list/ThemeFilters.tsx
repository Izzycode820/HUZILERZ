'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Checkbox } from '@/components/shadcn-ui/checkbox';
import { Label } from '@/components/shadcn-ui/label';
import { Separator } from '@/components/shadcn-ui/separator';
import { ThemeTemplateTemplateTypeChoices, ThemeTemplatePriceTierChoices } from '@/types/themes/graphql-base';

interface ThemeFiltersProps {
  selectedTemplateType?: string;
  selectedPriceTier?: string;
  onTemplateTypeChange: (type: string | undefined) => void;
  onPriceTierChange: (tier: string | undefined) => void;
}

export function ThemeFilters({
  selectedTemplateType,
  selectedPriceTier,
  onTemplateTypeChange,
  onPriceTierChange,
}: ThemeFiltersProps) {
  const templateTypes = [
    { value: ThemeTemplateTemplateTypeChoices.Ecommerce, label: 'E-commerce' },
    { value: ThemeTemplateTemplateTypeChoices.Services, label: 'Services' },
    { value: ThemeTemplateTemplateTypeChoices.Blog, label: 'Blog' },
    { value: ThemeTemplateTemplateTypeChoices.Restaurant, label: 'Restaurant' },
  ];

  const priceTiers = [
    { value: ThemeTemplatePriceTierChoices.Free, label: 'Free' },
    { value: ThemeTemplatePriceTierChoices.Paid, label: 'Paid' },
    { value: ThemeTemplatePriceTierChoices.Exclusive, label: 'Exclusive' },
  ];

  return (
    <Card className="sticky top-4">
      <CardHeader>
        <CardTitle className="text-lg">Filters</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Industry Filter */}
        <div className="space-y-3">
          <h3 className="font-semibold text-sm">Industry</h3>
          <div className="space-y-2">
            {templateTypes.map((type) => (
              <div key={type.value} className="flex items-center space-x-2">
                <Checkbox
                  id={`industry-${type.value}`}
                  checked={selectedTemplateType === type.value}
                  onCheckedChange={(checked) => {
                    onTemplateTypeChange(checked ? type.value : undefined);
                  }}
                />
                <Label
                  htmlFor={`industry-${type.value}`}
                  className="text-sm font-normal cursor-pointer"
                >
                  {type.label}
                </Label>
              </div>
            ))}
          </div>
        </div>

        <Separator />

        {/* Price Filter */}
        <div className="space-y-3">
          <h3 className="font-semibold text-sm">Price</h3>
          <div className="space-y-2">
            {priceTiers.map((tier) => (
              <div key={tier.value} className="flex items-center space-x-2">
                <Checkbox
                  id={`price-${tier.value}`}
                  checked={selectedPriceTier === tier.value}
                  onCheckedChange={(checked) => {
                    onPriceTierChange(checked ? tier.value : undefined);
                  }}
                />
                <Label
                  htmlFor={`price-${tier.value}`}
                  className="text-sm font-normal cursor-pointer"
                >
                  {tier.label}
                </Label>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
