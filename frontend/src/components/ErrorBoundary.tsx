import { Component, type ReactNode } from 'react'

/** Per-page crash guard: a render error shows a friendly card instead of a blank app. */
export default class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  componentDidCatch(error: unknown, info: unknown) { console.error('Page crashed:', error, info) }
  render() {
    if (!this.state.failed) return this.props.children
    return (
      <div role="alert" className="rounded-xl border-2 border-danger bg-surface p-4">
        <p className="text-lg font-semibold">This section had a problem — other tabs still work. In danger call 911.</p>
        <a href="tel:911" className="mt-2 inline-flex min-h-11 items-center font-bold text-danger underline">Call 911</a>
        <div>
          <button type="button" onClick={() => this.setState({ failed: false })}
            className="mt-2 min-h-11 rounded-lg bg-brand px-4 py-2 text-base font-medium text-brandink">Retry</button>
        </div>
      </div>
    )
  }
}
