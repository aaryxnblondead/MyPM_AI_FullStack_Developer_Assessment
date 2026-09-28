"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Container } from "@/components/ui/Container";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Spinner } from "@/components/ui/Spinner";
import { Textarea } from "@/components/ui/Textarea";
import { createEvaluation, extractPdf, friendlyError } from "@/lib/api";

const STEPS = ["Extracting resume", "Indexing", "Matching requirements", "Writing outreach"];

type Fields = {
  candidateName: string;
  targetRole: string;
  resumeText: string;
  companyName: string;
  jobTitle: string;
  jobDescription: string;
};

const EMPTY: Fields = {
  candidateName: "",
  targetRole: "",
  resumeText: "",
  companyName: "",
  jobTitle: "",
  jobDescription: "",
};

function validate(f: Fields): Partial<Record<keyof Fields, string>> {
  const errors: Partial<Record<keyof Fields, string>> = {};
  const check = (key: keyof Fields, limit: number) => {
    const v = f[key].trim();
    if (!v) errors[key] = "This field is required.";
    else if (v.length > limit) errors[key] = `Keep it under ${limit} characters.`;
  };
  check("candidateName", 200);
  check("targetRole", 200);
  check("resumeText", 30000);
  check("companyName", 200);
  check("jobTitle", 200);
  check("jobDescription", 15000);
  return errors;
}

