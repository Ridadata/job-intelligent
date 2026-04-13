import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useRegister } from "@/hooks/useAuth";
import { ROUTES } from "@/config/routes";
import { Mail, Lock, User, Loader2, ArrowRight } from "lucide-react";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const register = useRegister();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    register.mutate({ email, password, full_name: fullName });
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Create your account</h2>
        <p className="mt-2 text-sm text-[hsl(var(--muted-foreground))]">
          Start discovering AI-matched job opportunities
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-2">
          <label htmlFor="fullName" className="text-sm font-medium">Full name</label>
          <div className="relative">
            <User className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[hsl(var(--muted-foreground))]" />
            <Input
              id="fullName"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Jane Doe"
              className="pl-10"
            />
          </div>
        </div>

        <div className="space-y-2">
          <label htmlFor="email" className="text-sm font-medium">Email</label>
          <div className="relative">
            <Mail className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[hsl(var(--muted-foreground))]" />
            <Input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="pl-10"
            />
          </div>
        </div>

        <div className="space-y-2">
          <label htmlFor="password" className="text-sm font-medium">Password</label>
          <div className="relative">
            <Lock className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[hsl(var(--muted-foreground))]" />
            <Input
              id="password"
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 8 characters"
              className="pl-10"
            />
          </div>
          <p className="text-xs text-[hsl(var(--muted-foreground))]">
            Must be at least 8 characters
          </p>
        </div>

        <Button type="submit" variant="gradient" className="w-full h-11" disabled={register.isPending}>
          {register.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <ArrowRight className="mr-2 h-4 w-4" />
          )}
          Create account
        </Button>
      </form>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-[hsl(var(--border))]" />
        </div>
        <div className="relative flex justify-center text-xs">
          <span className="bg-[hsl(var(--background))] px-3 text-[hsl(var(--muted-foreground))]">
            Already have an account?
          </span>
        </div>
      </div>

      <p className="text-center text-sm text-[hsl(var(--muted-foreground))]">
        <Link to={ROUTES.LOGIN} className="font-medium text-brand-500 hover:text-brand-400 transition-colors">
          Sign in
        </Link>
      </p>
    </div>
  );
}
