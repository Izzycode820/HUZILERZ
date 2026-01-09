"use client"

import { createContext, useContext, useEffect, useState } from "react"

type ThemeValue =
  | "default"
  | "blue"
  | "green"
  | "amber"
  | "default-scaled"
  | "blue-scaled"
  | "mono-scaled"

interface ThemeConfigContextValue {
  activeTheme: ThemeValue
  setActiveTheme: (theme: ThemeValue) => void
}

const ThemeConfigContext = createContext<ThemeConfigContextValue | undefined>(
  undefined
)

export function ThemeConfigProvider({ children }: { children: React.ReactNode }) {
  const [activeTheme, setActiveThemeState] = useState<ThemeValue>("default")
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)

    // Get theme from localStorage
    const savedTheme = localStorage.getItem("activeTheme") as ThemeValue
    if (savedTheme) {
      setActiveThemeState(savedTheme)
    }
  }, [])

  const setActiveTheme = (theme: ThemeValue) => {
    setActiveThemeState(theme)
    localStorage.setItem("activeTheme", theme)
  }

  // Prevent hydration mismatch
  if (!mounted) {
    return null
  }

  // Get theme classes
  const themeClasses = `theme-${activeTheme} ${activeTheme.includes("scaled") ? "theme-scaled" : ""}`

  return (
    <ThemeConfigContext.Provider value={{ activeTheme, setActiveTheme }}>
      <div className={themeClasses}>
        {children}
      </div>
    </ThemeConfigContext.Provider>
  )
}

export function useThemeConfig() {
  const context = useContext(ThemeConfigContext)
  if (context === undefined) {
    throw new Error("useThemeConfig must be used within a ThemeConfigProvider")
  }
  return context
}
