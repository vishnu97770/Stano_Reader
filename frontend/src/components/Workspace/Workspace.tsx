import type { ReactNode } from 'react';

interface WorkspaceProps {
  canvas: ReactNode;
  outputPanel: ReactNode;
}

export default function Workspace({ canvas, outputPanel }: WorkspaceProps) {
  return (
    <main className="flex-1 flex gap-4 p-4 min-h-0 overflow-hidden">
      <section className="flex-1 min-h-0">{canvas}</section>
      <aside className="hidden lg:flex w-80 flex-col">{outputPanel}</aside>
    </main>
  );
}
