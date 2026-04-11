import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="flex flex-col items-center justify-center h-64 text-center">
            <div className="w-12 h-12 rounded-full bg-red-400/10 flex items-center justify-center mb-4">
              <span className="text-red-400 text-xl">!</span>
            </div>
            <p className="text-text-primary font-semibold mb-2">Une erreur est survenue</p>
            <p className="text-text-secondary text-sm max-w-md mb-4">
              {this.state.error?.message || "Erreur inconnue"}
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
              className="px-4 py-2 bg-gold/10 text-gold border border-gold/20 rounded-lg text-sm hover:bg-gold/20 transition-colors"
            >
              Recharger la page
            </button>
          </div>
        )
      );
    }

    return this.props.children;
  }
}
