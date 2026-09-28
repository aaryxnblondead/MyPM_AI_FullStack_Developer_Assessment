import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Container } from "@/components/ui/Container";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Spinner } from "@/components/ui/Spinner";
import { Textarea } from "@/components/ui/Textarea";

const swatches = [
  { name: "primary #113754", cls: "bg-primary" },
  { name: "secondary #666666", cls: "bg-secondary" },
  { name: "title #111111", cls: "bg-title" },
  { name: "body #666666", cls: "bg-body" },
  { name: "tint #eff2e6", cls: "bg-tint" },
  { name: "mist #e3e7eb", cls: "bg-mist" },
  { name: "border #e5e5e5", cls: "bg-border" },
  { name: "muted #808080", cls: "bg-muted" },
];

export default function DesignSystem() {
  return (
    <Container className="py-12">
      <p className="font-display text-sm font-semibold text-body">Tokens from design/css</p>
      <h1 className="mt-2 font-display text-3xl font-semibold text-title">Design system</h1>
      <p className="mt-2 max-w-2xl text-base text-body">
        Colors, type, shape, and components match talentstack.in CSS. Compare side by side with the source site.
      </p>

      <section className="mt-10">
        <h2 className="font-display text-xl font-semibold text-title">Color</h2>
        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {swatches.map((s) => (
            <div key={s.name} className="rounded-card border border-border bg-surface p-4">
              <div className={`h-12 rounded-card border border-border ${s.cls}`} />
              <p className="mt-2 text-sm text-body">{s.name}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-10">
        <h2 className="font-display text-xl font-semibold text-title">Type</h2>
        <div className="mt-4 rounded-card border border-border bg-surface p-6">
          <p className="font-display text-3xl font-semibold text-title">Outfit heading 30px</p>
          <p className="mt-2 text-base text-body">Inter body 16px with 26px line height.</p>
          <p className="mt-2 text-sm text-muted">Muted small 14px for labels and help.</p>
        </div>
      </section>

      <section className="mt-10">
        <h2 className="font-display text-xl font-semibold text-title">Buttons</h2>
        <div className="mt-4 flex flex-wrap gap-4">
          <Button>Primary</Button>
          <Button variant="dark">Dark</Button>
          <Button variant="ghost">Ghost</Button>
          <Button disabled>Disabled</Button>
        </div>
        <div className="mt-4">
          <Button fullWidth>Full width submit</Button>
        </div>
      </section>

      <section className="mt-10 grid gap-6 md:grid-cols-2">
        <div>
          <h2 className="font-display text-xl font-semibold text-title">Form</h2>
          <div className="mt-4 rounded-card border border-border bg-surface p-6">
            <Label htmlFor="ds-name">Name</Label>
            <Input id="ds-name" placeholder="Riya Shah" className="mt-2" />
            <Label htmlFor="ds-notes" className="mt-4">Notes</Label>
            <Textarea id="ds-notes" placeholder="Paste resume text here" className="mt-2" rows={4} />
          </div>
        </div>
        <div>
          <h2 className="font-display text-xl font-semibold text-title">Cards and feedback</h2>
          <Card className="mt-4 p-6">
            <Badge>Partial fit</Badge>
            <p className="mt-3 font-display text-lg font-semibold text-title">Enterprise CSM</p>
            <p className="mt-1 text-sm text-body">5 years SaaS plus 25 accounts. No Salesforce evidence found.</p>
          </Card>
          <div className="mt-4 grid gap-3">
            <Alert>Saved to history. You can reopen it later.</Alert>
            <Alert tone="error">Backend is down. Check the API URL and try again.</Alert>
            <Spinner />
          </div>
        </div>
      </section>
    </Container>
  );
}
