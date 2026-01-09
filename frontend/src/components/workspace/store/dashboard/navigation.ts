/**
 * Store Workspace Navigation Configuration
 * Store-specific navigation items for sidebar
 */

import {
  IconBuildingStore,
  IconChartBar,
  IconDashboard,
  IconPackage,
  IconShoppingCart,
  IconSettings,
  IconHelp,
  IconSearch,
  IconUsers,
  IconCreditCard,
  IconUpload,
  IconInfoCircle,
} from "@tabler/icons-react"

// Store navigation items
export const storeNavMain = [
  {
    title: "Dashboard",
    url: "#",
    icon: IconDashboard,
  },
  {
    title: "Products",
    url: "#",
    icon: IconPackage,
  },
  {
    title: "Orders",
    url: "#",
    icon: IconShoppingCart,
  },
  {
    title: "Analytics",
    url: "#",
    icon: IconChartBar,
  },
  {
    title: "Customers",
    url: "#",
    icon: IconUsers,
  },
]

// Store document shortcuts
export const storeDocuments = [
  {
    name: "Inventory",
    url: "#",
    icon: IconPackage,
  },
  {
    name: "Transactions",
    url: "#",
    icon: IconCreditCard,
  },
  {
    name: "Bulk Upload",
    url: "#",
    icon: IconUpload,
  },
]

// Store secondary navigation
export const storeNavSecondary = [
  {
    title: "Settings",
    url: "#",
    icon: IconSettings,
  },
  {
    title: "Get Help",
    url: "#",
    icon: IconHelp,
  },
  {
    title: "Themes",
    url: "#",
    icon: IconSettings,
  },
]

// Store workspace metadata
export const storeWorkspaceConfig = {
  name: "Store Workspace",
  icon: IconBuildingStore,
  type: "store" as const,
}
