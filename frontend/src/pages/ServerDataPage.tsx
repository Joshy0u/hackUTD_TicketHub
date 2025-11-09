"use client"

import * as React from "react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { SERVERS_URL } from "@/config"
import Sidebar from "@/components/Sidebar"

type Server = {
  rack: { label: string }
  hostname: string
  serial_number: string
  slot: number
}

const TOTAL_RACKS = 36
const AISLES = 6
const RACKS_PER_AISLE = TOTAL_RACKS / AISLES
const RACK_LABELS = Array.from({ length: TOTAL_RACKS }, (_, i) => `R${i + 1}`)

export default function ServerDataCenterPage() {
  const [servers, setServers] = React.useState<Server[]>([])
  const [selectedRack, setSelectedRack] = React.useState<string | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    async function fetchServers() {
      try {
        const res = await fetch(`${SERVERS_URL}/servers/list`)
        if (!res.ok) throw new Error(`Failed to fetch servers: ${res.status}`)
        const data = await res.json()
        console.log("✅ Servers API data:", data)
        setServers(data.servers || [])
      } catch (err: any) {
        console.error("❌ Error fetching servers:", err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    fetchServers()
  }, [])

  // Group servers by rack
  const racks = React.useMemo(() => {
    const map: Record<string, Server[]> = {}
    for (const r of RACK_LABELS) {
      map[r] = servers.filter((s) => s.rack?.label === r)
    }
    return map
  }, [servers])

  const aisleGroups = Array.from({ length: AISLES }, (_, i) =>
    RACK_LABELS.slice(i * RACKS_PER_AISLE, (i + 1) * RACKS_PER_AISLE)
  )

  // states
  if (loading)
    return (
      <div className="h-[80vh] flex items-center justify-center text-muted-foreground">
        Loading data center...
      </div>
    )

  if (error)
    return (
      <div className="h-[80vh] flex items-center justify-center text-destructive">
        Error: {error}
      </div>
    )

    // rack
  if (selectedRack) {
    const rackServers = racks[selectedRack]
    return (
      <div className="p-6 space-y-4">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-semibold text-foreground">
            Rack {selectedRack}
          </h1>
          <Button variant="outline" onClick={() => setSelectedRack(null)}>
            ← Back to Overview
          </Button>
        </div>

        <Card className="p-4 border bg-card shadow-sm">
          {rackServers.length === 0 ? (
            <div className="text-center text-muted-foreground py-10">
              No servers in this rack
            </div>
          ) : (
            <div className="flex flex-col-reverse">
              {Array.from({ length: 8 }, (_, i) => i + 1).map((slot) => {
                const s = rackServers.find((srv) => srv.slot === slot)
                return (
                  <div
                    key={slot}
                    className={`flex justify-between items-center border-b px-3 py-2 text-sm transition-colors ${
                      s
                        ? "bg-muted/30 hover:bg-muted/40 text-foreground"
                        : "text-muted-foreground"
                    }`}
                    title={
                      s
                        ? `Hostname: ${s.hostname}\nSerial: ${s.serial_number}`
                        : `Empty slot #${slot}`
                    }
                  >
                    <span>{s ? s.hostname : "— Empty —"}</span>
                    <Badge
                      variant={s ? "secondary" : "outline"}
                      className={s ? "bg-green-500/20 text-green-600" : ""}
                    >
                      Slot {slot}
                    </Badge>
                  </div>
                )
              })}
            </div>
          )}
        </Card>
      </div>
    )
  }

  // OVERVIEW
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold text-foreground">
        Ticketeer
      </h1>

      <Card className="p-6 bg-card border shadow-sm">
        {servers.length === 0 ? (
          <div className="text-center text-muted-foreground py-20">
            No server data available
          </div>
        ) : (
          <div className="space-y-10">
            {aisleGroups.map((racksInRow, idx) => (
              <div key={idx}>
                <div className="text-sm text-muted-foreground mb-2">
                  Aisle A{idx + 1}
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
                  {racksInRow.map((rackLabel) => {
                    const count = racks[rackLabel]?.length ?? 0
                    const filled = count > 0
                    return (
                      <Card
                        key={rackLabel}
                        onClick={() => setSelectedRack(rackLabel)}
                        className={`cursor-pointer text-center py-8 border transition-all hover:shadow-sm ${
                          filled
                            ? "bg-green-500/10 hover:bg-green-500/20 border-green-500/40 text-green-600"
                            : "bg-muted hover:bg-muted/60 border-muted text-muted-foreground"
                        }`}
                      >
                        <div className="font-semibold text-sm">
                          {rackLabel}
                        </div>
                        <div className="text-[11px] mt-1 text-muted-foreground">
                          {count ? `${count} servers` : "empty"}
                        </div>
                      </Card>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
