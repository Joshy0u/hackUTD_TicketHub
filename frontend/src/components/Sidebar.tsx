import { ClipboardList, PlusCircle, Settings } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function Sidebar({ onNewTicket }: { onNewTicket: () => void }) {
  return (
    <aside className="w-64 bg-muted/30 border-r h-screen flex flex-col">
      <div className="p-4 border-b font-bold text-lg">Menu</div>
      <nav className="flex-1 p-4 flex flex-col gap-2">
        <Button variant="ghost" className="justify-start gap-2"><ClipboardList size={18}/>Tickets</Button>
        <Button variant="ghost" className="justify-start gap-2" onClick={onNewTicket}><PlusCircle size={18}/>New Ticket</Button>
      </nav>
      <div className="p-4 border-t">
        <Button variant="ghost" className="justify-start gap-2"><Settings size={18}/>Settings</Button>
      </div>
    </aside>
  )
}
