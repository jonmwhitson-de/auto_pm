import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import ProjectPage from './pages/ProjectPage';
import NewProjectPage from './pages/NewProjectPage';
import AdminPage from './pages/AdminPage';
import IntakeInboxPage from './pages/IntakeInboxPage';
import IntakeDetailPage from './pages/IntakeDetailPage';
import { LifecyclePage } from './pages/LifecyclePage';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/projects/new" element={<NewProjectPage />} />
        <Route path="/projects/:id" element={<ProjectPage />} />
        <Route path="/projects/:projectId/lifecycle" element={<LifecyclePage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/intake" element={<IntakeInboxPage />} />
        <Route path="/intake/:id" element={<IntakeDetailPage />} />
      </Routes>
    </Layout>
  );
}

export default App;
