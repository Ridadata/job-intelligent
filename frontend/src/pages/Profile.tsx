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
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">Profile</h1>
        <p className="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
          {isNew ? "Create your profile for personalized recommendations" : `Completeness: ${profile?.profile_completeness ?? 0}%`}
        </p>
      </div>

      {/* CV Upload — 2-column drag & drop zone */}
      <div className="grid gap-4 lg:grid-cols-2 items-stretch">
        {/* Left — Upload zone */}
        <div className="rounded-2xl bg-white dark:bg-[hsl(var(--surface-1))] border border-gray-100 dark:border-white/[0.06] shadow-sm p-5 space-y-3">
          <h2 className="text-base font-bold text-gray-900 dark:text-white">Upload Your CV</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
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
            className={`cursor-pointer text-center rounded-2xl border-2 border-dashed p-10 transition-all duration-200 ${isDragging ? "border-brand-500 bg-brand-50/50 dark:bg-brand-500/5" : "border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/[0.02]"}`}
          >
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 dark:bg-brand-500/10 border border-brand-100 dark:border-brand-500/20">
              <Upload className="h-5 w-5 text-brand-500" />
            </div>
            {uploadMutation.isPending ? (
              <div className="flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-brand-500" />
                <span className="text-sm font-medium text-gray-900 dark:text-white">Uploading…</span>
              </div>
            ) : (
              <>
                <p className="text-sm font-semibold text-gray-900 dark:text-white">Drag &amp; drop your resume</p>
                <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">PDF, DOCX up to 10MB</p>
                <button
                  type="button"
                  className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-white/[0.04] px-4 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 transition-colors hover:bg-gray-50 dark:hover:bg-white/[0.06]"
                >
                  Browse Files
                </button>
              </>
            )}
          </div>
        </div>

        {/* Right — Parse status card */}
        <div className="rounded-2xl bg-white dark:bg-[hsl(var(--surface-1))] border border-gray-100 dark:border-white/[0.06] shadow-sm p-5 space-y-3 flex flex-col">
          <h3 className="text-sm font-bold text-gray-900 dark:text-white">
            Last Parsed: {profile?.name ? "resume.pdf" : "No CV yet"}
          </h3>
          {[
            { icon: <CheckCircle className="h-3.5 w-3.5" />, label: "Skills extracted", value: `${profile?.skills?.length ?? 0} skills`, accent: "text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-500/10 border-brand-100 dark:border-brand-500/20" },
            { icon: <CheckCircle className="h-3.5 w-3.5" />, label: "Experience parsed", value: `${profile?.experience_years ?? 0} years`, accent: "text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-500/10 border-brand-100 dark:border-brand-500/20" },
            { icon: <Clock className="h-3.5 w-3.5" />, label: "AI matching running…", value: `${profile?.profile_completeness ?? 0}%`, accent: "text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-500/10 border-brand-100 dark:border-brand-500/20" },
          ].map((row) => (
            <div
              key={row.label}
              className={`flex items-center justify-between rounded-lg border px-3 py-2.5 text-xs ${row.accent}`}
            >
              <span className="flex items-center gap-2">
                {row.icon} {row.label}
              </span>
              <span className="font-medium">{row.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Completeness bar */}
      {!isNew && profile?.profile_completeness != null && (
        <div className="rounded-2xl bg-white dark:bg-[hsl(var(--surface-1))] border border-gray-100 dark:border-white/[0.06] shadow-sm p-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="font-medium text-gray-900 dark:text-white">Profile completeness</span>
            <span className="font-bold text-brand-500">{profile.profile_completeness}%</span>
          </div>
          <div className="h-2 rounded-full overflow-hidden bg-gray-100 dark:bg-white/[0.06]">
            <div
              className="h-full rounded-full bg-brand-400 transition-all duration-700"
              style={{ width: `${profile.profile_completeness}%` }}
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
