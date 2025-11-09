import * as React from "react"
import Header from "@/components/Header"
import Sidebar from "@/components/Sidebar"
import TicketForm from "@/components/TicketForm"
import TicketBoard from "@/components/TicketBoard"
import { Input } from "@/components/ui/input"
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from "@/components/ui/select"
import { API_URL, SERVERS_URL } from "@/config"

export default function Dashboard() {
  const [tickets, setTickets] = React.useState<any[]>([])
  const [open, setOpen] = React.useState(false)
  const [role, setRole] = React.useState("Engineer")
  const [loading, setLoading] = React.useState(true)

  // Filters
  const [searchQuery, setSearchQuery] = React.useState("")
  const [severityFilter, setSeverityFilter] = React.useState("All")

  // ✅ Fetch logs (includes hostname)
  React.useEffect(() => {
    async function fetchLogs() {
      try {
        const res = await fetch(`${API_URL}/logs`)
        if (!res.ok) throw new Error(`Failed to fetch logs: ${res.status}`)
        const data = await res.json()
      console.log(data)
        setTickets(data)
      } catch (err) {
        console.error("❌ Error fetching logs:", err)
      } finally {
        setLoading(false)
      }
    }
    fetchLogs()
  }, [])



  // ✅ Filter + sort by numeric suffix in label (priority level)
  const filteredTickets = React.useMemo(() => {
    const query = searchQuery.toLowerCase()

    const filtered = tickets.filter((t) => {
      const host = (t.hostname || "").toLowerCase()
      const matchesSearch = !query || host.includes(query)
      const priorityNum = parseInt((t.label || "").slice(-1)) || 0
      const matchesSeverity = severityFilter === "All" || priorityNum === Number(severityFilter)
      return matchesSearch && matchesSeverity
    })

    return filtered.sort((a, b) => {
      const numA = parseInt((a.label || "").slice(-1)) || 0
      const numB = parseInt((b.label || "").slice(-1)) || 0
      return numA - numB
    })
  }, [tickets, searchQuery, severityFilter])

  return (
    <div className="flex h-screen bg-background">
      <Sidebar onNewTicket={() => setOpen(true)} />

      <div className="flex-1 flex flex-col">
        <Header role={role} setRole={setRole} />

        <main className="flex-1 overflow-auto p-4">
          {/* Filter Bar */}
          <div className="flex flex-wrap gap-3 mb-6 items-center justify-between border-b pb-4">
            <Input
              placeholder="Search by hostname..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-64"
            />

            {/* Severity Filter */}
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="All">All Severities</SelectItem>
                <SelectItem value="1">1 - Critical</SelectItem>
                <SelectItem value="2">2 - High</SelectItem>
                <SelectItem value="3">3 - Medium</SelectItem>
                <SelectItem value="4">4 - Low</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Pass filtered tickets */}
          {loading ? (
            <div className="text-center text-muted-foreground mt-20">Loading logs...</div>
          ) : (
            <TicketBoard tickets={filteredTickets} />
          )}
        </main>
      </div>

      <TicketForm open={open} setOpen={setOpen} onSubmit={() => {}} />
    </div>
  )
}
