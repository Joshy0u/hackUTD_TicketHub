import { Bell } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface HeaderProps {
  role: string
  setRole: (role: string) => void
}

export default function Header({ role, setRole }: HeaderProps) {
  return (
    <header className="flex items-center justify-between bg-background border-b px-6 py-3 sticky top-0 z-40">
      <h1 className="text-2xl font-semibold">Datacenter Ticketing</h1>

      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon">
          <Bell />
        </Button>

        <Select value={role} onValueChange={setRole}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Select role" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Engineer">Engineer</SelectItem>
            <SelectItem value="Technician">Technician</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </header>
  )
}