export default function Home() {
  const router = useRouter();
  const [fields, setFields] = useState<Fields>(EMPTY);
  const [errors, setErrors] = useState<Partial<Record<keyof Fields, string>>>({});
  const [running, setRunning] = useState(false);
  const [step, setStep] = useState(0);
  const [submitError, setSubmitError] = useState("");
  const [pdfBusy, setPdfBusy] = useState(false);
  const [pdfNote, setPdfNote] = useState("");
  const timers = useRef<number[]>([]);

  useEffect(() => {
    return () => {
      timers.current.forEach((t) => window.clearTimeout(t));
    };
  }, []);

  const set = (key: keyof Fields) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    setFields((f) => ({ ...f, [key]: e.target.value }));
    setErrors((prev) => ({ ...prev, [key]: undefined }));
  };

  async function onPdf(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setPdfBusy(true);
    setPdfNote("");
    try {
      const out = await extractPdf(file);
      setFields((f) => ({ ...f, resumeText: out.text }));
      setErrors((prev) => ({ ...prev, resumeText: undefined }));
      setPdfNote(`Filled from ${out.pages} page PDF. Review and edit before running.`);
    } catch (err) {
      setPdfNote(friendlyError(err));
    } finally {
      setPdfBusy(false);
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const problems = validate(fields);
    setErrors(problems);
    if (Object.values(problems).some(Boolean)) return;
    setRunning(true);
    setSubmitError("");
    setStep(0);
    STEPS.slice(1).forEach((_, i) => {
      timers.current.push(window.setTimeout(() => setStep(i + 1), 4000 * (i + 1)));
    });
    try {
      const record = await createEvaluation({
        candidate_name: fields.candidateName.trim(),
        target_role: fields.targetRole.trim(),
        resume_text: fields.resumeText.trim(),
        company_name: fields.companyName.trim(),
        job_title: fields.jobTitle.trim(),
        job_description: fields.jobDescription.trim(),
      });
      router.push(`/evaluations/${record.id}`);
    } catch (err) {
      timers.current.forEach((t) => window.clearTimeout(t));
      timers.current = [];
      setSubmitError(friendlyError(err));
      setRunning(false);
    }
  }

  return (
    <Container className="py-10">
      <p className="font-display text-sm font-semibold text-body">MyPM hiring helper</p>
      <h1 className="mt-2 font-display text-3xl font-semibold text-title">New Analysis</h1>
      <p className="mt-2 max-w-2xl text-base text-body">
        Paste a resume and a job description to see fit and draft outreach.
      </p>

      <form onSubmit={onSubmit} noValidate className="mt-8 grid gap-6 lg:grid-cols-2">
        <Card className="p-6">
          <h2 className="font-display text-lg font-semibold text-title">Candidate</h2>
          <div className="mt-4 grid gap-4">
            <div>
              <Label htmlFor="candidateName">Candidate Name</Label>
              <Input
                id="candidateName"
                value={fields.candidateName}
                onChange={set("candidateName")}
                aria-invalid={Boolean(errors.candidateName)}
                maxLength={201}
                className="mt-2"
              />
              {errors.candidateName ? <p className="mt-1 text-sm text-body">{errors.candidateName}</p> : null}
            </div>
            <div>
              <Label htmlFor="targetRole">Target Role</Label>
              <Input
                id="targetRole"
                value={fields.targetRole}
                onChange={set("targetRole")}
                aria-invalid={Boolean(errors.targetRole)}
                maxLength={201}
                className="mt-2"
              />
              {errors.targetRole ? <p className="mt-1 text-sm text-body">{errors.targetRole}</p> : null}
            </div>
            <div>
              <Label htmlFor="resumeText">Resume Text</Label>
              <div className="mt-2 flex items-center gap-3">
                <label
                  htmlFor="resumePdf"
                  className="cursor-pointer rounded-pill border border-border bg-surface px-4 py-2 font-display text-sm font-medium text-title hover:border-primary"
                >
                  Upload PDF
                </label>
                <input
                  id="resumePdf"
                  type="file"
                  accept="application/pdf,.pdf"
                  className="sr-only"
                  disabled={running || pdfBusy}
                  onChange={onPdf}
                />
                {pdfBusy ? <span className="text-sm text-muted">Reading PDF...</span> : null}
              </div>
              {pdfNote ? <p className="mt-1 text-sm text-muted">{pdfNote}</p> : null}
              <Textarea
                id="resumeText"
                value={fields.resumeText}
                onChange={set("resumeText")}
                aria-invalid={Boolean(errors.resumeText)}
                rows={12}
                className="mt-2"
              />
              {errors.resumeText ? <p className="mt-1 text-sm text-body">{errors.resumeText}</p> : null}
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="font-display text-lg font-semibold text-title">Job</h2>
          <div className="mt-4 grid gap-4">
            <div>
              <Label htmlFor="companyName">Company Name</Label>
              <Input
                id="companyName"
                value={fields.companyName}
                onChange={set("companyName")}
                aria-invalid={Boolean(errors.companyName)}
                maxLength={201}
                className="mt-2"
              />
              {errors.companyName ? <p className="mt-1 text-sm text-body">{errors.companyName}</p> : null}
            </div>
            <div>
              <Label htmlFor="jobTitle">Job Title</Label>
              <Input
                id="jobTitle"
                value={fields.jobTitle}
                onChange={set("jobTitle")}
                aria-invalid={Boolean(errors.jobTitle)}
                maxLength={201}
                className="mt-2"
              />
              {errors.jobTitle ? <p className="mt-1 text-sm text-body">{errors.jobTitle}</p> : null}
            </div>
            <div>
              <Label htmlFor="jobDescription">Job Description</Label>
              <Textarea
                id="jobDescription"
                value={fields.jobDescription}
                onChange={set("jobDescription")}
                aria-invalid={Boolean(errors.jobDescription)}
                rows={12}
                className="mt-2"
              />
              {errors.jobDescription ? <p className="mt-1 text-sm text-body">{errors.jobDescription}</p> : null}
            </div>
          </div>
        </Card>

        <div className="lg:col-span-2">
          {running ? (
            <Card className="p-6">
              <Spinner label={STEPS[step]} />
              <ol className="mt-4 grid gap-2">
                {STEPS.map((s, i) => (
                  <li key={s} className={`text-sm ${i <= step ? "text-title" : "text-muted"}`}>
                    {i < step ? "Done: " : i === step ? "Working: " : "Queued: "}{s}
                  </li>
                ))}
              </ol>
            </Card>
          ) : null}
          {submitError ? <Alert tone="error" className="mt-4">{submitError}</Alert> : null}
          <div className="mt-4 flex gap-3">
            <Button type="submit" disabled={running} fullWidth>
              {running ? "Running analysis" : "Run analysis"}
            </Button>
          </div>
        </div>
      </form>
    </Container>
  );
}
