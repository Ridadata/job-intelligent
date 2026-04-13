import { Component, type ReactNode, type ErrorInfo } from "react";
import { Button } from "@/components/ui/Button";
import { AlertTriangle } from "lucide-react";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <AlertTriangle className="mb-4 h-10 w-10 text-[hsl(var(--destructive))]" />
          <h2 className="text-lg font-semibold">Something went wrong</h2>
          <p className="mt-1 max-w-md text-sm text-[hsl(var(--muted-foreground))]">
            {this.state.error?.message ?? "An unexpected error occurred."}
          </p>
          <Button className="mt-4" onClick={this.handleReset}>
            Try again
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
