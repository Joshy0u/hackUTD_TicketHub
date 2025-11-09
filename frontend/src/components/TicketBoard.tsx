import * as React from "react"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select"

interface Ticket {
  id: number
  title: string
  description: string
  priority: string
  status: string
  reporter?: string
  assignee?: string
  time?: string
}

interface TicketBoardProps {
  tickets: Ticket[]
  role: string
  onDelete?: (ids: number[]) => void
  onStatusChange?: (id: number, newStatus: string) => void
}

export default function TicketBoard({
  tickets,
  role,
  onDelete,
  onStatusChange,
}: TicketBoardProps) {
  const [selectedIds, setSelectedIds] = React.useState<number[]>([])

  function handleSelect(id: number, checked: boolean) {
    setSelectedIds((prev) =>
      checked ? [...prev, id] : prev.filter((x) => x !== id)
    )
  }

  function handleDeleteSelected() {
    if (onDelete && selectedIds.length > 0) {
      onDelete(selectedIds)
      setSelectedIds([])
    }
  }

  if (!tickets.length)
    return (
      <div className="text-center text-muted-foreground mt-20">
        No tickets found
      </div>
    )

  return (
    <div className="space-y-3">
      {/* Only show for technicians */}
      {role === "Technician" && (
        <div className="flex justify-end">
          <Button
            variant="destructive"
            size="sm"
            disabled={selectedIds.length === 0}
            onClick={handleDeleteSelected}
          >
            Delete Selected ({selectedIds.length})
          </Button>
        </div>
      )}

      <Card className="w-full overflow-x-auto shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 border-b text-muted-foreground">
            <tr>
              {role === "Technician" && (
                <th className="text-left px-4 py-2 w-[5%] font-medium">Select</th>
              )}
              <th className="text-left px-4 py-2 w-[10%] font-medium">Key</th>
              <th className="text-left px-4 py-2 w-[35%] font-medium">Summary</th>
              <th className="text-left px-4 py-2 w-[15%] font-medium">Reporter</th>
              <th className="text-left px-4 py-2 w-[15%] font-medium">Assignee</th>
              <th className="text-left px-4 py-2 w-[10%] font-medium">Status</th>
              <th className="text-left px-4 py-2 w-[10%] font-medium">Priority</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((ticket, i) => (
              <tr
                key={ticket.id}
                className={`border-b hover:bg-muted/30 transition ${
                  i % 2 === 0 ? "bg-background" : "bg-muted/10"
                }`}
              >
                {role === "Technician" && (
                  <td className="px-4 py-2">
                    <Checkbox
                      checked={selectedIds.includes(ticket.id)}
                      onCheckedChange={(checked) =>
                        handleSelect(ticket.id, checked as boolean)
                      }
                    />
                  </td>
                )}

                <td className="px-4 py-2 font-medium text-muted-foreground">
                  RD-{ticket.id.toString().slice(-3)}
                </td>

                <td className="px-4 py-2">
                  <div className="font-medium">{ticket.title}</div>
                  <div className="text-xs text-muted-foreground truncate max-w-xs">
                    {ticket.description}
                  </div>
                </td>

                <td className="px-4 py-2">
                  <div className="flex items-center gap-2">
                    <Avatar className="h-6 w-6">
                      <AvatarImage src={`https://i.pravatar.cc/100?img=${i + 1}`} />
                      <AvatarFallback>
                        {ticket.reporter?.charAt(0) ?? "E"}
                      </AvatarFallback>
                    </Avatar>
                    <span className="truncate">
                      {ticket.reporter ?? "Engineer"}
                    </span>
                  </div>
                </td>

                <td className="px-4 py-2">
                  <div className="flex items-center gap-2">
                    <Avatar className="h-6 w-6">
                      <AvatarImage src={`https://i.pravatar.cc/100?img=${i + 10}`} />
                      <AvatarFallback>
                        {ticket.assignee?.charAt(0) ?? "T"}
                      </AvatarFallback>
                    </Avatar>
                    <span className="truncate">
                      {ticket.assignee ?? "Technician"}
                    </span>
                  </div>
                </td>

                {/* Editable status for technician */}
                <td className="px-4 py-2">
                  {role === "Technician" ? (
                    <Select
                      value={ticket.status}
                      onValueChange={(val) =>
                        onStatusChange?.(ticket.id, val)
                      }
                    >
                      <SelectTrigger className="h-7 w-[130px] text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Open">Open</SelectItem>
                        <SelectItem value="In Progress">In Progress</SelectItem>
                        <SelectItem value="Resolved">Resolved</SelectItem>
                      </SelectContent>
                    </Select>
                  ) : (
                    <Badge
                      className={
                        ticket.status === "Open"
                          ? "bg-blue-500/20 text-blue-600"
                          : ticket.status === "In Progress"
                          ? "bg-yellow-500/20 text-yellow-600"
                          : ticket.status === "Resolved"
                          ? "bg-green-500/20 text-green-600"
                          : "bg-muted/50 text-muted-foreground"
                      }
                    >
                      {ticket.status}
                    </Badge>
                  )}
                </td>

                <td className="px-4 py-2">
                  <Badge
                    className={
                      ticket.priority === "High"
                        ? "bg-red-500/20 text-red-600"
                        : ticket.priority === "Medium"
                        ? "bg-yellow-500/20 text-yellow-600"
                        : "bg-green-500/20 text-green-600"
                    }
                  >
                    {ticket.priority}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  )
}
