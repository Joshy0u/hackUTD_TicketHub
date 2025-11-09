import * as React from "react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function TicketBoard({ tickets }: { tickets: any[] }) {
  if (!tickets.length)
    return <div className="text-center text-muted-foreground mt-20">No logs found</div>

  // Handle hostname click
  function handleHostnameClick(hostname: string) {
    console.log(`🔍 Host clicked: ${hostname}`)
    alert(`Hostname: ${hostname}`)
  }

  return (
    <Card className="w-full overflow-x-auto shadow-sm">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 border-b text-muted-foreground">
          <tr>
            <th className="text-left px-4 py-2 w-[10%] font-medium">Key</th>
            <th className="text-left px-4 py-2 w-[15%] font-medium">Hostname</th>
            <th className="text-left px-4 py-2 w-[15%] font-medium">Logged At</th>
            <th className="text-left px-4 py-2 w-[15%] font-medium">Reported At</th>
            <th className="text-left px-4 py-2 w-[10%] font-medium">Priority</th>
            <th className="text-left px-4 py-2 w-[35%] font-medium">Log Line</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((log, i) => (
            <tr
              key={log.id}
              className={`border-b hover:bg-muted/30 transition ${
                i % 2 === 0 ? "bg-background" : "bg-muted/10"
              }`}
            >
              <td className="px-4 py-2 font-medium text-muted-foreground">
                RD-{log.id.toString().padStart(4, "0")}
              </td>

              <td
                className="px-4 py-2 text-blue-600 hover:underline cursor-pointer"
                onClick={() => handleHostnameClick(log.hostname)}
              >
                {log.hostname || "—"}
              </td>

              <td className="px-4 py-2">{new Date(log.logged_at).toLocaleString()}</td>
              <td className="px-4 py-2">{log.upload_ts || "—"}</td>

              <td className="px-4 py-2">
                <Badge
                  className={
                    log.label?.endsWith("1")
                      ? "bg-red-500/20 text-red-600"
                      : log.label?.endsWith("2")
                      ? "bg-orange-500/20 text-orange-600"
                      : log.label?.endsWith("3")
                      ? "bg-yellow-500/20 text-yellow-600"
                      : "bg-green-500/20 text-green-600"
                  }
                >
                  {log.label}
                </Badge>
              </td>

              <td className="px-4 py-2 truncate max-w-[250px]">{log.log_line}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  )
}
