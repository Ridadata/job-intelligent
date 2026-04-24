import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Brain,
  Target,
  BarChart3,
  Zap,
  ArrowRight,
  Search,
  Users,
  TrendingUp,
  Shield,
  CheckCircle,
} from "lucide-react";
import { ROUTES } from "@/config/routes";

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5, ease: "easeOut" },
  }),
};

const stats = [
  { value: "10K+", label: "Job Listings" },
  { value: "95%", label: "Match Accuracy" },
  { value: "50+", label: "Data Skills Tracked" },
  { value: "5min", label: "To First Match" },
];

const features = [
  {
    icon: Brain,
    title: "AI-Powered Matching",
    description:
      "Our NLP engine analyzes your skills, experience, and preferences to find your perfect data role.",
  },
  {
    icon: Target,
    title: "Skill Gap Analysis",
    description:
      "See exactly which skills you need to learn to qualify for your dream positions.",
  },
  {
    icon: BarChart3,
    title: "Market Intelligence",
    description:
      "Real-time insights on salary trends, in-demand skills, and hiring patterns across the data industry.",
  },
  {
    icon: Zap,
    title: "Instant Recommendations",
    description:
      "Get personalized job recommendations the moment you create your profile — no waiting required.",
  },
];

const steps = [
  {
    num: "01",
    title: "Create Your Profile",
    description: "Tell us about your skills, experience, and career goals. Upload your CV for instant parsing.",
    icon: Users,
  },
  {
    num: "02",
    title: "Get Matched",
    description: "Our AI analyzes thousands of openings and ranks them by how well they fit your profile.",
    icon: Search,
  },
  {
    num: "03",
    title: "Grow Your Career",
    description: "Follow skill gap insights, track trends, and land the data role you deserve.",
    icon: TrendingUp,
  },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-gray-100">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Link to="/" className="flex items-center">
            <img
              src="/images/logo.png"
              alt="radian"
              className="h-9 object-contain"
            />
          </Link>
          <div className="flex items-center gap-3">
            <Link
              to={ROUTES.LOGIN}
              className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              Sign in
            </Link>
            <Link
              to={ROUTES.REGISTER}
              className="rounded-xl bg-gray-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-gray-800 transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        {/* Subtle gradient background */}
        <div className="absolute inset-0 bg-gradient-to-b from-cyan-50/40 via-white to-white" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] rounded-full bg-cyan-100/30 blur-3xl" />

        <div className="relative mx-auto max-w-6xl px-6 pt-24 pb-20 lg:pt-32 lg:pb-28">
          <motion.div
            initial="hidden"
            animate="visible"
            className="mx-auto max-w-3xl text-center"
          >
            <motion.div custom={0} variants={fadeUp}>
              <span className="inline-flex items-center gap-2 rounded-full border border-cyan-200 bg-cyan-50 px-4 py-1.5 text-sm font-medium text-cyan-700 mb-8">
                <Zap className="h-3.5 w-3.5" />
                AI-Powered Career Intelligence
              </span>
            </motion.div>

            <motion.h1
              custom={1}
              variants={fadeUp}
              className="mt-6 text-5xl font-bold tracking-tight text-gray-900 sm:text-6xl lg:text-7xl leading-[1.1]"
            >
              Find your next{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-500 to-blue-500">
                data career
              </span>{" "}
              move
            </motion.h1>

            <motion.p
              custom={2}
              variants={fadeUp}
              className="mt-6 text-lg text-gray-500 max-w-2xl mx-auto leading-relaxed"
            >
              Radian connects data professionals with their ideal roles using semantic matching,
              skill analysis, and real-time market intelligence. Stop scrolling job boards —
              let AI do the work.
            </motion.p>

            <motion.div custom={3} variants={fadeUp} className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to={ROUTES.REGISTER}
                className="flex items-center gap-2 rounded-xl bg-gray-900 px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-gray-900/10 hover:bg-gray-800 transition-all hover:shadow-xl"
              >
                Start Free <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to={ROUTES.LOGIN}
                className="flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-8 py-3.5 text-base font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Sign In
              </Link>
            </motion.div>
          </motion.div>

          {/* Stats bar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.5 }}
            className="mt-20 mx-auto max-w-3xl"
          >
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 rounded-2xl border border-gray-100 bg-white shadow-sm p-6">
              {stats.map((stat) => (
                <div key={stat.label} className="text-center">
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                  <p className="mt-1 text-sm text-gray-500">{stat.label}</p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 bg-gray-50/50">
        <div className="mx-auto max-w-6xl px-6">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center mb-16"
          >
            <span className="text-sm font-semibold text-cyan-600 tracking-wide uppercase">Features</span>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Everything you need to land your data role
            </h2>
            <p className="mt-4 text-lg text-gray-500 max-w-2xl mx-auto">
              Powered by NLP, embeddings, and real-time analytics to give you an unfair advantage.
            </p>
          </motion.div>

          <div className="grid gap-6 sm:grid-cols-2">
            {features.map((feature, idx) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1, duration: 0.4 }}
                className="group rounded-2xl bg-white border border-gray-100 p-8 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-50 text-cyan-600">
                  <feature.icon className="h-6 w-6" />
                </div>
                <h3 className="mt-5 text-lg font-semibold text-gray-900">{feature.title}</h3>
                <p className="mt-2 text-sm text-gray-500 leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-24">
        <div className="mx-auto max-w-6xl px-6">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center mb-16"
          >
            <span className="text-sm font-semibold text-cyan-600 tracking-wide uppercase">How It Works</span>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Three steps to your next role
            </h2>
          </motion.div>

          <div className="grid gap-8 lg:grid-cols-3">
            {steps.map((step, idx) => (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.15, duration: 0.4 }}
                className="relative text-center"
              >
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gray-900 text-white shadow-lg">
                  <step.icon className="h-7 w-7" />
                </div>
                <span className="mt-4 inline-block text-xs font-bold text-cyan-600 tracking-widest uppercase">
                  Step {step.num}
                </span>
                <h3 className="mt-2 text-xl font-semibold text-gray-900">{step.title}</h3>
                <p className="mt-3 text-sm text-gray-500 leading-relaxed max-w-xs mx-auto">
                  {step.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Trust / Security */}
      <section className="py-20 bg-gray-50/50">
        <div className="mx-auto max-w-4xl px-6">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="rounded-2xl border border-gray-100 bg-white p-10 shadow-sm text-center"
          >
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-50 text-cyan-600 mb-6">
              <Shield className="h-7 w-7" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900">Your data, your control</h3>
            <p className="mt-3 text-gray-500 max-w-lg mx-auto">
              We never share your profile with employers without your consent.
              All data is encrypted, and you can delete your account at any time.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-6 text-sm text-gray-500">
              {["End-to-end encryption", "GDPR compliant", "No data selling", "Delete anytime"].map((item) => (
                <span key={item} className="flex items-center gap-1.5">
                  <CheckCircle className="h-4 w-4 text-cyan-500" />
                  {item}
                </span>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24">
        <div className="mx-auto max-w-6xl px-6">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="rounded-3xl bg-gray-900 px-8 py-16 text-center sm:px-16"
          >
            <h2 className="text-3xl font-bold text-white sm:text-4xl">
              Ready to accelerate your data career?
            </h2>
            <p className="mt-4 text-lg text-gray-400 max-w-xl mx-auto">
              Join thousands of data professionals who found their next role through Radian.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to={ROUTES.REGISTER}
                className="flex items-center gap-2 rounded-xl bg-white px-8 py-3.5 text-base font-semibold text-gray-900 hover:bg-gray-100 transition-colors shadow-lg"
              >
                Create Free Account <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to={ROUTES.LOGIN}
                className="flex items-center gap-2 rounded-xl border border-white/20 px-8 py-3.5 text-base font-semibold text-white hover:bg-white/10 transition-colors"
              >
                Sign In
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-12">
        <div className="mx-auto max-w-6xl px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <img src="/images/logo.png" alt="radian" className="h-7 object-contain" />
          </div>
          <p className="text-sm text-gray-400">
            &copy; {new Date().getFullYear()} Radian. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
