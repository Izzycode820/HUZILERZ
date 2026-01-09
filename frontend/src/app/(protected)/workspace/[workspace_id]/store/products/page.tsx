"use client"

import ProductsListContainer from "@/components/workspace/store/products/list/ProductsListContainer"

export default function ProductsPage() {
  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        <ProductsListContainer />
      </div>
    </div>
  )
}