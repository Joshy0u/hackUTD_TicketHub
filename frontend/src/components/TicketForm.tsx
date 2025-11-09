import * as React from "react"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select"

import { API_URL } from "@/config"

export default function TicketForm({ open, setOpen, onSubmit }: any) {
  const [title, setTitle] = React.useState("")
  const [description, setDescription] = React.useState("")
  const [priority, setPriority] = React.useState("Medium")
  const [hostname, setHostname] = React.useState("")
  const [loading, setLoading] = React.useState(false)

  async function handleSubmit() {
    if (!title.trim() || !description.trim()) return

    setLoading(true)
    const payload = {
      upload_ts: "Today",
      hostname: hostname || "unknown-host",
      label: `BAD${title}_${priority.charAt(0)}`, // simple mapping
      log_line: description,
    }

    try {
      const res = await fetch(`${API_URL}/logs`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      })

      console.log(`${API_URL}/logs`)

      if (!res.ok) throw new Error(`Failed with ${res.status}`)

      const data = await res.json()
      console.log("✅ Created log:", data)

      // Call parent handler
      onSubmit(payload)

      // Reset fields
      setTitle("")
      setDescription("")
      setPriority("Medium")
      setHostname("")

      // 🔥 Close dialog after success
      setOpen(false)
    } catch (err) {
      console.error("❌ Error submitting log:", err)
      alert("Failed to submit log. Check console for details.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="max-w-md rounded-xl shadow-lg bg-card border border-border">
        <DialogHeader>
          <DialogTitle className="text-lg font-semibold text-foreground">
            Create New Log Entry
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-5">
          <div className="space-y-2">
            <Label>Hostname</Label>
            <Input
              value={hostname}
              onChange={(e) => setHostname(e.target.value)}
              placeholder="Enter host name"
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <Label>Reason</Label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Overheating Alert"
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <Label>Log Details</Label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Include log snippet or error trace"
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <Label>Severity</Label>
            <Select
              value={priority}
              onValueChange={setPriority}
              disabled={loading}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Low">4 - Low</SelectItem>
                <SelectItem value="Medium">3 - Medium</SelectItem>
                <SelectItem value="High">2 - High</SelectItem>
                <SelectItem value="Critical">1 - Critical</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-primary text-primary-foreground hover:bg-primary/90 transition"
          >
            {loading ? "Submitting..." : "Submit Log"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
