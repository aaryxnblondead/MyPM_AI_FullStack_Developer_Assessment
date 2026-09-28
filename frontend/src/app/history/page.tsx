"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Container } from "@/components/ui/Container";
import { Spinner } from "@/components/ui/Spinner";
import { listEvaluations, type EvaluationListItem, friendlyError } from "@/lib/api";

const PAGE_SIZE = 20;

export default function HistoryPage() {
  const [items, setItems] = useState<EvaluationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const loadTrigger = useRef(0);

  useEffect(() => {
    loadTrigger.current += 1;
    const trigger = loadTrigger.current;
    const run = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await listEvaluations(PAGE_SIZE, page * PAGE_SIZE);
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

  const getCategoryColor = (cat: string | null) => {
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

  const formatDate = (iso: string | null) => {
    if (!iso) return "—";
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <Container className="py-10">
      <div className="mb-6 flex items-center justify-between gap-4 flex-wrap">
        <div>
          <Link href="/" className="text-sm text-muted hover:underline mb-2 inline-block">
            ← New Analysis
          </Link>
          <h1 className="font-display text-3xl font-semibold text-title">History</h1>
        </div>
      </div>

      {error && <Alert tone="error" className="mb-6">{error}</Alert>}

      {loading && items.length === 0 ? (
        <Container className="py-16 flex items-center justify-center min-h-[60vh]">
          <Spinner label="Loading history" />
        </Container>
      ) : items.length === 0 ? (
        <Card className="p-12 text-center">
          <p className="text-body">No evaluations yet.</p>
          <Link href="/" className="mt-4 inline-block">
            <Button>Run Your First Analysis</Button>
          </Link>
        </Card>
      ) : (
        <>
          <div className="space-y-4">
            {items.map((item) => (
              <Link key={item.id} href={`/evaluations/${item.id}`}>
                <Card className="p-4 hover:bg-mist/50 transition-colors cursor-pointer">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 flex-wrap">
                        <h2 className="font-display text-lg font-semibold text-title truncate">
                          {item.candidate_name}
                        </h2>
                        <Badge className={`${getCategoryColor(item.fit_category)} px-3 py-1 text-sm`}>
                          {item.fit_category ?? "—"}
                        </Badge>
                        {item.fit_score !== null && (
                          <span className="text-sm font-mono text-muted">{item.fit_score}/100</span>
                        )}
                      </div>
                      <div className="mt-1 flex flex-wrap gap-4 text-sm text-muted">
                        <span>{item.company_name}</span>
                        <span>•</span>
                        <span>{item.job_title}</span>
                        <span>•</span>
                        <span>{formatDate(item.created_at)}</span>
                      </div>
                    </div>
                    <div className="sm:ml-4 flex items-center">
                      <span className="text-sm text-muted">Open →</span>
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>

          {hasMore && (
            <div className="mt-8 text-center">
              <Button
                variant="ghost"
                onClick={() => setPage((p) => p + 1)}
                disabled={loading}
              >
                {loading ? "Loading..." : "Load More"}
              </Button>
            </div>
          )}
        </>
      )}
    </Container>
  );
}