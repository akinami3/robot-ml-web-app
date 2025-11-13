import React, { Component, ErrorInfo, ReactNode } from "react";

interface ErrorBoundaryProps {
  fallback?: ReactNode;
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("ErrorBoundary caught", error, info);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div className="p-6 bg-rose-950/40 border border-rose-800 rounded-lg text-rose-200">
            予期しないエラーが発生しました。
          </div>
        )
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
