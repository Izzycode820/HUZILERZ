'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card'
import { Input } from '@/components/shadcn-ui/input'
import { Label } from '@/components/shadcn-ui/label'
import { Switch } from '@/components/shadcn-ui/switch'
import { Button } from '@/components/shadcn-ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/shadcn-ui/select'
import { Plus, Loader2 } from 'lucide-react'
import { useQuery, useMutation } from '@apollo/client/react'
import { GetPackagesDocument } from '@/services/graphql/admin-store/queries/shipping/__generated__/GetPackages.generated'
import { CreatePackageDocument } from '@/services/graphql/admin-store/mutations/shipping/__generated__/CreatePackage.generated'
import { CreatePackageModal } from './CreatePackageModal'

interface ProductShippingSectionProps {
  requiresShipping: boolean
  packageId?: string
  weight?: number
  weightUnit: string
  onRequiresShippingChange: (requiresShipping: boolean) => void
  onPackageIdChange: (packageId?: string) => void
  onWeightChange: (weight?: number) => void
  onWeightUnitChange: (weightUnit: string) => void
}

export function ProductShippingSection({
  requiresShipping,
  packageId,
  weight,
  weightUnit,
  onRequiresShippingChange,
  onPackageIdChange,
  onWeightChange,
  onWeightUnitChange,
}: ProductShippingSectionProps) {
  const [showCreatePackageModal, setShowCreatePackageModal] = useState(false)

  // Query for existing packages
  const { data: packagesData, loading: packagesLoading, refetch: refetchPackages } = useQuery(GetPackagesDocument, {
    variables: { first: 100 },
    skip: !requiresShipping,
  })

  // Mutation for creating new package
  const [createPackage, { loading: createPackageLoading }] = useMutation(CreatePackageDocument)

  const packages = packagesData?.packages?.edges?.map(edge => edge?.node) || []

  const handleCreatePackage = async (packageData: any) => {
    try {
      const result = await createPackage({
        variables: {
          input: {
            name: packageData.name,
            packageType: packageData.packageType,
            size: packageData.size,
            weight: packageData.weight,
            method: packageData.method,
            regionFees: packageData.regionFees,
            estimatedDays: packageData.estimatedDays,
            useAsDefault: packageData.useAsDefault,
            isActive: true,
          }
        }
      })

      if (result.data?.createPackage?.success && result.data.createPackage.package) {
        // Refresh packages list
        await refetchPackages()

        // Select the newly created package
        onPackageIdChange(result.data.createPackage.package.id)

        // Close modal
        setShowCreatePackageModal(false)
      }
    } catch (error) {
      console.error('Failed to create package:', error)
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Shipping</CardTitle>
          <div className="flex items-center gap-2">
            <Label htmlFor="requires-shipping" className="text-sm font-normal cursor-pointer">
              Requires shipping
            </Label>
            <Switch
              id="requires-shipping"
              checked={requiresShipping}
              onCheckedChange={onRequiresShippingChange}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pb-4">

        {requiresShipping && (
          <div className="space-y-4">
            {/* Package and Weight Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Package Selection */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="package">Shipping Package</Label>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowCreatePackageModal(true)}
                    disabled={createPackageLoading}
                    className="h-8 px-2 text-xs"
                  >
                    {createPackageLoading ? (
                      <Loader2 className="h-3 w-3 animate-spin mr-1" />
                    ) : (
                      <Plus className="h-3 w-3 mr-1" />
                    )}
                    Add Package
                  </Button>
                </div>
                <Select value={packageId || ''} onValueChange={onPackageIdChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a package" />
                  </SelectTrigger>
                  <SelectContent>
                    {packagesLoading ? (
                      <div className="flex items-center justify-center p-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="ml-2 text-sm">Loading packages...</span>
                      </div>
                    ) : packages.length === 0 ? (
                      <div className="p-2 text-center text-sm text-muted-foreground">
                        <div className="mb-2">No packages available</div>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => setShowCreatePackageModal(true)}
                          className="w-full"
                        >
                          <Plus className="h-3 w-3 mr-1" />
                          Create First Package
                        </Button>
                      </div>
                    ) : (
                      packages.map((pkg) => {
                        // Format regions for display - parse JSON string first
                        let regions = 'No regions'
                        if (pkg?.regionFees) {
                          try {
                            const regionFeesObj = JSON.parse(pkg.regionFees)
                            regions = Object.keys(regionFeesObj).join(', ')
                          } catch (error) {
                            console.error('Failed to parse regionFees:', error)
                            regions = 'Invalid regions'
                          }
                        }
                        return (
                          <SelectItem key={pkg?.id} value={pkg?.id || ''}>
                            {pkg?.name} - {regions} ({pkg?.method})
                          </SelectItem>
                        )
                      })
                    )}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Select a shipping package
                </p>
              </div>

              {/* Weight */}
              <div className="space-y-2">
                <Label htmlFor="weight">Weight</Label>
                <div className="flex gap-2">
                  <Input
                    id="weight"
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                    value={weight || ''}
                    onChange={(e) => onWeightChange(
                      e.target.value ? parseFloat(e.target.value) : undefined
                    )}
                  />
                  <Select value={weightUnit} onValueChange={onWeightUnitChange}>
                    <SelectTrigger className="w-20">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="kg">kg</SelectItem>
                      <SelectItem value="lb">lb</SelectItem>
                      <SelectItem value="g">g</SelectItem>
                      <SelectItem value="oz">oz</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <p className="text-xs text-muted-foreground">
                  Product weight for shipping
                </p>
              </div>
            </div>

            {/* Shipping Info */}
            <div className="bg-muted p-3 rounded-md">
              <div className="text-sm text-muted-foreground">
                Shipping rates are calculated based on the package and weight you select.
                Make sure these values are accurate to get correct shipping costs.
              </div>
            </div>
          </div>
        )}

        {!requiresShipping && (
          <div className="bg-muted p-3 rounded-md">
            <div className="text-sm text-muted-foreground">
              This product will be marked as a digital product or service that doesn't require shipping.
            </div>
          </div>
        )}

        {/* Create Package Modal */}
        <CreatePackageModal
          open={showCreatePackageModal}
          onOpenChange={setShowCreatePackageModal}
          onSubmit={handleCreatePackage}
          loading={createPackageLoading}
        />
      </CardContent>
    </Card>
  )
}