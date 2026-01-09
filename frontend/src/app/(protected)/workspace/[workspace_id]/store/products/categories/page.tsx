"use client"

import CategoriesListContainer from "@/components/workspace/store/categories/list/CategoriesListContainer"

export default function CategoriesPage() {
  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        <CategoriesListContainer />
      </div>
    </div>
  )
}