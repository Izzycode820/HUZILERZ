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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/shadcn-ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/shadcn-ui/table'
import { ChevronRight, Plus } from 'lucide-react'
import { Button } from '@/components/shadcn-ui/button'
import { useQuery, useMutation } from '@apollo/client/react'
import { GetLocationsDocument } from '@/services/graphql/admin-store/queries/inventory/__generated__/GetLocations.generated'
import { CreateLocationDocument } from '@/services/graphql/admin-store/mutations/locations/__generated__/CreateLocation.generated'
import { toast } from 'sonner'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/shadcn-ui/dialog'

interface ProductInventorySectionProps {
  sku: string
  barcode?: string
  trackInventory: boolean
  onhand: number
  available: number
  condition: string
  locationId?: string
  allowBackorders: boolean
  onSkuChange: (sku: string) => void
  onBarcodeChange: (barcode: string) => void
  onTrackInventoryChange: (trackInventory: boolean) => void
  onOnhandChange: (onhand: number) => void
  onAvailableChange: (available: number) => void
  onConditionChange: (condition: string) => void
  onLocationIdChange: (locationId?: string) => void
  onAllowBackordersChange: (allowBackorders: boolean) => void
}

export function ProductInventorySection({
  sku,
  barcode,
  trackInventory,
  onhand,
  available,
  condition,
  locationId,
  allowBackorders,
  onSkuChange,
  onBarcodeChange,
  onTrackInventoryChange,
  onOnhandChange,
  onAvailableChange,
  onConditionChange,
  onLocationIdChange,
  onAllowBackordersChange,
}: ProductInventorySectionProps) {
  const [showMore, setShowMore] = useState(false)

  const [isLocationModalOpen, setIsLocationModalOpen] = useState(false)
  const [newLocationData, setNewLocationData] = useState({
    name: '',
    region: '',
    addressLine1: '',
    addressLine2: '',
    city: '',
    phone: '',
    email: '',
    managerName: '',
    lowStockThreshold: 10,
    isActive: true,
    isPrimary: false,
  })

  // Query locations
  const { data: locationsData, refetch: refetchLocations } = useQuery(GetLocationsDocument)

  // Create location mutation
  const [createLocation, { loading: creatingLocation }] = useMutation(CreateLocationDocument, {
    onCompleted: (data) => {
      if (data.createLocation?.success) {
        toast.success(`Location "${data.createLocation.location?.name}" created successfully`)
        setIsLocationModalOpen(false)
        setNewLocationData({
          name: '',
          region: '',
          addressLine1: '',
          addressLine2: '',
          city: '',
          phone: '',
          email: '',
          managerName: '',
          lowStockThreshold: 10,
          isActive: true,
          isPrimary: false,
        })
        refetchLocations()
        // Auto-select the newly created location
        if (data.createLocation.location?.id) {
          onLocationIdChange(data.createLocation.location.id)
        }
      } else {
        toast.error(data.createLocation?.error || 'Failed to create location')
      }
    },
    onError: (error) => {
      toast.error(error.message)
    },
  })

  const handleCreateLocation = async () => {
    if (!newLocationData.name || !newLocationData.region || !newLocationData.addressLine1 || !newLocationData.city) {
      toast.error('Please fill in required fields: name, region, address, and city')
      return
    }

    await createLocation({
      variables: {
        input: newLocationData,
      },
    })
  }

  const locations = locationsData?.locations?.filter(loc => loc?.isActive) || []

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Inventory</CardTitle>
          <div className="flex items-center gap-2">
            <Label htmlFor="track-inventory" className="text-sm font-normal cursor-pointer">
              Inventory tracked
            </Label>
            <Switch
              id="track-inventory"
              checked={trackInventory}
              onCheckedChange={onTrackInventoryChange}
            />
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pb-4">
        {trackInventory && (
          <>
            {/* Compact Table - Shopify Style */}
            <div className="border rounded-md overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-b bg-muted/30">
                    <TableHead className="h-8 text-xs font-medium px-3">Locations</TableHead>
                    <TableHead className="h-8 text-xs font-medium px-2 text-center w-[100px]">Unavailable</TableHead>
                    <TableHead className="h-8 text-xs font-medium px-2 text-center w-[100px]">Committed</TableHead>
                    <TableHead className="h-8 text-xs font-medium px-2 text-center w-[100px]">Available</TableHead>
                    <TableHead className="h-8 text-xs font-medium px-2 text-center w-[100px]">On hand</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow className="border-0">
                    {/* Location */}
                    <TableCell className="py-1.5 px-3">
                      <div className="flex items-center gap-2">
                        <Select value={locationId} onValueChange={onLocationIdChange}>
                          <SelectTrigger className="h-8 text-xs flex-1">
                            <SelectValue placeholder="Select warehouse/location" />
                          </SelectTrigger>
                          <SelectContent>
                            {locations.map((location) => (
                              <SelectItem key={location!.id} value={location!.id}>
                                {location!.name} ({location!.region})
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>

                        <Dialog open={isLocationModalOpen} onOpenChange={setIsLocationModalOpen}>
                          <DialogTrigger asChild>
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0 shrink-0">
                              <Plus className="h-4 w-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
                            <DialogHeader>
                              <DialogTitle>Add New Warehouse/Location</DialogTitle>
                            </DialogHeader>
                            <div className="space-y-4 pt-4 pb-2">
                              <div className="space-y-2">
                                <Label htmlFor="location-name">Name *</Label>
                                <Input
                                  id="location-name"
                                  value={newLocationData.name}
                                  onChange={(e) => setNewLocationData(prev => ({ ...prev, name: e.target.value }))}
                                  placeholder="e.g., Douala Warehouse"
                                />
                              </div>

                              <div className="space-y-2">
                                <Label htmlFor="location-region">Region *</Label>
                                <Select
                                  value={newLocationData.region}
                                  onValueChange={(val) => setNewLocationData(prev => ({ ...prev, region: val }))}
                                >
                                  <SelectTrigger id="location-region">
                                    <SelectValue placeholder="Select region" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="adamawa">adamawa</SelectItem>
                                    <SelectItem value="centre">centre</SelectItem>
                                    <SelectItem value="east">east</SelectItem>
                                    <SelectItem value="far North">far_north</SelectItem>
                                    <SelectItem value="littoral">littoral</SelectItem>
                                    <SelectItem value="north">north</SelectItem>
                                    <SelectItem value="northwest">northwest</SelectItem>
                                    <SelectItem value="south">south</SelectItem>
                                    <SelectItem value="southwest">southwest</SelectItem>
                                    <SelectItem value="west">west</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>

                              <div className="space-y-2">
                                <Label htmlFor="location-address1">Address Line 1 *</Label>
                                <Input
                                  id="location-address1"
                                  value={newLocationData.addressLine1}
                                  onChange={(e) => setNewLocationData(prev => ({ ...prev, addressLine1: e.target.value }))}
                                  placeholder="Street address"
                                />
                              </div>

                              <div className="space-y-2">
                                <Label htmlFor="location-address2">Address Line 2</Label>
                                <Input
                                  id="location-address2"
                                  value={newLocationData.addressLine2}
                                  onChange={(e) => setNewLocationData(prev => ({ ...prev, addressLine2: e.target.value }))}
                                  placeholder="Apartment, suite, etc. (optional)"
                                />
                              </div>

                              <div className="space-y-2">
                                <Label htmlFor="location-city">City *</Label>
                                <Input
                                  id="location-city"
                                  value={newLocationData.city}
                                  onChange={(e) => setNewLocationData(prev => ({ ...prev, city: e.target.value }))}
                                  placeholder="e.g., Douala"
                                />
                              </div>

                              <div className="space-y-2">
                                <Label htmlFor="location-manager">Manager Name</Label>
                                <Input
                                  id="location-manager"
                                  value={newLocationData.managerName}
                                  onChange={(e) => setNewLocationData(prev => ({ ...prev, managerName: e.target.value }))}
                                  placeholder="e.g., John Doe"
                                />
                              </div>

                              <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-2">
                                  <Label htmlFor="location-phone">Phone</Label>
                                  <Input
                                    id="location-phone"
                                    value={newLocationData.phone}
                                    onChange={(e) => setNewLocationData(prev => ({ ...prev, phone: e.target.value }))}
                                    placeholder="+237..."
                                  />
                                </div>

                                <div className="space-y-2">
                                  <Label htmlFor="location-email">Email</Label>
                                  <Input
                                    id="location-email"
                                    type="email"
                                    value={newLocationData.email}
                                    onChange={(e) => setNewLocationData(prev => ({ ...prev, email: e.target.value }))}
                                    placeholder="email@example.com"
                                  />
                                </div>
                              </div>

                              <div className="space-y-2">
                                <Label htmlFor="location-low-stock">Low Stock Threshold</Label>
                                <Input
                                  id="location-low-stock"
                                  type="number"
                                  min="0"
                                  value={newLocationData.lowStockThreshold}
                                  onChange={(e) => setNewLocationData(prev => ({ ...prev, lowStockThreshold: parseInt(e.target.value) || 0 }))}
                                  placeholder="10"
                                />
                                <p className="text-xs text-muted-foreground">Alert when stock falls below this number</p>
                              </div>

                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <Switch
                                    id="location-active"
                                    checked={newLocationData.isActive}
                                    onCheckedChange={(checked) => setNewLocationData(prev => ({ ...prev, isActive: checked }))}
                                  />
                                  <Label htmlFor="location-active" className="text-sm font-normal cursor-pointer">
                                    Active location
                                  </Label>
                                </div>

                                <div className="flex items-center gap-2">
                                  <Switch
                                    id="location-primary"
                                    checked={newLocationData.isPrimary}
                                    onCheckedChange={(checked) => setNewLocationData(prev => ({ ...prev, isPrimary: checked }))}
                                  />
                                  <Label htmlFor="location-primary" className="text-sm font-normal cursor-pointer">
                                    Primary location
                                  </Label>
                                </div>
                              </div>

                              <div className="flex justify-end gap-2 pt-4">
                                <Button
                                  variant="outline"
                                  onClick={() => setIsLocationModalOpen(false)}
                                  disabled={creatingLocation}
                                >
                                  Cancel
                                </Button>
                                <Button onClick={handleCreateLocation} disabled={creatingLocation}>
                                  {creatingLocation ? 'Creating...' : 'Create Location'}
                                </Button>
                              </div>
                            </div>
                          </DialogContent>
                        </Dialog>
                      </div>
                    </TableCell>

                    {/* Unavailable - Calculated field (you can add logic later) */}
                    <TableCell className="py-1.5 px-2 text-center">
                      <Select defaultValue="0">
                        <SelectTrigger className="h-8 text-xs w-full">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">0</SelectItem>
                        </SelectContent>
                      </Select>
                    </TableCell>

                    {/* Committed - Using your 'condition' field as example */}
                    <TableCell className="py-1.5 px-2 text-center">
                      <Select defaultValue="0">
                        <SelectTrigger className="h-8 text-xs w-full">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">0</SelectItem>
                        </SelectContent>
                      </Select>
                    </TableCell>

                    {/* Available */}
                    <TableCell className="py-1.5 px-2">
                      <Select
                        value={available.toString()}
                        onValueChange={(val) => onAvailableChange(parseInt(val) || 0)}
                      >
                        <SelectTrigger className="h-8 text-xs w-full">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {[0, 10, 20, 30, 40, 50, 100].map((num) => (
                            <SelectItem key={num} value={num.toString()}>
                              {num}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>

                    {/* On Hand */}
                    <TableCell className="py-1.5 px-2">
                      <Select
                        value={onhand.toString()}
                        onValueChange={(val) => onOnhandChange(parseInt(val) || 0)}
                      >
                        <SelectTrigger className="h-8 text-xs w-full">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {[0, 10, 20, 30, 40, 50, 100].map((num) => (
                            <SelectItem key={num} value={num.toString()}>
                              {num}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>

            {/* View adjustment history link */}
            <div className="px-1">
              <button className="text-xs text-blue-600 hover:underline">
                View adjustment history
              </button>
            </div>

            {/* Lower Section - Collapsible with right-aligned chips */}
            <Collapsible open={showMore} onOpenChange={setShowMore}>
              <CollapsibleTrigger className="w-full border rounded-md px-3 py-2.5 hover:bg-muted/30 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ChevronRight className={`h-4 w-4 transition-transform ${showMore ? 'rotate-90' : ''}`} />
                    <span className="text-sm font-medium">SKU</span>
                    <span className="text-sm font-medium">Barcode</span>
                    <span className="text-sm">Sell when out of stock</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {/* Right-aligned chips/badges */}
                    {sku && <Badge variant="secondary" className="text-xs">{sku}</Badge>}
                    {barcode && <Badge variant="secondary" className="text-xs">{barcode}</Badge>}
                    {allowBackorders && (
                      <Badge variant="outline" className="text-xs">
                        On
                      </Badge>
                    )}
                  </div>
                </div>
              </CollapsibleTrigger>

              <CollapsibleContent>
                <div className="border border-t-0 rounded-b-md px-3 py-3 space-y-3 bg-muted/10">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label htmlFor="sku" className="text-xs">SKU (Stock Keeping Unit)</Label>
                      <Input
                        id="sku"
                        placeholder="SKU-001"
                        value={sku}
                        onChange={(e) => onSkuChange(e.target.value)}
                        className="h-8 text-xs"
                      />
                    </div>

                    <div className="space-y-1.5">
                      <Label htmlFor="barcode" className="text-xs">Barcode (ISBN, UPC, GTIN)</Label>
                      <Input
                        id="barcode"
                        placeholder="123456789012"
                        value={barcode || ''}
                        onChange={(e) => onBarcodeChange(e.target.value)}
                        className="h-8 text-xs"
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="condition" className="text-xs">Condition</Label>
                    <Select value={condition} onValueChange={onConditionChange}>
                      <SelectTrigger className="h-8 text-xs">
                        <SelectValue placeholder="Select condition" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="new">New</SelectItem>
                        <SelectItem value="refurbished">Refurbished</SelectItem>
                        <SelectItem value="second_hand">Second Hand</SelectItem>
                        <SelectItem value="used">Used</SelectItem>
                        <SelectItem value="damaged">Damaged</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center gap-2 pt-1">
                    <Switch
                      id="allow-backorders"
                      checked={allowBackorders}
                      onCheckedChange={onAllowBackordersChange}
                    />
                    <Label htmlFor="allow-backorders" className="text-xs font-normal cursor-pointer">
                      Sell when out of stock
                    </Label>
                  </div>
                </div>
              </CollapsibleContent>
            </Collapsible>
          </>
        )}

        {!trackInventory && (
          <div className="bg-muted/30 px-3 py-2 rounded-md border">
            <p className="text-xs text-muted-foreground">
              Inventory tracking is disabled for this product.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}