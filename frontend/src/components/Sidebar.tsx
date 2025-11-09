import { ClipboardList, PlusCircle, Settings, Server } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useNavigate } from "react-router-dom"

export default function Sidebar({ onNewTicket }: { onNewTicket: () => void }) {
    const navigate = useNavigate()
  return (
    <aside className="w-64 bg-muted/30 border-r h-screen flex flex-col">
  <div className="p-4 border-b text-lg font-semibold tracking-tight">
    Menu
  </div>

  <nav className="flex-1 p-4 flex flex-col gap-2">
    <Button variant="ghost" className="justify-start gap-2 hover:bg-accent">
      <ClipboardList className="h-5 w-5 text-blue-600" />
      Tickets
    </Button>
        <Button
      variant="ghost"
      className="justify-start gap-2 hover:bg-accent"
      onClick={() => navigate("/servers")}
    >
      <Server className="h-5 w-5 text-purple-600" />
      Servers
    </Button>
    <Button
      variant="ghost"
      className="justify-start gap-2 hover:bg-accent"
      onClick={onNewTicket}
    >
      <PlusCircle className="h-5 w-5 text-green-600" />
      New Ticket
    </Button>

  </nav>


  <div className="p-4 border-t">
    <Button variant="ghost" className="justify-start gap-2 hover:bg-accent/40">
      <Settings className="h-5 w-5 text-muted-foreground" />
      Settings
    </Button>
  </div>
</aside>

  )
}
