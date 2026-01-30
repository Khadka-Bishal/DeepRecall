import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { LandingPage } from './components/LandingPage';
import { AnimatePresence, motion } from 'framer-motion';
import { ToastProvider } from './contexts/ToastContext';
import { DeepRecallLogo } from './components/DeepRecallLogo';

// Lazy load the main application
const DeepRecallApp = lazy(() => import('./DeepRecallApp'));

const LoadingScreen = () => (
  <div className="h-screen w-full flex flex-col items-center justify-center bg-[#09090b] text-zinc-500 gap-4">
    <div className="animate-pulse">
      <DeepRecallLogo />
    </div>
    <div className="text-xs font-mono">Loading application...</div>
  </div>
);

const AnimatedRoutes = () => {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route
          path="/"
          element={
            <motion.div
              key="landing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5 }}
            >
              <LandingPage onLaunch={() => navigate('/app')} />
            </motion.div>
          }
        />
        <Route
          path="/app"
          element={
            <motion.div
              key="app"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="h-screen"
            >
              <Suspense fallback={<LoadingScreen />}>
                <DeepRecallApp onHome={() => navigate('/')} />
              </Suspense>
            </motion.div>
          }
        />
      </Routes>
    </AnimatePresence>
  );
};

const App = () => {
  return (
    <BrowserRouter basename="/DeepRecall">
      <ToastProvider>
        <AnimatedRoutes />
      </ToastProvider>
    </BrowserRouter>
  );
};

export default App;
