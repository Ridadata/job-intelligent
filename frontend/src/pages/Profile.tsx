import { useState, useRef, useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { notify } from "@/lib/toast";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { candidatesService } from "@/services/candidates.service";
import { Upload, Save, Loader2, X, User, CheckCircle, Clock } from "lucide-react";
import type { CandidateProfile } from "@/types";

const CONTRACT_OPTIONS = ["CDI", "CDD", "Freelance", "Internship", "Alternance"];
const EDUCATION_OPTIONS = ["Bac", "Bac+2", "Bac+3", "Bac+5", "Doctorat", "Autre"];

export default function Profile() {
  const qc = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: profile, isLoading, isError } = useQuery({
    queryKey: ["candidate-profile"],
    queryFn: () => candidatesService.getProfile(),
    retry: false,
  });

  const [form, setForm] = useState<Partial<CandidateProfile>>({});
  const [skillInput, setSkillInput] = useState("");
  const isNew = isError || !profile;

  // Merge fetched profile into form on first load
  const initialised = useRef(false);
  if (profile && !initialised.current) {
    setForm({
      name: profile.name ?? "",
      title: profile.title ?? "",
      skills: profile.skills ?? [],
      experience_years: profile.experience_years,
      education_level: profile.education_level ?? "",
      location: profile.location ?? "",
      salary_expectation: profile.salary_expectation,
      preferred_contract_types: profile.preferred_contract_types ?? [],
    });
    initialised.current = true;
  }

  const saveMutation = useMutation({
    mutationFn: (data: Partial<CandidateProfile>) =>
      isNew ? candidatesService.createProfile(data) : candidatesService.updateProfile(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["candidate-profile"] });
      notify.success("Profile saved");
    },
    onError: (err: Error) => notify.error("Save failed", err.message),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => candidatesService.uploadCV(file),
    onSuccess: () => {
      notify.success("CV uploaded", "Parsing in progress — your profile will update shortly");
      qc.invalidateQueries({ queryKey: ["candidate-profile"] });
    },
    onError: (err: Error) => notify.error("Upload failed", err.message),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    saveMutation.mutate(form);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
  };

  const addSkill = () => {
    const trimmed = skillInput.trim();
    const skills = form.skills ?? [];
    if (trimmed && !skills.includes(trimmed)) {
      setForm({ ...form, skills: [...skills, trimmed] });
    }
    setSkillInput("");
  };

  const removeSkill = (s: string) => {
    setForm({ ...form, skills: (form.skills ?? []).filter((sk) => sk !== s) });
  };

  const toggleContract = (ct: string) => {
    const current = form.preferred_contract_types ?? [];
    setForm({
      ...form,
      preferred_contract_types: current.includes(ct)
        ? current.filter((c) => c !== ct)
        : [...current, ct],
    });
  };

  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) uploadMutation.mutate(file);
    },
    [uploadMutation]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6 max-w-4xl"
    >
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl" style={{ background: "rgba(6,182,212,0.1)" }}>
          <User className="h-5 w-5" style={{ color: "var(--accent-blue)" }} />
        </div>
        <div>
          <h1 className="text-2xl font-display font-bold" style={{ color: "var(--text-primary)" }}>Profile</h1>
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            {isNew ? "Create your profile for personalized recommendations" : `Completeness: ${profile?.profile_completeness ?? 0}%`}
          </p>
        </div>
      </div>

      {/* CV Upload — 2-column drag & drop zone */}
      <div className="grid gap-4 lg:grid-cols-2 items-stretch">
        {/* Left — Upload zone */}
        <div className="glass-card p-5 space-y-3" style={{ boxShadow: "var(--shadow-card)" }}>
          <h2 className="font-display font-bold" style={{ fontSize: "1.1rem", color: "var(--text-primary)" }}>Upload Your CV</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
            Our AI parses your resume instantly — extracting skills and matching you to live data roles automatically.
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={handleFileChange}
          />
          <div
            onClick={() => fileInputRef.current?.click()}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className="cursor-pointer text-center transition-all duration-250"
            style={{
              border: `1.5px dashed ${isDragging ? "var(--accent-cyan)" : "var(--border-glow)"}`,
              borderRadius: 24,
              padding: "2.5rem",
              background: isDragging ? "rgba(6,182,212,0.04)" : "var(--drop-zone-bg)",
            }}
          >
            <div
              className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl"
              style={{ background: "rgba(6,182,212,0.1)", border: "1px solid rgba(6,182,212,0.2)" }}
            >
              <Upload className="h-5 w-5" style={{ color: "var(--accent-cyan)" }} />
            </div>
            {uploadMutation.isPending ? (
              <div className="flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" style={{ color: "var(--accent-blue)" }} />
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Uploading…</span>
              </div>
            ) : (
              <>
                <p className="font-semibold" style={{ fontSize: "0.9rem", color: "var(--text-primary)" }}>Drag &amp; drop your resume</p>
                <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: 4 }}>PDF, DOCX up to 10MB</p>
                <button
                  type="button"
                  className="mt-3 inline-flex items-center gap-1.5 rounded-lg px-4 py-1.5 text-sm font-medium transition-all duration-200"
                  style={{
                    background: "var(--btn-subtle-bg)",
                    border: "1px solid var(--border-glow)",
                    color: "var(--text-primary)",
                  }}
                >
                  Browse Files
                </button>
              </>
            )}
          </div>
        </div>

        {/* Right — Parse status card */}
        <div className="glass-card p-5 space-y-3 flex flex-col" style={{ boxShadow: "var(--shadow-card)" }}>
          <h3 className="font-display font-bold" style={{ fontSize: "0.9rem", color: "var(--text-primary)" }}>
            Last Parsed: {profile?.name ? "resume.pdf" : "No CV yet"}
          </h3>
          {[
            { icon: <CheckCircle className="h-3.5 w-3.5" />, label: "Skills extracted", value: `${profile?.skills?.length ?? 0} skills`, bg: "rgba(16,185,129,0.07)", border: "rgba(16,185,129,0.15)", color: "var(--accent-emerald)" },
            { icon: <CheckCircle className="h-3.5 w-3.5" />, label: "Experience parsed", value: `${profile?.experience_years ?? 0} years`, bg: "rgba(16,185,129,0.07)", border: "rgba(16,185,129,0.15)", color: "var(--accent-emerald)" },
            { icon: <Clock className="h-3.5 w-3.5" />, label: "AI matching running…", value: `${profile?.profile_completeness ?? 0}%`, bg: "rgba(6,182,212,0.07)", border: "rgba(6,182,212,0.15)", color: "var(--accent-cyan)" },
          ].map((row) => (
            <div
              key={row.label}
              className="flex items-center justify-between rounded-lg px-3 py-2.5"
              style={{ background: row.bg, border: `1px solid ${row.border}`, fontSize: "0.82rem" }}
            >
              <span className="flex items-center gap-2" style={{ color: row.color }}>
                {row.icon} {row.label}
              </span>
              <span className="font-medium" style={{ color: row.color }}>{row.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Completeness bar */}
      {!isNew && profile?.profile_completeness != null && (
        <div className="glass-card p-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="font-medium" style={{ color: "var(--text-primary)" }}>Profile completeness</span>
            <span className="font-bold" style={{ color: "var(--accent-blue)" }}>{profile.profile_completeness}%</span>
          </div>
          <div className="h-2 rounded-full overflow-hidden" style={{ background: "rgba(99,130,199,0.12)" }}>
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{ width: `${profile.profile_completeness}%`, background: "linear-gradient(135deg, #06B6D4, #0EA5E9)" }}
            />
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
            <CardDescription>Update your profile to improve job matching accuracy</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6 sm:grid-cols-2">
            {/* Name */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Full name</label>
              <Input
                value={form.name ?? ""}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Jane Doe"
              />
            </div>

            {/* Title */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Job title</label>
              <Input
                value={form.title ?? ""}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="Data Engineer"
              />
            </div>

            {/* Location */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Location</label>
              <Input
                value={form.location ?? ""}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
                placeholder="Paris"
              />
            </div>

            {/* Experience */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Years of experience</label>
              <Input
                type="number"
                min={0}
                value={form.experience_years ?? ""}
                onChange={(e) => setForm({ ...form, experience_years: e.target.value ? Number(e.target.value) : null })}
                placeholder="3"
              />
            </div>

            {/* Education */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Education level</label>
              <select
                value={form.education_level ?? ""}
                onChange={(e) => setForm({ ...form, education_level: e.target.value })}
                className="flex h-10 w-full rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--surface-1))] px-4 py-2 text-sm transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/30 focus-visible:border-brand-500/50"
              >
                <option value="">Select</option>
                {EDUCATION_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>

            {/* Salary expectation */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Salary expectation (€/year)</label>
              <Input
                type="number"
                min={0}
                value={form.salary_expectation ?? ""}
                onChange={(e) => setForm({ ...form, salary_expectation: e.target.value ? Number(e.target.value) : null })}
                placeholder="45000"
              />
            </div>

            {/* Skills */}
            <div className="space-y-2 sm:col-span-2">
              <label className="text-sm font-medium">Skills</label>
              <div className="flex gap-2">
                <Input
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  placeholder="Add a skill"
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addSkill())}
                />
                <Button type="button" variant="secondary" onClick={addSkill}>Add</Button>
              </div>
              {(form.skills ?? []).length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {(form.skills ?? []).map((s) => (
                    <Badge key={s} variant="secondary" className="cursor-pointer gap-1 hover:bg-red-500/10 hover:text-red-400 transition-colors" onClick={() => removeSkill(s)}>
                      {s} <X className="h-3 w-3" />
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            {/* Preferred contract types */}
            <div className="space-y-2 sm:col-span-2">
              <label className="text-sm font-medium">Preferred contract types</label>
              <div className="flex flex-wrap gap-2">
                {CONTRACT_OPTIONS.map((ct) => {
                  const selected = (form.preferred_contract_types ?? []).includes(ct);
                  return (
                    <button
                      key={ct}
                      type="button"
                      onClick={() => toggleContract(ct)}
                      className={`rounded-xl border px-4 py-2 text-sm font-medium transition-all duration-200 ${selected ? "border-brand-500/50 bg-brand-500/15 text-brand-400" : "border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))] hover:border-brand-500/30"}`}
                    >
                      {ct}
                    </button>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="mt-6 flex justify-end">
          <Button type="submit" variant="gradient" disabled={saveMutation.isPending}>
            {saveMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
            {isNew ? "Create profile" : "Save changes"}
          </Button>
        </div>
      </form>
    </motion.div>
  );
}
