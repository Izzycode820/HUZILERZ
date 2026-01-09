"use client"

/**
 * Leave Workspace Button with Confirmation Modal
 * Security feature - allows users to exit workspace context and clear permissions
 */

import { useState } from "react"
import { useRouter } from "next/navigation"
import { IconLogout } from "@tabler/icons-react"
import { toast } from "sonner"
import { useWorkspace } from "@/hooks/authentication/useWorkspace"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/shadcn-ui/alert-dialog"
import { Button } from "@/components/shadcn-ui/button"

export function LeaveWorkspaceButton() {
  const router = useRouter()
  const { leaveWorkspace, currentWorkspace } = useWorkspace()
  const [isLeaving, setIsLeaving] = useState(false)

  const handleLeaveWorkspace = async () => {
    try {
      setIsLeaving(true)

      // Call backend to leave workspace (revokes old token, issues new one)
      await leaveWorkspace()

      // Show success message
      toast.success("Left workspace", {
        description: `You have successfully left ${currentWorkspace?.name || 'the workspace'}.`,
      })

      // Navigate to workspace listing
      router.push("/workspace")

    } catch (error) {
      console.error("Leave workspace error:", error)

      toast.error("Failed to leave workspace", {
        description: error instanceof Error ? error.message : "An error occurred",
      })
    } finally {
      setIsLeaving(false)
    }
  }

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="w-full justify-start gap-2 text-muted-foreground hover:text-foreground"
        >
          <IconLogout className="h-4 w-4" />
          <span>Leave Workspace</span>
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Leave workspace?</AlertDialogTitle>
          <AlertDialogDescription>
            You are about to leave <span className="font-semibold">{currentWorkspace?.name || 'this workspace'}</span>.
            <br />
            <br />
            Your workspace permissions will be cleared for security. You can re-enter this workspace anytime from the workspace listing.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isLeaving}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleLeaveWorkspace}
            disabled={isLeaving}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isLeaving ? "Leaving..." : "Leave Workspace"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
