"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Container } from "@/components/ui/Container";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Spinner } from "@/components/ui/Spinner";
import { friendlyError, listCandidates, type CandidateListItem } from "@/lib/api";

const PAGE_SIZE = 50;

export default function ResumesPage() {
  const [items, setItems] = useState<CandidateListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [query, setQuery] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);
  const loadTrigger = useRef(0);

  useEffect(() => {
    loadTrigger.current += 1;
    const trigger = loadTrigger.current;
    const run = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await listCandidates(PAGE_SIZE, page * PAGE_SIZE);
        if (trigger !== loadTrigger.current) return;
        setItems((prev) => (page === 0 ? data : [...prev, ...data]));
        setHasMore(data.length === PAGE_SIZE);
      } catch (err) {
        if (trigger === loadTrigger.current) setError(friendlyError(err));
      } finally {
        if (trigger === loadTrigger.current) setLoading(false);
      }
    };
    run();
  }, [page]);

  const q = query.trim().toLowerCase();
  const filtered = q
    ? items.filter((c) => {
        const skills = (c.resume_structured?.skills ?? []).map((s) => s.name.toLowerCase()).join(" ");
        return (
          c.name.toLowerCase().includes(q) ||
          c.target_role.toLowerCase().includes(q) ||
          skills.includes(q)
        );
      })
    : items;

  const formatDate = (iso: string | null) => {
    if (!iso) return "Unknown date";
    return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  };

  return (
    <Container className="py-10">
      <p className="font-display text-sm font-semibold text-body">Recruiter view</p>
      <h1 className="mt-2 font-display text-3xl font-semibold text-title">Resumes and skills</h1>
      <p className="mt-2 max-w-2xl text-base text-body">
        Every ingested resume with the skills extracted from it. Search by name, role, or skill.
      </p>

      <div className="mt-6 max-w-xl">
        <Label htmlFor="resume-search">Search resumes</Label>
        <Input
          id="resume-search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Try HubSpot or a candidate name"
          className="mt-2"
        />
      </div>

      {error ? <Alert tone="error" className="mt-6">{error}</Alert> : null}

      {loading && items.length === 0 ? (
        <div className="flex min-h-[40vh] items-center justify-center py-16">
          <Spinner label="Loading resumes" />
        </div>
      ) : filtered.length === 0 ? (
        <Card className="mt-6 p-12 text-center">
          <p className="text-body">{items.length === 0 ? "No resumes yet. Run an analysis first." : "No resumes match this search."}</p>
          {items.length === 0 ? (
            <Link href="/" className="mt-4 inline-block">
              <Button>Run your first analysis</Button>
            </Link>
          ) : null}
        </Card>
      ) : (
        <>
          <div className="mt-6 space-y-4">
            {filtered.map((c) => {
              const skills = c.resume_structured?.skills ?? [];
              const open = openId === c.id;
              return (
                <Card key={c.id} className="p-6">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h2 className="font-display text-lg font-semibold text-title">{c.name}</h2>
                      <p className="text-sm text-muted">
                        {c.target_role} | {c.chunk_count} chunks | {formatDate(c.created_at)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {c.injection_flagged ? <Badge className="bg-mist text-body border border-border">Flagged input</Badge> : null}
                      <Badge className="bg-tint text-primary">{skills.length} skills</Badge>
                      <Button variant="ghost" size="sm" onClick={() => setOpenId(open ? null : c.id)} aria-expanded={open}>
                        {open ? "Hide skills" : "View skills"}
                      </Button>
                    </div>
                  </div>
                  {open ? (
                    <div className="mt-4 border-t border-border pt-4">
                      {skills.length === 0 ? (
                        <p className="text-sm text-muted">No skills extracted for this resume.</p>
                      ) : (
                        <ul className="grid gap-2">
                          {skills.map((s, i) => (
                            <li key={i} className="text-sm">
                              <span className="font-medium text-title">{s.name}</span>
                              {s.known === false ? (
                                <span className="ml-2 rounded-pill bg-tint px-2 py-0.5 text-xs text-primary">New</span>
                              ) : null}
                              <span className="block text-muted">Source: {s.source}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                      <div className="mt-3 grid gap-2 text-sm text-body">
                        {c.resume_structured?.total_years_experience != null ? (
                          <p>Years: {c.resume_structured.total_years_experience}</p>
                        ) : null}
                        {(c.resume_structured?.roles ?? []).map((r, i) => (
                          <p key={i}>
                            {r.title}
                            {r.company ? ` at ${r.company}` : ""}
                          </p>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </Card>
              );
            })}
          </div>
          {hasMore && !q ? (
            <div className="mt-8 text-center">
              <Button variant="ghost" onClick={() => setPage((p) => p + 1)} disabled={loading}>
                {loading ? "Loading..." : "Load more"}
              </Button>
            </div>
          ) : null}
        </>
      )}
    </Container>
  );
}
