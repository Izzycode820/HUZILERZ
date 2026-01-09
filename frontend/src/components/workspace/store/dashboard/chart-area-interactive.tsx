"use client"

import * as React from "react"
import { Area, AreaChart, CartesianGrid, XAxis } from "recharts"

import { useIsMobile } from "@/hooks/shadcn/use-mobile"
import {
  Card,
  CardContent,
  CardDescription,
  CardAction,
  CardHeader,
  CardTitle,
} from "@/components/shadcn-ui/card"
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/shadcn-ui/chart"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/shadcn-ui/select"
import {
  ToggleGroup,
  ToggleGroupItem,
} from "@/components/shadcn-ui/toggle-group"

type ChartDataPoint = {
  date: string
  orders: number
  revenue: number
}

type ChartData = {
  data: (ChartDataPoint | null)[]
  config: {
    orders: { label: string; color: string } | null
    revenue: { label: string; color: string } | null
  } | null
}

type ChartAreaInteractiveProps = {
  chartData: ChartData | null | undefined
}

export function ChartAreaInteractive({ chartData }: ChartAreaInteractiveProps) {
  const isMobile = useIsMobile()
  const [timeRange, setTimeRange] = React.useState("30d")

  React.useEffect(() => {
    if (isMobile) {
      setTimeRange("7d")
    }
  }, [isMobile])

  // No data state
  if (!chartData || !chartData.data || chartData.data.length === 0) {
    return (
      <Card className="@container/card">
        <CardHeader>
          <CardTitle>Revenue & Orders</CardTitle>
          <CardDescription>No chart data available</CardDescription>
        </CardHeader>
        <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
          <div className="flex items-center justify-center h-[250px] text-muted-foreground">
            <p>No data to display</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Filter out null data points and prepare for chart
  const validData = chartData.data.filter((item): item is ChartDataPoint => item !== null)

  // Filter by time range (simple filtering - last N days)
  const filteredData = React.useMemo(() => {
    let days = 30
    if (timeRange === "7d") days = 7
    else if (timeRange === "90d") days = 90

    return validData.slice(-days)
  }, [validData, timeRange])

  // Build chart config from backend data
  const chartConfig: ChartConfig = {
    orders: {
      label: chartData.config?.orders?.label || "Orders",
      color: chartData.config?.orders?.color || "hsl(var(--chart-1))",
    },
    revenue: {
      label: chartData.config?.revenue?.label || "Revenue",
      color: chartData.config?.revenue?.color || "hsl(var(--chart-2))",
    },
  }

  return (
    <Card className="@container/card">
      <CardHeader>
        <CardTitle>Revenue & Orders</CardTitle>
        <CardDescription>
          <span className="hidden @[540px]/card:block">
            Showing {filteredData.length} days of data
          </span>
          <span className="@[540px]/card:hidden">{filteredData.length} days</span>
        </CardDescription>
        <CardAction>
          <ToggleGroup
            type="single"
            value={timeRange}
            onValueChange={setTimeRange}
            variant="outline"
            className="hidden *:data-[slot=toggle-group-item]:!px-4 @[767px]/card:flex"
          >
            <ToggleGroupItem value="90d">Last 90 days</ToggleGroupItem>
            <ToggleGroupItem value="30d">Last 30 days</ToggleGroupItem>
            <ToggleGroupItem value="7d">Last 7 days</ToggleGroupItem>
          </ToggleGroup>
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger
              className="flex w-40 **:data-[slot=select-value]:block **:data-[slot=select-value]:truncate h-8 text-sm @[767px]/card:hidden"
              aria-label="Select a value"
            >
              <SelectValue placeholder="Last 30 days" />
            </SelectTrigger>
            <SelectContent className="rounded-xl">
              <SelectItem value="90d" className="rounded-lg">
                Last 90 days
              </SelectItem>
              <SelectItem value="30d" className="rounded-lg">
                Last 30 days
              </SelectItem>
              <SelectItem value="7d" className="rounded-lg">
                Last 7 days
              </SelectItem>
            </SelectContent>
          </Select>
        </CardAction>
      </CardHeader>
      <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
        <ChartContainer
          config={chartConfig}
          className="aspect-auto h-[250px] w-full"
        >
          <AreaChart data={filteredData}>
            <defs>
              <linearGradient id="fillRevenue" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor="var(--color-revenue)"
                  stopOpacity={1.0}
                />
                <stop
                  offset="95%"
                  stopColor="var(--color-revenue)"
                  stopOpacity={0.1}
                />
              </linearGradient>
              <linearGradient id="fillOrders" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor="var(--color-orders)"
                  stopOpacity={0.8}
                />
                <stop
                  offset="95%"
                  stopColor="var(--color-orders)"
                  stopOpacity={0.1}
                />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              minTickGap={32}
              tickFormatter={(value) => {
                const date = new Date(value)
                return date.toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                })
              }}
            />
            <ChartTooltip
              cursor={false}
              defaultIndex={isMobile ? -1 : Math.floor(filteredData.length / 2)}
              content={
                <ChartTooltipContent
                  labelFormatter={(value) => {
                    return new Date(value).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })
                  }}
                  indicator="dot"
                />
              }
            />
            <Area
              dataKey="orders"
              type="natural"
              fill="url(#fillOrders)"
              stroke="var(--color-orders)"
              stackId="a"
            />
            <Area
              dataKey="revenue"
              type="natural"
              fill="url(#fillRevenue)"
              stroke="var(--color-revenue)"
              stackId="a"
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
