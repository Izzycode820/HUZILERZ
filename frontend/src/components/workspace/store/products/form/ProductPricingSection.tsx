'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card'
import { Input } from '@/components/shadcn-ui/input'
import { Label } from '@/components/shadcn-ui/label'
import { Switch } from '@/components/shadcn-ui/switch'
import { Badge } from '@/components/shadcn-ui/badge'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/shadcn-ui/collapsible'
import { ChevronRight } from 'lucide-react'

interface ProductPricingSectionProps {
  price: number
  compareAtPrice?: number
  costPrice?: number
  chargeTax: boolean
  paymentCharges: boolean
  chargesAmount?: number
  onPriceChange: (price: number) => void
  onCompareAtPriceChange: (compareAtPrice?: number) => void
  onCostPriceChange: (costPrice?: number) => void
  onChargeTaxChange: (chargeTax: boolean) => void
  onPaymentChargesChange: (paymentCharges: boolean) => void
  onChargesAmountChange: (chargesAmount?: number) => void
}

export function ProductPricingSection({
  price,
  compareAtPrice,
  costPrice,
  chargeTax,
  paymentCharges,
  chargesAmount,
  onPriceChange,
  onCompareAtPriceChange,
  onCostPriceChange,
  onChargeTaxChange,
  onPaymentChargesChange,
  onChargesAmountChange,
}: ProductPricingSectionProps) {
  const [showMore, setShowMore] = useState(false)

  // Calculate profit metrics
  const profit = price > 0 && costPrice ? price - costPrice : 0
  const margin = price > 0 && costPrice ? ((price - costPrice) / price) * 100 : 0
  const discount = compareAtPrice && compareAtPrice > price ? compareAtPrice - price : 0

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Pricing</CardTitle>
      </CardHeader>

      <CardContent className="space-y-3 pb-4">
        {/* Compact Grid - All on one row */}
        <div className="grid grid-cols-4 gap-3">
          {/* Price */}
          <div className="space-y-1.5">
            <Label htmlFor="price" className="text-xs font-medium">Price</Label>
            <div className="relative">
              <span className="absolute left-2 top-1/2 transform -translate-y-1/2 text-xs text-muted-foreground">
                FCFA
              </span>
              <Input
                id="price"
                type="number"
                min="0"
                step="0.01"
                placeholder="0.00"
                value={price || ''}
                onChange={(e) => onPriceChange(parseFloat(e.target.value) || 0)}
                className="h-8 text-xs pl-12"
                required
              />
            </div>
          </div>

          {/* Has Charges */}
          <div className="space-y-1.5">
            <Label htmlFor="payment-charges" className="text-xs font-medium">Has charges</Label>
            <div className="flex items-center h-8">
              <Switch
                id="payment-charges"
                checked={paymentCharges}
                onCheckedChange={onPaymentChargesChange}
              />
            </div>
          </div>

          {/* Charges Amount */}
          <div className="space-y-1.5">
            <Label htmlFor="charges-amount" className="text-xs font-medium">Charges amount</Label>
            <div className="relative">
              <span className="absolute left-2 top-1/2 transform -translate-y-1/2 text-xs text-muted-foreground">
                FCFA
              </span>
              <Input
                id="charges-amount"
                type="number"
                min="0"
                step="0.01"
                placeholder="0.00"
                value={chargesAmount || ''}
                onChange={(e) => onChargesAmountChange(
                  e.target.value ? parseFloat(e.target.value) : undefined
                )}
                className="h-8 text-xs pl-12"
                disabled={!paymentCharges}
              />
            </div>
          </div>

          {/* Charge Tax */}
          <div className="space-y-1.5">
            <Label htmlFor="charge-tax" className="text-xs font-medium">Charge tax</Label>
            <div className="flex items-center h-8">
              <Switch
                id="charge-tax"
                checked={chargeTax}
                onCheckedChange={onChargeTaxChange}
              />
            </div>
          </div>
        </div>

        {/* Collapsible Section - Compare at / Cost */}
        <Collapsible open={showMore} onOpenChange={setShowMore}>
          <CollapsibleTrigger className="w-full border rounded-md px-3 py-2.5 hover:bg-muted/30 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ChevronRight className={`h-4 w-4 transition-transform ${showMore ? 'rotate-90' : ''}`} />
                <span className="text-sm font-medium">Compare at</span>
                <span className="text-sm font-medium">Cost per item</span>
              </div>
              <div className="flex items-center gap-2">
                {compareAtPrice && (
                  <Badge variant="secondary" className="text-xs">
                    FCFA {compareAtPrice.toFixed(2)}
                  </Badge>
                )}
                {costPrice && (
                  <Badge variant="secondary" className="text-xs">
                    FCFA {costPrice.toFixed(2)}
                  </Badge>
                )}
              </div>
            </div>
          </CollapsibleTrigger>

          <CollapsibleContent>
            <div className="border border-t-0 rounded-b-md px-3 py-3 space-y-3 bg-muted/10">
              {/* Two Column Layout */}
              <div className="grid grid-cols-2 gap-3">
                {/* Compare at Price */}
                <div className="space-y-1.5">
                  <Label htmlFor="compare-at-price" className="text-xs">Compare at price</Label>
                  <div className="relative">
                    <span className="absolute left-2 top-1/2 transform -translate-y-1/2 text-xs text-muted-foreground">
                      FCFA
                    </span>
                    <Input
                      id="compare-at-price"
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="0.00"
                      value={compareAtPrice || ''}
                      onChange={(e) => onCompareAtPriceChange(
                        e.target.value ? parseFloat(e.target.value) : undefined
                      )}
                      className="h-8 text-xs pl-12"
                    />
                  </div>
                </div>

                {/* Cost per Item */}
                <div className="space-y-1.5">
                  <Label htmlFor="cost-price" className="text-xs">Cost per item</Label>
                  <div className="relative">
                    <span className="absolute left-2 top-1/2 transform -translate-y-1/2 text-xs text-muted-foreground">
                      FCFA
                    </span>
                    <Input
                      id="cost-price"
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="0.00"
                      value={costPrice || ''}
                      onChange={(e) => onCostPriceChange(
                        e.target.value ? parseFloat(e.target.value) : undefined
                      )}
                      className="h-8 text-xs pl-12"
                    />
                  </div>
                </div>
              </div>

              {/* Profit Metrics - Clean Row Layout */}
              {(costPrice && price > 0) || (compareAtPrice && compareAtPrice > price) ? (
                <div className="space-y-2 pt-2 border-t">
                  {/* Profit Row */}
                  {costPrice && price > 0 && (
                    <div className="flex items-center justify-between text-sm px-2 py-1.5 bg-background rounded">
                      <span className="text-muted-foreground">Profit</span>
                      <span className={`font-medium ${profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        FCFA {profit.toFixed(2)}
                      </span>
                    </div>
                  )}

                  {/* Margin Row */}
                  {costPrice && price > 0 && (
                    <div className="flex items-center justify-between text-sm px-2 py-1.5 bg-background rounded">
                      <span className="text-muted-foreground">Margin</span>
                      <span className={`font-medium ${margin >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {margin.toFixed(1)}%
                      </span>
                    </div>
                  )}

                  {/* Discount Row */}
                  {compareAtPrice && compareAtPrice > price && (
                    <div className="flex items-center justify-between text-sm px-2 py-1.5 bg-background rounded">
                      <span className="text-muted-foreground">Discount</span>
                      <span className="font-medium text-orange-600">
                        Save FCFA {discount.toFixed(2)}
                      </span>
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  )
}