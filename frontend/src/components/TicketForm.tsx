import * as React from "react"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from "@/components/ui/select"

export default function TicketForm({ open, setOpen, onSubmit }: any) {
  const [title, setTitle] = React.useState("")
  const [description, setDescription] = React.useState("")
  const [priority, setPriority] = React.useState("Medium")

  function handleSubmit() {
    if (!title.trim()) return
    onSubmit({ title, description, priority, status: "Open" })
    setTitle("")
    setDescription("")
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="max-w-md rounded-xl shadow-lg bg-card">
        <DialogHeader>
          <DialogTitle className="text-lg font-semibold">
            Create New Ticket
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-5">
          <div className="space-y-2">
            <Label>Title</Label>
            <Input placeholder="Server overheating in rack 4A" />
          </div>
          <div className="space-y-2">
            <Label>Description</Label>
            <Textarea placeholder="Include details, affected servers, etc." />
          </div>
          <div className="space-y-2">
            <Label>Priority</Label>
            <Select>
              <SelectTrigger>
                <SelectValue placeholder="Select priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Low">Low</SelectItem>
                <SelectItem value="Medium">Medium</SelectItem>
                <SelectItem value="High">High</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button className="w-full bg-primary text-primary-foreground hover:bg-primary/90">
            Submit Ticket
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
