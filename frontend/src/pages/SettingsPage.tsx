import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent, Button, Input, Label, Select } from "@/components/ui/primitives";
import { Moon, Sun, Save } from "lucide-react";

export function SettingsPage() {
  const [theme, setTheme] = useState<"light" | "dark">(
    () => (localStorage.getItem("theme") as "light" | "dark") ?? "light"
  );
  const [maxLinear, setMaxLinear] = useState("0.5");
  const [maxAngular, setMaxAngular] = useState("1.0");
  const [sensorFreq, setSensorFreq] = useState("10");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("theme", theme);
  }, [theme]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Appearance */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Appearance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <Label>Theme</Label>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setTheme((t) => (t === "light" ? "dark" : "light"))}
                className="gap-2"
              >
                {theme === "light" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                {theme === "light" ? "Light" : "Dark"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Safety */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Safety Limits</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Max Linear Speed (m/s)</Label>
              <Input type="number" step="0.1" min="0" max="2" value={maxLinear} onChange={(e) => setMaxLinear(e.target.value)} />
            </div>
            <div>
              <Label>Max Angular Speed (rad/s)</Label>
              <Input type="number" step="0.1" min="0" max="5" value={maxAngular} onChange={(e) => setMaxAngular(e.target.value)} />
            </div>
            <Button className="gap-2">
              <Save className="h-4 w-4" />
              Save
            </Button>
          </CardContent>
        </Card>

        {/* Recording */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recording Defaults</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Default Sensor Frequency (Hz)</Label>
              <Select value={sensorFreq} onChange={(e) => setSensorFreq(e.target.value)}>
                <option value="1">1 Hz</option>
                <option value="5">5 Hz</option>
                <option value="10">10 Hz</option>
                <option value="20">20 Hz</option>
                <option value="50">50 Hz</option>
              </Select>
            </div>
            <Button className="gap-2">
              <Save className="h-4 w-4" />
              Save
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
