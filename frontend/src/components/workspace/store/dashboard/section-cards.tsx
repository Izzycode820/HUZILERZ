import { IconTrendingDown, IconTrendingUp } from "@tabler/icons-react"

import { Badge } from "@/components/shadcn-ui/badge"
import {
  Card,
  CardAction,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/shadcn-ui/card"

type DashboardCard = {
  title: string
  value: string
  trend: string
  trendDirection: string
}

type SectionCardsProps = {
  cards: (DashboardCard | null)[]
}

export function SectionCards({ cards }: SectionCardsProps) {
  // Filter out null cards and ensure we have data
  const validCards = cards.filter((card): card is DashboardCard => card !== null)

  if (validCards.length === 0) {
    return (
      <div className="px-4 lg:px-6">
        <p className="text-muted-foreground text-center py-8">No analytics data available</p>
      </div>
    )
  }

  return (
    <div className="
        flex overflow-x-auto pb-4 gap-4 px-4 snap-x snap-mandatory 
        lg:grid lg:grid-cols-4 lg:pb-0 lg:overflow-visible
        scrollbar-none
    ">
      {validCards.map((card, index) => {
        const isUp = card.trendDirection === 'up'
        const TrendIcon = isUp ? IconTrendingUp : IconTrendingDown

        return (
          <div key={index} className="min-w-[85%] sm:min-w-[45%] snap-center lg:min-w-0">
            <Card className="@container/card h-full">
              <CardHeader>
                <CardDescription>{card.title}</CardDescription>
                <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
                  {card.value}
                </CardTitle>
                <CardAction>
                  <Badge variant="outline">
                    <TrendIcon className="size-3" />
                    {card.trend}
                  </Badge>
                </CardAction>
              </CardHeader>
            </Card>
          </div>
        )
      })}
    </div>
  )
}
