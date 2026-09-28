"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Container } from "@/components/ui/Container";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Spinner } from "@/components/ui/Spinner";
import { Textarea } from "@/components/ui/Textarea";
import {
  getEvaluation,
  patchEvaluation,
  regenerateOutreach,
  getCandidateChunks,
  type EvaluationRecord,
  type ChunkItem,
  friendlyError,
} from "@/lib/api";

type ViewMode = "default" | "explanation" | "outreach";

export default function EvaluationPage() {
  const params = useParams();
  const id = params.id as string;

  const [record, setRecord] = useState<EvaluationRecord | null>(null);
  const [chunks, setChunks] = useState<ChunkItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [viewMode, setViewMode] = useState<ViewMode>("default");
  const [profileOpen, setProfileOpen] = useState(false);
  const [explanationDraft, setExplanationDraft] = useState("");
  const [outreachSubjectDraft, setOutreachSubjectDraft] = useState("");
  const [outreachBodyDraft, setOutreachBodyDraft] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const evalData = await getEvaluation(id);
        setRecord(evalData);
        setExplanationDraft(evalData.explanation_edited ?? evalData.explanation ?? "");
        setOutreachSubjectDraft(evalData.outreach_subject_edited ?? evalData.outreach_subject ?? "");
        setOutreachBodyDraft(evalData.outreach_body_edited ?? evalData.outreach_body ?? "");
      } catch (err) {
        setError(friendlyError(err));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  useEffect(() => {
    if (record?.candidate_id) {
      getCandidateChunks(record.candidate_id)
        .then((data) => setChunks(data.chunks ?? []))
        .catch(() => setChunks([]));
    }
  }, [record?.candidate_id]);

  if (loading) {
    return (
      <Container className="py-16 flex items-center justify-center min-h-[60vh]">
        <Spinner label="Loading analysis" />
      </Container>
    );
  }

  if (error || !record) {
    return (
      <Container className="py-16">
        <Alert tone="error">{error || "Evaluation not found"}</Alert>
        <div className="mt-4">
          <Link href="/history">
            <Button variant="ghost">Back to History</Button>
          </Link>
        </div>
      </Container>
    );
  }

  const fitCategory = record.fit_category ?? "Unknown";
  const fitScore = record.fit_score ?? 0;
  const requirements = record.per_requirement ?? [];

  const metReqs = requirements.filter((r) => r.verdict === "met");
  const partialReqs = requirements.filter((r) => r.verdict === "partial");
  const missingReqs = requirements.filter((r) => r.verdict === "no_evidence");

  const getCategoryColor = (cat: string) => {
    switch (cat) {
      case "Strong Fit":
        return "bg-primary text-surface";
      case "Moderate Fit":
        return "bg-tint text-title border border-primary";
      case "Weak Fit":
        return "bg-mist text-body border border-border";
      default:
        return "bg-muted text-surface";
    }
  };

  function findChunk(chunkId: string): ChunkItem | undefined {
    return chunks.find((c) => c.id === chunkId);
  }

  function highlightQuote(chunk: ChunkItem, quote: string) {
    const text = chunk.text;
    const idx = text.toLowerCase().indexOf(quote.toLowerCase());
    if (idx < 0) return <span className="text-body">{text}</span>;
    return (
      <>
        <span className="text-body">{text.slice(0, idx)}</span>
        <mark className="bg-tint font-medium">{text.slice(idx, idx + quote.length)}</mark>
        <span className="text-body">{text.slice(idx + quote.length)}</span>
      </>
    );
  }

  async function handleSaveExplanation() {
    setSaving(true);
    try {
      await patchEvaluation(id, { explanation_edited: explanationDraft });
      setRecord((r) => r ? { ...r, explanation_edited: explanationDraft } : null);
      setViewMode("default");
    } catch (err) {
      alert(friendlyError(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleResetExplanation() {
    setExplanationDraft(record?.explanation ?? "");
  }

  async function handleSaveOutreach() {
    setSaving(true);
    try {
      await patchEvaluation(id, {
        outreach_subject_edited: outreachSubjectDraft,
        outreach_body_edited: outreachBodyDraft,
      });
      setRecord((r) => r ? { ...r, outreach_subject_edited: outreachSubjectDraft, outreach_body_edited: outreachBodyDraft } : null);
      setViewMode("default");
    } catch (err) {
      alert(friendlyError(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleResetOutreach() {
    setOutreachSubjectDraft(record?.outreach_subject ?? "");
    setOutreachBodyDraft(record?.outreach_body ?? "");
  }

  async function handleCopyOutreach() {
    const text = `Subject: ${outreachSubjectDraft}\n\n${outreachBodyDraft}`;
    await navigator.clipboard.writeText(text);
    alert("Copied to clipboard");
  }

  async function handleRegenerateOutreach() {
    setSaving(true);
    try {
      const updated = await regenerateOutreach(id);
      setRecord(updated);
      setOutreachSubjectDraft(updated.outreach_subject ?? "");
      setOutreachBodyDraft(updated.outreach_body ?? "");
    } catch (err) {
      alert(friendlyError(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Container className="py-10">
      <div className="mb-6 flex items-center justify-between gap-4 flex-wrap">
        <div>
          <Link href="/history" className="text-sm text-muted hover:underline mb-2 inline-block">
            ← Back to History
          </Link>
          <h1 className="font-display text-3xl font-semibold text-title">Analysis Dashboard</h1>
        </div>
        <Badge className={`${getCategoryColor(fitCategory)} px-4 py-1.5 text-sm font-medium`}>
          {fitCategory} · {fitScore}/100
        </Badge>
      </div>

      {record.injection_flagged && (
        <Alert tone="error" className="mb-6">
          Instruction-like text was detected in the input and ignored. The assessment is based only on real content.
        </Alert>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-lg font-semibold text-title">Matching Qualifications</h2>
              <Badge className="bg-primary text-surface">{metReqs.length + partialReqs.length} matched</Badge>
            </div>
            {metReqs.length === 0 && partialReqs.length === 0 ? (
              <p className="mt-4 text-sm text-muted">No matching qualifications found.</p>
            ) : (
              <div className="mt-4 space-y-4">
                {metReqs.map((req) => (
                  <div key={req.requirement_id} className="border-l-4 border-primary pl-4 py-2">
                    <p className="font-medium text-title">{req.requirement_id}</p>
                    <p className="mt-1 text-sm text-body">{req.reasoning}</p>
                    {req.evidence.map((ev, i) => {
                      const chunk = findChunk(ev.chunk_id);
                      return chunk ? (
                        <div key={i} className="mt-2 text-sm">
                          <span className="text-muted">Evidence ({chunk.section_label}):</span>
                          <p className="mt-1 text-body">{highlightQuote(chunk, ev.quote)}</p>
                        </div>
                      ) : (
                        <div key={i} className="mt-2 text-sm text-muted">
                          Evidence: {ev.quote}
                        </div>
                      );
                    })}
                  </div>
                ))}
                {partialReqs.map((req) => (
                  <div key={req.requirement_id} className="border-l-4 border-tint pl-4 py-2">
                    <p className="font-medium text-title">{req.requirement_id} <span className="text-xs text-muted">(partial)</span></p>
                    <p className="mt-1 text-sm text-body">{req.reasoning}</p>
                    {req.evidence.map((ev, i) => {
                      const chunk = findChunk(ev.chunk_id);
                      return chunk ? (
                        <div key={i} className="mt-2 text-sm">
                          <span className="text-muted">Evidence ({chunk.section_label}):</span>
                          <p className="mt-1 text-body">{highlightQuote(chunk, ev.quote)}</p>
                        </div>
                      ) : (
                        <div key={i} className="mt-2 text-sm text-muted">
                          Evidence: {ev.quote}
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card className="p-6">
            <h2 className="font-display text-lg font-semibold text-title">Missing Requirements</h2>
            {missingReqs.length === 0 ? (
              <p className="mt-4 text-sm text-muted">All requirements have some evidence.</p>
            ) : (
              <div className="mt-4 space-y-3">
                {missingReqs.map((req) => (
                  <div key={req.requirement_id} className="border-l-4 border-muted pl-4 py-2">
                    <p className="font-medium text-title">{req.requirement_id}</p>
                    <p className="mt-1 text-sm text-muted">No evidence found in resume</p>
                    <p className="mt-1 text-xs text-muted">{req.reasoning}</p>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-lg font-semibold text-title">Explanation</h2>
              {viewMode === "explanation" ? (
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" onClick={handleSaveExplanation} disabled={saving}>
                    {saving ? "Saving..." : "Save"}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={handleResetExplanation}>
                    Reset
                  </Button>
                </div>
              ) : (
                <Button variant="ghost" size="sm" onClick={() => setViewMode("explanation")}>
                  Edit
                </Button>
              )}
            </div>
            {viewMode === "explanation" ? (
              <Textarea
                className="mt-4"
                value={explanationDraft}
                onChange={(e) => setExplanationDraft(e.target.value)}
                rows={4}
                disabled={saving}
              />
            ) : (
              <p className="mt-4 text-body whitespace-pre-wrap">{record.explanation_edited ?? record.explanation ?? "No explanation generated."}</p>
            )}
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-lg font-semibold text-title">Outreach Email</h2>
              {viewMode === "outreach" ? (
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" onClick={handleSaveOutreach} disabled={saving}>
                    {saving ? "Saving..." : "Save"}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={handleResetOutreach}>
                    Reset
                  </Button>
                </div>
              ) : (
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setViewMode("outreach")}>
                    Edit
                  </Button>
                  <Button variant="ghost" size="sm" onClick={handleCopyOutreach}>
                    Copy
                  </Button>
                  <Button variant="ghost" size="sm" onClick={handleRegenerateOutreach} disabled={saving}>
                    Regenerate
                  </Button>
                </div>
              )}
            </div>
            {viewMode === "outreach" ? (
              <div className="mt-4 space-y-4">
                <div>
                  <Label htmlFor="outreachSubject">Subject</Label>
                  <Input
                    id="outreachSubject"
                    value={outreachSubjectDraft}
                    onChange={(e) => setOutreachSubjectDraft(e.target.value)}
                    className="mt-2"
                    disabled={saving}
                  />
                </div>
                <div>
                  <Label htmlFor="outreachBody">Body</Label>
                  <Textarea
                    id="outreachBody"
                    value={outreachBodyDraft}
                    onChange={(e) => setOutreachBodyDraft(e.target.value)}
                    rows={10}
                    className="mt-2"
                    disabled={saving}
                  />
                </div>
              </div>
            ) : (
              <div className="mt-4">
                <p className="font-medium text-title">{record.outreach_subject_edited ?? record.outreach_subject ?? "No subject"}</p>
                <p className="mt-2 text-body whitespace-pre-wrap">{record.outreach_body_edited ?? record.outreach_body ?? "No body generated."}</p>
              </div>
            )}
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-lg font-semibold text-title">Candidate Profile</h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setProfileOpen(!profileOpen)}
                aria-expanded={profileOpen}
              >
                {profileOpen ? "Collapse" : "Expand"}
              </Button>
            </div>
            {profileOpen && record.candidate_id && (
              <div className="mt-4 space-y-4">
                <div>
                  <h3 className="font-display text-sm font-semibold text-title">Skills</h3>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {record.resume_structured?.skills?.map((s, i) => (
                      <Badge key={i} className={s.known ? "bg-primary text-surface" : "bg-tint text-title border border-primary"}>
                        {s.name}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <h3 className="font-display text-sm font-semibold text-title">Experience</h3>
                  <div className="mt-2 space-y-2">
                    {record.resume_structured?.roles?.map((r, i) => (
                      <div key={i} className="text-sm text-body">
                        <p className="font-medium text-title">{r.title}</p>
                        <p className="text-muted">{r.company}</p>
                        {r.bullets.map((b, j) => (
                          <p key={j} className="text-xs text-body">• {b}</p>
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h3 className="font-display text-sm font-semibold text-title">Education</h3>
                  <div className="mt-2 space-y-1">
                    {record.resume_structured?.education?.map((e, i) => (
                      <p key={i} className="text-sm text-body">{e.detail}</p>
                    ))}
                  </div>
                </div>
                {record.resume_structured?.total_years_experience && (
                  <div>
                    <h3 className="font-display text-sm font-semibold text-title">Total Experience</h3>
                    <p className="mt-1 text-body">{record.resume_structured.total_years_experience} years</p>
                  </div>
                )}
                {record.resume_structured?.metrics && record.resume_structured.metrics.length > 0 && (
                  <div>
                    <h3 className="font-display text-sm font-semibold text-title">Key Metrics</h3>
                    <div className="mt-2 space-y-1">
                      {record.resume_structured.metrics.map((m, i) => (
                        <p key={i} className="text-sm text-body">{m.statement}</p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      </div>
    </Container>
  );
}