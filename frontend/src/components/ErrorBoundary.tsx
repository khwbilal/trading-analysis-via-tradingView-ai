import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = Readonly<{ children: ReactNode; label?: string }>;
type State = { error: Error | null };

/** Keeps one bad card from blanking the whole Desk (React render throws). */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error(this.props.label ?? "UI", error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <Box sx={{ p: 2, border: 1, borderColor: "error.main", borderRadius: 1, bgcolor: "surface.crit" }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 0.5 }}>
          {this.props.label ?? "This panel"} failed to render
        </Typography>
        <Typography variant="caption" component="pre" sx={{ whiteSpace: "pre-wrap", color: "text.secondary", mb: 1 }}>
          {this.state.error.message}
        </Typography>
        <Button size="small" variant="outlined" onClick={() => this.setState({ error: null })}>
          Try again
        </Button>
      </Box>
    );
  }
}
