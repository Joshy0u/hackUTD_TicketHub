import * as React from "react"
import Header from "@/components/Header"
import Sidebar from "@/components/Sidebar"
import TicketForm from "@/components/TicketForm"
import TicketBoard from "@/components/TicketBoard"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select"

export default function App() {
  const [tickets, setTickets] = React.useState<any[]>([])
  const [open, setOpen] = React.useState(false)
  const [role, setRole] = React.useState("Engineer")

  const [searchQuery, setSearchQuery] = React.useState("")
  const [priorityFilter, setPriorityFilter] = React.useState("All")
  const [statusFilter, setStatusFilter] = React.useState("All")

  function handleAddTicket(ticket: any) {
    setTickets((prev) => [
      ...prev,
      {
        ...ticket,
        id: Date.now(),
        reporter: "Engineer " + (prev.length + 1),
        assignee: "Technician " + ((prev.length % 3) + 1),
      },
    ])
  }

  function handleDelete(ids: number[]) {
    setTickets((prev) => prev.filter((t) => !ids.includes(t.id)))
  }

  const filteredTickets = React.useMemo(() => {
    const query = searchQuery.toLowerCase()
    return tickets.filter((t) => {
      const matchesSearch =
        t.title.toLowerCase().includes(query) ||
        t.description.toLowerCase().includes(query)
      const matchesPriority =
        priorityFilter === "All" || t.priority === priorityFilter
      const matchesStatus = statusFilter === "All" || t.status === statusFilter
      return matchesSearch && matchesPriority && matchesStatus
    })
  }, [tickets, searchQuery, priorityFilter, statusFilter])

  return (
    <div className="flex h-screen bg-background">
      <Sidebar onNewTicket={() => setOpen(true)} />
      <div className="flex-1 flex flex-col">
        <Header role={role} setRole={setRole} />

        <main className="flex-1 overflow-auto p-4">
          {/* Filters */}
          <div className="flex flex-wrap gap-3 mb-6 items-center justify-between border-b pb-4">
            <Input
              placeholder="Search tickets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-64"
            />

            <div className="flex gap-3">
              <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Priority" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="All">All Priorities</SelectItem>
                  <SelectItem value="High">High</SelectItem>
                  <SelectItem value="Medium">Medium</SelectItem>
                  <SelectItem value="Low">Low</SelectItem>
                </SelectContent>
              </Select>

              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="All">All Statuses</SelectItem>
                  <SelectItem value="Open">Open</SelectItem>
                  <SelectItem value="In Progress">In Progress</SelectItem>
                  <SelectItem value="Resolved">Resolved</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Unified Ticket Board */}
          <TicketBoard
            tickets={filteredTickets}
            role={role}
            onDelete={handleDelete}
          />
        </main>
      </div>

      <TicketForm open={open} setOpen={setOpen} onSubmit={handleAddTicket} />
    </div>
  )
}
