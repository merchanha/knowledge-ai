import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'

interface DeleteDirectoryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  directoryName: string
  pending?: boolean
  onConfirm: () => void
}

export function DeleteDirectoryDialog({
  open,
  onOpenChange,
  directoryName,
  pending,
  onConfirm,
}: DeleteDirectoryDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete “{directoryName}”?</AlertDialogTitle>
          <AlertDialogDescription>
            This removes the folder and its entire subtree (including nested
            KnowledgeNeurons and Commands). This cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={pending}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            variant="destructive"
            disabled={pending}
            onClick={onConfirm}
          >
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
