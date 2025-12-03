import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import CatalogManager from './pages/CatalogManager';
import Playground from './pages/Playground';
import AgentBrowser from './pages/AgentBrowser';
import MetadataEditor from './pages/MetadataEditor';

function App() {
    return (
        <Router>
            <div className="min-h-screen bg-slate-50">
                <nav className="bg-white border-b border-slate-200">
                    <div className="px-8 py-4">
                        <div className="flex items-center justify-between">
                            <h1 className="text-2xl font-bold text-indigo-600">VE Admin Portal</h1>
                            <div className="flex gap-4">
                                <a href="/catalog" className="text-slate-600 hover:text-slate-900 font-medium">Catalog</a>
                                <a href="/browse-agents" className="text-slate-600 hover:text-slate-900 font-medium">Browse Agents</a>
                                <a href="/playground" className="text-slate-600 hover:text-slate-900 font-medium">Playground</a>
                            </div>
                        </div>
                    </div>
                </nav>

                <Routes>
                    <Route path="/" element={<Navigate to="/catalog" />} />
                    <Route path="/catalog" element={<CatalogManager />} />
                    <Route path="/browse-agents" element={<AgentBrowser />} />
                    <Route path="/metadata-editor/:veId" element={<MetadataEditor />} />
                    <Route path="/playground" element={<Playground />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;
