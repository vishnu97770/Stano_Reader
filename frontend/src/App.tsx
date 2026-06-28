import { useState } from 'react';
import WritingPage from './pages/WritingPage';
import UploadPage from './pages/UploadPage';

type Route = 'write' | 'upload';

export default function App() {
  const [route, setRoute] = useState<Route>('write');

  if (route === 'upload') {
    return <UploadPage onNavigate={setRoute} />;
  }
  return <WritingPage onNavigate={setRoute} />;
}
