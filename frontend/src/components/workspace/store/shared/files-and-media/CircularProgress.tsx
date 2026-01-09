'use client'

interface CircularProgressProps {
  /** Progress value 0-100 */
  value: number

  /** Size in pixels */
  size?: number

  /** Stroke width */
  strokeWidth?: number

  /** Show percentage text */
  showPercentage?: boolean

  /** Custom class name */
  className?: string
}

export function CircularProgress({
  value,
  size = 48,
  strokeWidth = 4,
  showPercentage = true,
  className = '',
}: CircularProgressProps) {
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (value / 100) * circumference

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg
        width={size}
        height={size}
        className="rotate-[-90deg]"
      >
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-muted-foreground/20"
        />

        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="text-primary transition-all duration-300 ease-in-out"
        />
      </svg>

      {/* Percentage text */}
      {showPercentage && (
        <span className="absolute text-xs font-medium">
          {Math.round(value)}%
        </span>
      )}
    </div>
  )
}
