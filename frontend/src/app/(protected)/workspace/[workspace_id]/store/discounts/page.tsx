"use client"

import DiscountsListContainer from "@/components/workspace/store/discounts/list/DiscountsListContainer"

export default function DiscountsPage() {
  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        <DiscountsListContainer />
      </div>
    </div>
  )
}
